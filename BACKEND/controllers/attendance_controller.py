# ============================================================
# attendance_controller.py — Attendance Controller
# ============================================================

from flask import request, jsonify
from BACKEND.services.attendance_service import AttendanceService
from BACKEND.middleware.auth_middleware import require_auth


@require_auth
def mark_attendance(current_student=None):
    """
    POST /api/attendance/mark
    Body: { latitude, longitude, face_descriptor: [...128 floats...] }
    """
    data = request.get_json()
    student_id = current_student["student_id"]

    lat = data.get("latitude")
    lon = data.get("longitude")
    descriptor = data.get("face_descriptor")

    if lat is None or lon is None:
        return jsonify({"success": False, "message": "GPS coordinates are required."}), 400
    if not descriptor or not isinstance(descriptor, list) or len(descriptor) != 128:
        return jsonify({"success": False, "message": "Valid 128-d face descriptor is required."}), 400

    radius = data.get("radius")  # optional override
    is_periodic = data.get("is_periodic", False)

    result = AttendanceService.mark_attendance(student_id, float(lat), float(lon), descriptor, radius, is_periodic)
    http_status = 200 if result.get("success") else 400
    return jsonify(result), http_status


@require_auth
def get_history(current_student=None):
    """GET /api/attendance/history?limit=30"""
    limit = int(request.args.get("limit", 30))
    records = AttendanceService.get_history(current_student["student_id"], limit=limit)
    return jsonify({"success": True, "records": records, "count": len(records)}), 200


@require_auth
def get_summary(current_student=None):
    """GET /api/attendance/summary"""
    summary = AttendanceService.get_summary(current_student["student_id"])
    return jsonify({"success": True, "summary": summary}), 200


@require_auth
def get_by_date_range(current_student=None):
    """GET /api/attendance/range?start=YYYY-MM-DD&end=YYYY-MM-DD"""
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        return jsonify({"success": False, "message": "start and end dates are required."}), 400

    records = AttendanceService.get_by_date_range(current_student["student_id"], start, end)
    return jsonify({"success": True, "records": records}), 200
