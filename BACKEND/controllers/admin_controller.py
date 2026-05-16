# ============================================================
# admin_controller.py — Administrator Actions
# ============================================================

from flask import request, jsonify
from DATABASE.connection.db_connection import execute_query, execute_insert
from datetime import datetime, timezone, timedelta
import functools

ADMIN_TOKEN = "smart-attendance-admin-2026"
IST = timezone(timedelta(hours=5, minutes=30))  # Asia/Kolkata — no pytz needed

def get_current_date():
    return datetime.now(IST).date()

def require_admin(f):
    @functools.wraps(f)
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
    """POST /api/admin/login — ONLY ADMIN"""
    from BACKEND.services.auth_service import AuthService
    data = request.get_json()
    
    identifier = data.get("username") or data.get("identifier") or data.get("email", "")
    password = data.get("password", "")
    
    if not identifier or not password:
        return jsonify({"success": False, "message": "Identifier and password required"}), 400

    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    
    # Use strict role enforcement
    result = AuthService.login(identifier, password, ip=ip, user_agent=ua, required_role='admin')
    
    if not result.get("success"):
        return jsonify(result), 401
        
    return jsonify(result), 200

@require_admin
def get_all_students():
    """GET /api/admin/all-students-old"""
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
    query = """
        SELECT DISTINCT ON (student_id) 
            student_id, gps_status, face_status, final_status, check_time, latitude, longitude
        FROM auto_verify_log 
        WHERE DATE(check_time) = %s
        ORDER BY student_id, check_time DESC
    """
    latest_logs = execute_query(query, (today,), fetch="all")
    
    if latest_logs:
        for rec in latest_logs:
            if 'check_time' in rec and rec['check_time']:
                rec['check_time'] = rec['check_time'].isoformat()
    
    return jsonify({"success": True, "status": latest_logs}), 200

@require_admin
def get_today_summary():
    """GET /api/admin/today-summary"""
    today = get_current_date()
    
    total_res = execute_query("SELECT COUNT(*) as count FROM students", fetch="one")
    total_students = total_res["count"] if total_res else 0
    
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

# --- New Monitoring Functions ---

@require_admin
def get_student_monitoring():
    """GET /api/admin/monitoring"""
    query = """
        SELECT 
            s.student_id, s.name, s.department, s.year, s.class_name,
            v.gps_status, v.latitude, v.longitude, v.distance_meters, v.check_time
        FROM students s
        LEFT JOIN (
            SELECT DISTINCT ON (student_id) student_id, gps_status, latitude, longitude, distance_meters, check_time
            FROM auto_verify_log
            ORDER BY student_id, check_time DESC
        ) v ON s.student_id = v.student_id
        WHERE s.is_active = 1 AND s.role = 'student'
        ORDER BY s.name ASC
    """
    students = execute_query(query, fetch="all")
    if students:
        for s in students:
            if s.get('check_time'):
                s['check_time'] = s['check_time'].isoformat()
    return jsonify({"success": True, "students": students})

@require_admin
def mark_attendance():
    """POST /api/admin/verify-attendance"""
    data = request.get_json()
    student_id = data.get("student_id")
    status = (data.get("status") or "present").lower()
    if status not in ["present", "absent"]:
        status = "present"
    print(f"Saving attendance: {student_id}, {status}")    
    if not student_id:
        return jsonify({"success": False, "message": "Student ID required"}), 400
        
    now = datetime.now(IST)
    
    # Enforce dynamic identification of administrator committing current mark
    current_admin_name = "Admin"
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            tkn = auth_header.split(" ", 1)[1].strip()
            from BACKEND.models.session_model import SessionModel
            from BACKEND.models.student_model import StudentModel
            sess = SessionModel.get_session(tkn)
            if sess:
                stu = StudentModel.find_by_student_id(sess.get("student_id"))
                if stu and stu.get("name"):
                    current_admin_name = stu["name"]
        except Exception: pass

    query = """
        INSERT INTO attendance 
            (student_id, date, time, status, recorded_by_role, remarks, marked_by_name, location_valid)
        VALUES 
            (%s, %s, %s, %s, %s, %s, %s, TRUE)
        RETURNING id
    """
    execute_insert(query, (
        student_id, 
        now.date(), 
        now.strftime("%H:%M:%S"), 
        status, 
        "admin", 
        "Attendance manually updated",
        current_admin_name
    ))
    
    return jsonify({"success": True, "message": f"Attendance marked as {status}"})

# --- Compatibility Functions ---

def get_boundary_status_check(student_id):
    from BACKEND.models.student_model import StudentModel
    
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
    
    students = StudentModel.get_all()
    logs = execute_query("""
        SELECT DISTINCT ON (student_id) 
            student_id, gps_status, distance_meters, check_time 
        FROM auto_verify_log 
        WHERE DATE(check_time) = CURRENT_DATE
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
