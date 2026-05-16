# ============================================================
# face_controller.py — Face Recognition Controller
# ============================================================

import os
import base64
from flask import request, jsonify, current_app
from BACKEND.services.face_service import FaceService
from BACKEND.middleware.auth_middleware import require_auth


@require_auth
def enroll_face(current_student=None):
    """
    POST /api/face/enroll
    Body: { image_base64: "data:image/jpeg;base64,..." }
    Saves the face image and stores 128-d descriptor.
    """
    data = request.get_json()
    image_b64 = data.get("image_base64", "")

    if not image_b64:
        return jsonify({"success": False, "message": "Face image is required."}), 400

    # Decode and save image
    try:
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]
        image_bytes = base64.b64decode(image_b64)
    except Exception:
        return jsonify({"success": False, "message": "Invalid image data."}), 400

    upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads/faces")
    os.makedirs(upload_dir, exist_ok=True)
    image_path = os.path.join(upload_dir, f"{current_student['student_id']}_face.jpg")

    with open(image_path, "wb") as f:
        f.write(image_bytes)

    result = FaceService.enroll_face(current_student["student_id"], image_path)
    status = 200 if result["success"] else 400
    return jsonify(result), status


@require_auth
def verify_face(current_student=None):
    """
    POST /api/face/verify
    Handles BOTH face_descriptor payloads AND raw base64 image data for complete backward compatibility.
    Automatically finalizes attendance commit if matches.
    """
    data = request.get_json() or {}
    student_id = current_student["student_id"] if current_student else data.get("student_id")
    
    if not student_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401
        
    descriptor = data.get("face_descriptor")
    image_data = data.get("image") or data.get("image_base64")
    
    # 1. Extraction strategy
    if not descriptor:
        if not image_data:
            return jsonify({"success": False, "message": "Face image or descriptor required."}), 400
        
        try:
            # Strip potential data:image/... preamble
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]
            image_bytes = base64.b64decode(image_data)
            
            from AI_FACE_MODULE.face_encoding_storage import encode_face_from_base64
            extracted = encode_face_from_base64(image_bytes)
            if extracted is None:
                 return jsonify({"success": False, "message": "No recognizable face detected in camera frame."}), 400
            descriptor = extracted.tolist()
        except Exception as e:
            return jsonify({"success": False, "message": f"Image processing error: {str(e)}"}), 400

    if not descriptor or len(descriptor) != 128:
        return jsonify({"success": False, "message": "Valid 128-d biometric descriptor required."}), 400

    # 2. Guard: verify face_enrolled AND descriptor exists in DB before running comparison
    from DATABASE.connection.db_connection import execute_query as _eq
    face_row = _eq(
        "SELECT face_enrolled, face_descriptor FROM students WHERE student_id = %s",
        (student_id,), fetch="one"
    )
    face_enrolled = bool(face_row.get('face_enrolled')) if face_row else False
    face_has_descriptor = bool(face_row.get('face_descriptor')) if face_row else False

    if not face_enrolled or not face_has_descriptor:
        return jsonify({
            "success": False,
            "matched": False,
            "face_status": "not_registered",
            "message": "Face not registered for this student. Please enroll first."
        }), 200

    # 3. Run Comparison
    result = FaceService.verify_face(student_id, descriptor)
    
    # 4. Final System Finalization Save
    if result.get("matched"):
        from DATABASE.connection.db_connection import get_connection, execute_query
        import datetime
        conn = get_connection()
        cursor = conn.cursor()
        
        # Fetch existing partial data
        cursor.execute("""
            SELECT location_valid, fingerprint_verified 
            FROM attendance 
            WHERE student_id = %s AND date = CURRENT_DATE
        """, (student_id,))
        row = cursor.fetchone()
        
        is_inside = bool(row[0]) if row else False
        fingerprint_verified = bool(row[1]) if row else False

        # Fetch global fingerprint toggle
        res_fp = execute_query("SELECT setting_value FROM system_config WHERE setting_key = 'fingerprint_verification_enabled'", fetch="one")
        fp_on = (res_fp["setting_value"] == "ON") if res_fp else False
        
        # RULE: 
        # If fingerprint OFF: face_match (True here) + inside_boundary = PRESENT
        # If fingerprint ON: face_match (True here) + inside_boundary + fingerprint_verified = PRESENT
        if fp_on:
            success_mark = (is_inside and fingerprint_verified)
        else:
            success_mark = is_inside
            
        final_status = "present" if success_mark else "absent"
        
        # Commit final verification override
        cursor.execute("""
            UPDATE attendance 
            SET status = %s, 
                face_match_status = 'success',
                remarks = %s,
                marked_at = CURRENT_TIMESTAMP
            WHERE student_id = %s AND date = CURRENT_DATE
        """, (
            final_status, 
            "Auto Verified" if final_status == "present" else "Verification failed (Biometric or Boundary issue).",
            student_id
        ))
        conn.commit()
        cursor.close()
        conn.close()
        
        result["success"] = True 
        result["status"] = final_status
    else:
         result["success"] = False
         result["message"] = result.get("message", "Face match failed.")
         
    return jsonify(result), 200


def identify_student():
    """
    POST /api/face/identify  (no auth required — used to auto-identify)
    Body: { face_descriptor: [...128 floats...] }
    """
    data = request.get_json()
    descriptor = data.get("face_descriptor")

    if not descriptor or len(descriptor) != 128:
        return jsonify({"success": False, "message": "Valid 128-d descriptor required."}), 400

    result = FaceService.identify_student(descriptor)
    return jsonify(result), 200
