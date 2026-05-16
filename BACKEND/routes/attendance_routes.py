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
    face_verified_client = data.get('face_verified', False)  # from frontend

    # ── Fetch boundary coordinates (DB first, config fallback) ───────────────
    from DATABASE.connection.db_connection import execute_query
    res_loc = execute_query(
        "SELECT latitude, longitude FROM boundary_locations ORDER BY updated_time DESC LIMIT 1",
        fetch="one"
    )
    if res_loc:
        COLLEGE_LAT = float(res_loc["latitude"])
        COLLEGE_LNG = float(res_loc["longitude"])
    else:
        from CONFIG.college_location_config import COLLEGE_LAT, COLLEGE_LNG

    from CONFIG.college_location_config import RADIUS
    from BACKEND.services.geofence_service import calculate_distance
    distance = calculate_distance(lat, lng, COLLEGE_LAT, COLLEGE_LNG)

    ALLOWED_RADIUS = RADIUS + 15  # 15m tolerance for GPS drift
    is_inside = distance <= ALLOWED_RADIUS

    print(f"[GPS] Student:{student_id} {lat},{lng} | College:{COLLEGE_LAT},{COLLEGE_LNG} | "
          f"Dist:{distance:.1f}m | {'INSIDE' if is_inside else 'OUTSIDE'}")

    # ── Validate face_enrolled in DB — never trust frontend alone ─────────────
    face_row = execute_query(
        "SELECT face_enrolled FROM students WHERE student_id = %s",
        (student_id,), fetch="one"
    )
    face_enrolled = bool(face_row.get('face_enrolled')) if face_row else False

    # Frontend may send face_verified=True but face was never enrolled
    face_verified = face_verified_client and face_enrolled

    # ── Delegate to canonical throttled store_auto_check ─────────────────────
    from BACKEND.models.attendance_model import store_auto_check
    result = store_auto_check(student_id, lat, lng, distance, status=None, face_verified=face_verified)

    return jsonify({
        "success": result.get("success", True),
        "status": result.get("status", "absent"),
        "distance": round(distance, 1),
        "face_verified": face_verified,
        "face_enrolled": face_enrolled,
        "face_status": result.get("face_status", "not_registered" if not face_enrolled else "failed"),
        "is_inside": is_inside,
        "inserted": result.get("inserted", False),
        "blocked": result.get("blocked"),
        "next_check_mins": result.get("next_check_mins"),
        "grace_timer_passed": result.get("grace_timer_passed", False)
    })

