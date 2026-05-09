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


@attendance_bp.route('/auto-verify/check', methods=['POST'])
def auto_verify_check():
    from flask import request, jsonify
    data = request.get_json()
    student_id = data.get('student_id')
    lat = data.get('latitude')
    lng = data.get('longitude')
    from CONFIG.college_location_config import COLLEGE_LAT, COLLEGE_LNG, RADIUS
    from BACKEND.services.geofence_service import calculate_distance
    distance = calculate_distance(lat, lng, COLLEGE_LAT, COLLEGE_LNG)
    status = 'present' if distance <= RADIUS else 'absent'
    from BACKEND.models.attendance_model import store_auto_check
    store_auto_check(student_id, lat, lng, distance, status)
    return jsonify({"success": True, "status": status, "distance": round(distance,1)})

