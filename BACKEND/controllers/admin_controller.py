from flask import request, jsonify
from functools import wraps
from DATABASE.connection.db_connection import execute_query
from UTILS.time_utils import get_current_date

ADMIN_TOKEN = "admin-secret-token-12345"

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Admin authentication required."}), 401
        
        token = auth_header.split(" ", 1)[1].strip()
        if token == ADMIN_TOKEN:
            return f(*args, **kwargs)
            
        from BACKEND.models.session_model import SessionModel
        from BACKEND.models.student_model import StudentModel
        session = SessionModel.get_session(token)
        if session:
            student = StudentModel.find_by_student_id(session["student_id"])
            if student:
                role = student.get("role") or ("creator" if student["email"] == "gowsicklitheswaran@gmail.com" else "student")
                if role in ["admin", "creator"]:
                    return f(*args, **kwargs)
        
        return jsonify({"success": False, "message": "Invalid admin token or unauthorized access."}), 401
    return decorated_function

def admin_login():
    """POST /api/admin/login"""
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if username == "admin" and password == "admin123":
        return jsonify({"success": True, "token": ADMIN_TOKEN}), 200
    
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@require_admin
def get_all_students():
    """GET /api/admin/all-students"""
    dept = request.args.get("department")
    cls = request.args.get("class")
    
    query = "SELECT student_id, name, email, phone, department, class_name FROM students WHERE 1=1"
    params = []
    
    if dept:
        query += " AND department = %s"
        params.append(dept)
    if cls:
        query += " AND class_name = %s"
        params.append(cls)
        
    students = execute_query(query, tuple(params), fetch="all")
    return jsonify({"success": True, "students": students}), 200

@require_admin
def get_boundary_status():
    """GET /api/admin/boundary-status"""
    today = get_current_date()
    # Get latest auto_verify_log for each student today
    query = """
        SELECT DISTINCT ON (student_id) 
            student_id, gps_status, face_status, final_status, check_time, latitude, longitude
        FROM auto_verify_log 
        WHERE DATE(check_time) = %s
        ORDER BY student_id, check_time DESC
    """
    latest_logs = execute_query(query, (today,), fetch="all")
    
    # Format datetime objects to string
    if latest_logs:
        for rec in latest_logs:
            if 'check_time' in rec and rec['check_time']:
                rec['check_time'] = rec['check_time'].isoformat()
    
    return jsonify({"success": True, "status": latest_logs}), 200

@require_admin
def get_today_summary():
    """GET /api/admin/today-summary"""
    today = get_current_date()
    
    # Total students count
    total_res = execute_query("SELECT COUNT(*) as count FROM students", fetch="one")
    total_students = total_res["count"] if total_res else 0
    
    # Today's present count (based on attendance table or auto_verify_log, we use attendance table for consistency)
    present_query = """
        SELECT COUNT(DISTINCT student_id) as present_count 
        FROM attendance 
        WHERE date = %s AND status IN ('present', 'late')
    """
    present_res = execute_query(present_query, (today,), fetch="one")
    present_count = present_res["present_count"] if present_res else 0
    
    return jsonify({
        "success": True, 
        "total_students": total_students,
        "present_count": present_count
    }), 200


def get_boundary_status_check(student_id):
    from BACKEND.models.student_model import StudentModel
    from BACKEND.services.geofence_service import calculate_distance
    from CONFIG.college_location_config import COLLEGE_LAT, COLLEGE_LNG, RADIUS
    from DATABASE.connection.db_connection import execute_query
    
    student = StudentModel.find_by_student_id(student_id)
    if not student:
        student = StudentModel.find_by_email(student_id)
        
    if not student:
        return {"success": False, "message": "Student not found"}
        
    log = execute_query("""
        SELECT latitude, longitude, distance_meters, gps_status, check_time 
        FROM auto_verify_log 
        WHERE student_id = %s 
        ORDER BY check_time DESC LIMIT 1
    """, (student["student_id"],), fetch="one")
    
    if log:
        lat = log.get('latitude')
        lng = log.get('longitude')
        distance = log.get('distance_meters')
        status = log.get('gps_status', 'outside')
        check_time = log.get('check_time').strftime("%Y-%m-%d %H:%M:%S") if log.get('check_time') else "—"
    else:
        lat, lng, distance, status, check_time = None, None, None, "unknown", "—"
        
    return {
        "success": True,
        "student": {
            "student_id": student["student_id"],
            "name": student["name"],
            "department": student["department"],
            "class_name": student["class_name"],
            "email": student["email"]
        },
        "status": status,
        "distance": round(distance, 1) if distance is not None else None,
        "last_check": check_time,
        "latitude": lat,
        "longitude": lng
    }


def get_all_students_list():
    from BACKEND.models.student_model import StudentModel
    from DATABASE.connection.db_connection import execute_query
    
    students = StudentModel.get_all()
    logs = execute_query("""
        SELECT DISTINCT ON (student_id) 
            student_id, gps_status, distance_meters, check_time 
        FROM auto_verify_log 
        ORDER BY student_id, check_time DESC
    """)
    
    log_map = {l["student_id"]: l for l in logs} if logs else {}
    
    res = []
    for s in students:
        log = log_map.get(s["student_id"], {})
        check_time = log.get("check_time")
        res.append({
            "student_id": s["student_id"],
            "name": s["name"],
            "department": s["department"],
            "class_name": s["class_name"],
            "email": s["email"],
            "status": log.get("gps_status", "unknown"),
            "distance": round(log.get("distance_meters"), 1) if log.get("distance_meters") is not None else "—",
            "last_check": check_time.strftime("%Y-%m-%d %H:%M:%S") if check_time else "—"
        })
    return {"success": True, "students": res}

