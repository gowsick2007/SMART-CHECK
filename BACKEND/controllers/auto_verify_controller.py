from flask import request, jsonify
from DATABASE.connection.db_connection import execute_insert, execute_query
from BACKEND.middleware.auth_middleware import require_auth
from datetime import datetime

@require_auth
def auto_verify_check(current_student=None):
    """POST /api/auto-verify/check"""
    data = request.get_json()
    student_id = current_student["student_id"]
    
    gps_status = data.get("gps_status", "outside")
    face_status = data.get("face_status", "failed")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    
    final_status = "present" if (gps_status == "inside" and face_status == "verified") else "absent"
    
    query = """
        INSERT INTO auto_verify_log 
        (student_id, check_time, gps_status, face_status, final_status, latitude, longitude)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    params = (
        student_id, datetime.now(), gps_status, face_status, final_status,
        latitude, longitude
    )
    log_id = execute_insert(query, params)
    
    return jsonify({
        "success": True, 
        "message": f"Auto-verify logged as {final_status}", 
        "final_status": final_status,
        "log_id": log_id
    }), 200

@require_auth
def get_auto_verify_history(current_student=None):
    """GET /api/auto-verify/history"""
    student_id = current_student["student_id"]
    query = "SELECT * FROM auto_verify_log WHERE student_id = %s ORDER BY check_time DESC LIMIT 50"
    records = execute_query(query, (student_id,), fetch="all")
    
    # Format datetime objects to string
    for rec in records:
        if 'check_time' in rec and rec['check_time']:
            rec['check_time'] = rec['check_time'].isoformat()
            
    return jsonify({"success": True, "records": records}), 200
