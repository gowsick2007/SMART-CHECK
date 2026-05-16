from flask import request, jsonify
from DATABASE.connection.db_connection import execute_insert, execute_query
from BACKEND.middleware.auth_middleware import require_auth
from datetime import datetime

@require_auth
def auto_verify_check(current_student=None):
    """
    POST /api/auto-verify/check
    Thin wrapper — delegates to store_auto_check in attendance_model
    which has the canonical 30-min throttle + face_enrolled check.
    """
    data = request.get_json()
    student_id = current_student["student_id"]

    gps_status = data.get("gps_status", "outside")
    face_status = data.get("face_status", "failed")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    distance = data.get("distance_meters", 0)

    # Resolve face_verified bool from face_status string
    face_verified = (face_status == "verified")

    # Delegate to the canonical throttled logic
    from BACKEND.models.attendance_model import store_auto_check
    result = store_auto_check(
        student_id, latitude, longitude, distance,
        status=None,          # computed inside store_auto_check
        face_verified=face_verified
    )

    return jsonify({
        "success": result.get("success", True),
        "final_status": result.get("status", "absent"),
        "inserted": result.get("inserted", False),
        "blocked": result.get("blocked"),
        "next_check_mins": result.get("next_check_mins"),
        "face_enrolled": result.get("face_enrolled"),
        "face_status": result.get("face_status"),
        "is_inside": result.get("is_inside", gps_status == "inside"),
    }), 200

@require_auth
def get_auto_verify_history(current_student=None):
    """GET /api/auto-verify/history"""
    student_id = current_student["student_id"]
    query = """
        SELECT id, student_id, check_time, gps_status, face_status,
               final_status, latitude, longitude, distance_meters
        FROM auto_verify_log
        WHERE student_id = %s
        ORDER BY check_time DESC
        LIMIT 100
    """
    records = execute_query(query, (student_id,), fetch="all") or []

    for rec in records:
        if rec.get('check_time'):
            rec['check_time'] = rec['check_time'].isoformat()

    return jsonify({"success": True, "records": records}), 200
