# ============================================================
# face_routes.py — Face Recognition API Routes
# ============================================================

from flask import Blueprint
from BACKEND.controllers.face_controller import enroll_face, verify_face, identify_student

face_bp = Blueprint("face", __name__, url_prefix="/api/face")

face_bp.route("/enroll", methods=["POST"])(enroll_face)
face_bp.route("/verify", methods=["POST"])(verify_face)
face_bp.route("/identify", methods=["POST"])(identify_student)
