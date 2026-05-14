# ============================================================
# attendance_routes.py — Attendance API Routes
# ============================================================

from flask import Blueprint
from BACKEND.controllers.attendance_controller import (
    mark_attendance, get_history, get_summary, get_by_date_range
)

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")

attendance_bp.route("/mark", methods=["POST"])(mark_attendance)
attendance_bp.route("/history", methods=["GET"])(get_history)
attendance_bp.route("/summary", methods=["GET"])(get_summary)
attendance_bp.route("/range", methods=["GET"])(get_by_date_range)

@attendance_bp.route("/weekly-summary", methods=["GET"])
def weekly_summary():
    from flask import request, jsonify
    from BACKEND.models.attendance_model import AttendanceModel
    student_id = request.args.get("student_id")
    if not student_id:
        return jsonify({"success": False, "message": "student_id required"}), 400
    summary = AttendanceModel.get_weekly_summary(student_id)
    return jsonify({"success": True, "percentage": summary["percentage"], "summary": summary}), 200

@attendance_bp.route('/auto-mark', methods=['POST'])
@attendance_bp.route('/auto-verify/check', methods=['POST'])
def auto_verify_check():
    from flask import request, jsonify
    data = request.get_json()
    student_id = data.get('student_id')
    lat = data.get('latitude')
    lng = data.get('longitude')
    face_verified = data.get('face_verified', False)
    from DATABASE.connection.db_connection import execute_query
    res_loc = execute_query("SELECT latitude, longitude FROM boundary_locations ORDER BY updated_time DESC LIMIT 1", fetch="one")
    if res_loc:
        COLLEGE_LAT = float(res_loc["latitude"])
        COLLEGE_LNG = float(res_loc["longitude"])
    else:
        from CONFIG.college_location_config import COLLEGE_LAT, COLLEGE_LNG
    
    from CONFIG.college_location_config import RADIUS
    from BACKEND.services.geofence_service import calculate_distance
    distance = calculate_distance(lat, lng, COLLEGE_LAT, COLLEGE_LNG)

    # Check global configs
    from DATABASE.connection.db_connection import execute_query
    res_face = execute_query("SELECT setting_value FROM system_config WHERE setting_key = 'face_verification_enabled'", fetch="one")
    face_required = (res_face["setting_value"] == "ON") if res_face else True
    
    res_fp = execute_query("SELECT setting_value FROM system_config WHERE setting_key = 'fingerprint_verification_enabled'", fetch="one")
    fp_required = (res_fp["setting_value"] == "ON") if res_fp else False

    # Combined status: Only 'present' if GPS is inside AND required biometrics are verified
    is_inside = distance <= RADIUS
    
    # Check if face is needed and verified
    face_ok = True
    if face_required:
        face_ok = face_verified
        
    # Check if fingerprint is needed (if we ever implement it for auto)
    fp_ok = True
    if fp_required:
        # Assuming for now auto-verify doesn't handle real-time fingerprint 
        # unless it was verified earlier in the session.
        # For now, let's just focus on face as requested.
        pass

    # STRICT RULE: Auto-verify ONLY marks present if face is verified AND inside boundary
    status = 'present' if (is_inside and face_verified) else 'absent'

    from BACKEND.models.attendance_model import store_auto_check
    result = store_auto_check(student_id, lat, lng, distance, status, face_verified=face_verified)
    
    return jsonify({
        "success": result.get("success", True), 
        "status": result.get("status", status), 
        "distance": round(distance, 1), 
        "face_verified": face_verified,
        "is_inside": result.get("is_inside", is_inside),
        "grace_time_remaining": result.get("grace_time_remaining", 0),
        "grace_timer_passed": result.get("grace_timer_passed", False)
    })

