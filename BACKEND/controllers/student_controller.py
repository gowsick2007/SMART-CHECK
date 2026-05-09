# ============================================================
# student_controller.py — Student Profile Controller
# ============================================================

from flask import request, jsonify
from BACKEND.models.student_model import StudentModel
from BACKEND.models.face_model import FaceModel
from BACKEND.models.attendance_model import AttendanceModel
from UTILS.time_utils import get_current_date
from BACKEND.middleware.auth_middleware import require_auth


@require_auth
def get_profile(current_student=None):
    """GET /api/student/profile"""
    student = dict(current_student)
    student.pop("password_hash", None)  # Never expose password hash
    has_face = FaceModel.has_face_data(student["student_id"])
    student["face_enrolled"] = has_face
    return jsonify({"success": True, "student": student}), 200


@require_auth
def get_all_students(current_student=None):
    """GET /api/student/all?department=X&class_name=Y&with_attendance=true"""
    dept = request.args.get("department")
    cls = request.args.get("class_name")
    with_att = request.args.get("with_attendance", "false").lower() == "true"
    
    students = StudentModel.get_all(department=dept, class_name=cls)
    today = get_current_date()
    
    # Optional: fetch today's attendance for everyone
    all_att = []
    if with_att:
        all_att = AttendanceModel.get_all_by_date(today) or []
    
    att_map = {}
    for a in all_att:
        sid = a["student_id"]
        if sid not in att_map or a["time"] > att_map[sid]["time"]:
            att_map[sid] = a  # Keep latest record
    
    for s in students:
        s.pop("password_hash", None)
        if with_att:
            s["live_attendance"] = att_map.get(s["student_id"], None)
            
    return jsonify({"success": True, "students": students, "count": len(students)}), 200


@require_auth
def get_student_by_id(student_id=None, current_student=None):
    """GET /api/student/<student_id>"""
    student = StudentModel.find_by_student_id(student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found."}), 404
    student = dict(student)
    student.pop("password_hash", None)
    return jsonify({"success": True, "student": student}), 200
