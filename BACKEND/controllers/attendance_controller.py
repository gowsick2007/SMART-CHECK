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
    try:
        limit = int(request.args.get("limit", 30))
        records = AttendanceService.get_history(current_student["student_id"], limit=limit)
        
        from DATABASE.connection.db_connection import execute_query
        fallback_admin_name = "System Admin"
        try:
            fallback_row = execute_query("SELECT name FROM students WHERE role = 'creator' LIMIT 1", fetch="one")
            if fallback_row: fallback_admin_name = fallback_row["name"]
        except Exception:
            pass
            
        from BACKEND.services.geofence_service import calculate_distance
        COLLEGE_LAT, COLLEGE_LNG = 0.0, 0.0
        try:
            res_loc = execute_query("SELECT latitude, longitude FROM boundary_locations ORDER BY updated_time DESC LIMIT 1", fetch="one")
            if res_loc:
                COLLEGE_LAT = float(res_loc["latitude"])
                COLLEGE_LNG = float(res_loc["longitude"])
            else:
                from CONFIG.college_location_config import COLLEGE_LAT as clat, COLLEGE_LNG as clng
                COLLEGE_LAT, COLLEGE_LNG = clat, clng
        except Exception:
            try:
                from CONFIG.college_location_config import COLLEGE_LAT as clat, COLLEGE_LNG as clng
                COLLEGE_LAT, COLLEGE_LNG = clat, clng
            except ImportError:
                pass

        formatted_records = []
        for rec in records:
            lat = float(rec.get("latitude")) if rec.get("latitude") else None
            lon = float(rec.get("longitude")) if rec.get("longitude") else None
            
            distance = None
            if lat is not None and lon is not None:
                distance = round(calculate_distance(lat, lon, COLLEGE_LAT, COLLEGE_LNG), 1)
            
            role = rec.get("recorded_by_role", "system")
            is_inside = bool(rec.get("location_valid"))
            boundary_str = "inside" if is_inside else "outside"
            
            if role == 'student':
                display_type = "Face Verified"
                source_type = "student"
                dist_str = f"{distance}m" if distance is not None else "—"
                clean_distance = f"{dist_str} {boundary_str}"
                face_display = "success"
                admin_name = None
            elif role != 'system':
                admin_name = rec.get("marked_by_name")
                if not admin_name or str(admin_name).strip().lower() in ["admin", ""]:
                    admin_name = fallback_admin_name
                display_type = f"Set by Admin ({admin_name})"
                source_type = "manual"
                clean_distance = "Attendance manually updated"
                face_display = "not_attempted" # Frontend renders this as "—"
            else:
                display_type = "Auto Verified"
                source_type = "auto"
                dist_str = f"{distance}m" if distance is not None else "—"
                clean_distance = f"{dist_str} {boundary_str}"
                face_display = rec.get("face_match_status", "not_attempted")
                admin_name = None

            formatted_records.append({
                "date": str(rec.get("date")) if rec.get("date") else "",
                "time": str(rec.get("time")) if rec.get("time") else "",
                "type": display_type,
                "source": source_type,
                "boundary": boundary_str,
                "distance": clean_distance,
                "status": (rec.get("status") or "absent").lower(),
                "recorded_by_role": role,
                "location_valid": is_inside,
                "face_match_status": face_display,
                "remarks": clean_distance,
                "marked_by_name": admin_name
            })

        return jsonify({"success": True, "records": formatted_records, "count": len(formatted_records)}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Failed to fetch history: {str(e)}"}), 500


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
