# ============================================================
# face_controller.py — Face Recognition Controller
# ============================================================

import os
import base64
import traceback
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
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Invalid image data: {e}"}), 400

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
        
    # 1. Guard: verify face_enrolled AND descriptor exists in DB before doing any heavy processing
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
            "message": "Face not registered. Please enroll your face first."
        }), 400

    descriptor = data.get("face_descriptor")
    image_data = data.get("image") or data.get("image_base64")
    
    # 2. Extraction strategy
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
                 return jsonify({"success": False, "message": "Face not detected clearly. Please keep your full face inside the frame, look straight, avoid low light, remove blur, and try again."}), 400
            descriptor = extracted.tolist()
        except Exception as e:
            traceback.print_exc()
            return jsonify({"success": False, "message": f"Image processing error: {str(e)}"}), 400

    if not descriptor or len(descriptor) != 128:
        return jsonify({"success": False, "message": "Valid 128-d biometric descriptor required."}), 400

    # 3. Run Comparison
    result = FaceService.verify_face(student_id, descriptor)

    if result.get("matched"):
        lat = data.get("latitude")
        lng = data.get("longitude")
        
        if lat is not None and lng is not None:
            # Check boundary
            from BACKEND.services.geofence_service import calculate_distance
            from DATABASE.connection.db_connection import execute_query as _eq2
            res_loc = _eq2(
                "SELECT latitude, longitude FROM boundary_locations ORDER BY updated_time DESC LIMIT 1",
                fetch="one"
            )
            if res_loc:
                COLLEGE_LAT = float(res_loc["latitude"])
                COLLEGE_LNG = float(res_loc["longitude"])
            else:
                from CONFIG.college_location_config import COLLEGE_LAT, COLLEGE_LNG
            from CONFIG.college_location_config import RADIUS
            
            distance = calculate_distance(lat, lng, COLLEGE_LAT, COLLEGE_LNG)
            ALLOWED_RADIUS = RADIUS + 15
            is_inside = distance <= ALLOWED_RADIUS
            
            if is_inside:
                # Mark attendance present manually by student
                from DATABASE.connection.db_connection import execute_insert
                from datetime import datetime, timezone, timedelta
                
                IST = timezone(timedelta(hours=5, minutes=30))
                now = datetime.now(IST)
                
                query = """
                    INSERT INTO attendance
                        (student_id, date, time, status, latitude, longitude,
                         location_valid, face_match_status, remarks, recorded_by_role,
                         marked_at)
                    VALUES (%s, %s, %s, 'present', %s, %s, %s, 'success', %s, 'student', CURRENT_TIMESTAMP)
                    ON CONFLICT (student_id, date, recorded_by_role) DO NOTHING
                """
                remarks = f"{distance:.1f}m INSIDE | Face: MATCHED"
                execute_insert(query, (
                    student_id, now.date(), now.strftime("%H:%M:%S"),
                    lat, lng, True, remarks
                ))
                
                # Also log it in the background auto-verify system (throttled)
                from BACKEND.models.attendance_model import store_auto_check
                store_auto_check(student_id, lat, lng, distance, status=None, face_verified=True)
                
                result["success"] = True
                result["message"] = "Face matched and you are inside campus. Attendance marked PRESENT."
                result["is_inside"] = True
            else:
                result["success"] = False
                result["message"] = "Face matched, but you are outside campus."
                result["is_inside"] = False
        else:
            # Fallback if GPS not provided
            result["success"] = True
            result["message"] = "Face matched successfully (location unknown)."
    else:
        result["success"] = False
        result["message"] = "Face not matched. Try again."

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
