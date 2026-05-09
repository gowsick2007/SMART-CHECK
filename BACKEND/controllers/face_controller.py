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
    Body: { face_descriptor: [...128 floats...] }
    Verifies live face descriptor against stored.
    """
    data = request.get_json()
    descriptor = data.get("face_descriptor")

    if not descriptor or len(descriptor) != 128:
        return jsonify({"success": False, "message": "Valid 128-d descriptor required."}), 400

    result = FaceService.verify_face(current_student["student_id"], descriptor)
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
