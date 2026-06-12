# ============================================================
# app.py — Main Flask Application Entry Point
# ============================================================

import os
import sys

# ── Fix: Add PROJECT ROOT (parent of BACKEND/) to sys.path ──
# __file__ = .../SMART-ATTENDANCE/BACKEND/app.py
# dirname(__file__)        = .../SMART-ATTENDANCE/BACKEND      ← wrong (was here before)
# dirname(dirname(__file__)) = .../SMART-ATTENDANCE            ← correct project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

from BACKEND.config.server_config import DevelopmentConfig
from BACKEND.routes.auth_routes import auth_bp
from BACKEND.routes.student_routes import student_bp, location_bp
from BACKEND.routes.attendance_routes import attendance_bp
from BACKEND.routes.face_routes import face_bp
from BACKEND.routes.admin_routes import admin_bp
from BACKEND.routes.auto_verify_routes import auto_verify_bp
from BACKEND.routes.role_routes import admin_bp as admin_extra_bp, creator_bp as creator_extra_bp
from BACKEND.routes.smart_analytics_routes import smart_analytics_bp
from BACKEND.middleware.error_handler import register_error_handlers

# Absolute path to FRONTEND pages folder (works regardless of CWD)
FRONTEND_PAGES = os.path.join(PROJECT_ROOT, "FRONTEND", "pages")
FRONTEND_ROOT  = os.path.join(PROJECT_ROOT, "FRONTEND")


def create_app(config=None):
    """Application factory pattern."""
    app = Flask(
        __name__,
        static_folder=FRONTEND_ROOT,
        static_url_path="/static",
    )

    # Load configuration
    app.config.from_object(config or DevelopmentConfig)

    # Ensure upload folder exists
    upload_dir = os.path.join(PROJECT_ROOT, "uploads", "faces")
    os.makedirs(upload_dir, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_dir

    # Initialize System Config Table
    try:
        from DATABASE.connection.db_connection import execute_insert, execute_query
        execute_insert("""
            CREATE TABLE IF NOT EXISTS system_config (
                setting_key VARCHAR(100) PRIMARY KEY,
                setting_value VARCHAR(100) NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Insert defaults if missing
        configs = [
            ('face_verification_enabled', 'ON'),
            ('fingerprint_verification_enabled', 'OFF')
        ]
        for key, val in configs:
            existing = execute_query("SELECT 1 FROM system_config WHERE setting_key = %s", (key,), fetch="one")
            if not existing:
                execute_insert("INSERT INTO system_config (setting_key, setting_value) VALUES (%s, %s)", (key, val))
    except Exception as e:
        print(f"Failed to initialize system_config: {e}")

    # CORS — allow all origins including 'null' (sent by browsers when HTML is opened from file://)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register all Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(student_bp)
    app.register_blueprint(location_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(face_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auto_verify_bp)
    app.register_blueprint(admin_extra_bp)
    app.register_blueprint(creator_extra_bp)
    app.register_blueprint(smart_analytics_bp)

    # Register global error handlers
    register_error_handlers(app)

    # ── Explicitly fix Creator/Admin Login routes to bypass any Blueprint issues ──────
    @app.route("/api/auth/creator/login", methods=["POST"])
    @app.route("/creator/login", methods=["POST"])
    def creator_login_fixed_path():
        from BACKEND.controllers.auth_controller import creator_login
        return creator_login()

    @app.route("/api/auth/admin/login", methods=["POST"])
    @app.route("/admin/login", methods=["POST"])
    def admin_login_fixed_path():
        from BACKEND.controllers.auth_controller import admin_login
        return admin_login()

    # ── Health check ──────────────────────────────────────────
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "system": "Smart Attendance System",
            "version": "1.0.0"
        }), 200

    @app.route("/api/save-boundary-location", methods=["POST"])
    @app.route("/api/location/save-boundary", methods=["POST"])
    @app.route("/set_boundary", methods=["POST"])
    @app.route("/set-boundary", methods=["POST"])
    @app.route("/update_location", methods=["POST"])
    @app.route("/update-location", methods=["POST"])
    @app.route("/api/student/update-location", methods=["POST"])
    def save_boundary_location():
        print("Boundary route reached")
        from flask import request, jsonify
        data = request.get_json() or {}
        print("Received payload:", data)
        
        address = data.get("address") or data.get("boundary_name") or "Custom Campus Boundary"
        lat = data.get("latitude") or data.get("lat")
        lng = data.get("longitude") or data.get("lng")
        radius = data.get("radius") or 50
        
        if lat is None or lng is None:
            return jsonify({"success": False, "error": "Bad Request", "message": "Latitude and longitude are required."}), 400
            
        lat = float(lat)
        lng = float(lng)
        radius = float(radius)
        
        # 1. Save to PostgreSQL database boundary_locations table
        from DATABASE.connection.db_connection import execute_insert
        query = """
            INSERT INTO boundary_locations (boundary_name, latitude, longitude, updated_time)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id;
        """
        execute_insert(query, (address, lat, lng))

        # Also save to boundary_config table for backward compatibility
        query_config = """
            INSERT INTO boundary_config (boundary_name, latitude, longitude, updated_time)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id;
        """
        execute_insert(query_config, (address, lat, lng))

        # 2. Update CONFIG/college_location_config.py file dynamically
        import os
        config_path = os.path.join(PROJECT_ROOT, "CONFIG", "college_location_config.py")
        try:
            content = f"""# ============================================================
# college_location_config.py — College GPS Coordinates
# ============================================================

COLLEGE_LOCATION = {{
    "name": "My College", 
    "latitude": {lat},
    "longitude": {lng},
    "address": "{address}",
}}

# Active radius
ACTIVE_GEOFENCE_RADIUS = {radius}  # metres

COLLEGE_LAT = {lat}
COLLEGE_LNG = {lng}
RADIUS = ACTIVE_GEOFENCE_RADIUS
"""
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print("Error writing college_location_config.py:", e)
            
        return jsonify({
            "success": True,
            "message": "Boundary updated successfully",
            "lat": lat,
            "lng": lng,
            "radius": radius
        })

    @app.route('/confirm_boundary', methods=['POST'])
    @app.route('/api/confirm_boundary', methods=['POST'])
    def confirm_boundary():
        print("Boundary route reached")
        from flask import request, jsonify, redirect
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form or {}
        print("Received payload:", data)
            
        address = data.get("address") or data.get("boundary_name") or "Custom Campus Boundary"
        lat = data.get("latitude") or data.get("lat")
        lng = data.get("longitude") or data.get("lng")
        
        if lat is None or lng is None:
            if request.is_json:
                return jsonify({"success": False, "error": "Bad Request", "message": "Latitude and longitude are required."}), 400
            else:
                return "Latitude and longitude are required.", 400
                
        lat = float(lat)
        lng = float(lng)
        
        # 1. Save to PostgreSQL database boundary_locations table
        from DATABASE.connection.db_connection import execute_insert
        query = """
            INSERT INTO boundary_locations (boundary_name, latitude, longitude, updated_time)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id;
        """
        execute_insert(query, (address, lat, lng))

        # Also save to boundary_config table for backward compatibility
        query_config = """
            INSERT INTO boundary_config (boundary_name, latitude, longitude, updated_time)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id;
        """
        execute_insert(query_config, (address, lat, lng))

        # 2. Update CONFIG/college_location_config.py file dynamically
        import os
        config_path = os.path.join(PROJECT_ROOT, "CONFIG", "college_location_config.py")
        try:
            content = f"""# ============================================================
# college_location_config.py — College GPS Coordinates
# ============================================================

COLLEGE_LOCATION = {{
    "name": "My College", 
    "latitude": {lat},
    "longitude": {lng},
    "address": "{address}",
}}

# Active radius — strictly set to 50m for attendance validation
ACTIVE_GEOFENCE_RADIUS = 50  # metres

COLLEGE_LAT = {lat}
COLLEGE_LNG = {lng}
RADIUS = ACTIVE_GEOFENCE_RADIUS
"""
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print("Error writing college_location_config.py:", e)
            
        if request.is_json:
            return jsonify({
                "success": True
            })
        else:
            return redirect('/dashboard')

    # ── Serve Frontend HTML pages ─────────────────────────────
    @app.route("/")
    def splash_screen():
        return send_from_directory(FRONTEND_PAGES, "splash.html")

    @app.route("/login")
    @app.route("/login.html")
    def index():
        return send_from_directory(FRONTEND_PAGES, "login.html")

    @app.route("/register")
    @app.route("/register.html")
    def register_page():
        return send_from_directory(FRONTEND_PAGES, "register.html")
        
    @app.route("/location.html")
    @app.route("/location")
    def location_page():
        return send_from_directory(FRONTEND_PAGES, "location.html")

    @app.route("/dashboard")
    @app.route("/dashboard.html")
    def dashboard():
        return send_from_directory(FRONTEND_PAGES, "dashboard.html")

    @app.route("/profile")
    @app.route("/profile.html")
    def profile():
        return send_from_directory(FRONTEND_PAGES, "profile.html")

    @app.route("/history")
    @app.route("/history.html")
    def history():
        return send_from_directory(FRONTEND_PAGES, "history.html")

    @app.route("/auto-verification")
    @app.route("/auto_verification.html")
    def auto_verification_page():
        return send_from_directory(FRONTEND_PAGES, "auto_verification.html")

    @app.route("/face-scan")
    @app.route("/face_verification.html")
    def face_scan():
        return send_from_directory(FRONTEND_PAGES, "face_verification.html")

    @app.route("/fingerprint")
    @app.route("/fingerprint.html")
    def fingerprint_page():
        return send_from_directory(FRONTEND_PAGES, "fingerprint.html")

    @app.route("/monitoring")
    def monitoring():
        return send_from_directory(FRONTEND_PAGES, "monitoring.html")

    @app.route("/admin")
    def admin_tracking():
        return send_from_directory(FRONTEND_PAGES, "admin_tracking.html")
        
    @app.route("/admin-panel")
    def admin_panel():
        return send_from_directory(FRONTEND_PAGES, "admin_panel.html")
        
    @app.route("/auto-verify")
    def auto_verify():
        return send_from_directory(FRONTEND_PAGES, "auto_verify.html")

    @app.route("/map_select.html")
    @app.route("/map-select")
    def map_select():
        return send_from_directory(FRONTEND_PAGES, "map_select.html")

    @app.route("/admin_boundary.html")
    @app.route("/admin-boundary")
    def admin_boundary():
        return send_from_directory(FRONTEND_PAGES, "admin_boundary.html")

    @app.route("/settings.html")
    @app.route("/settings")
    def settings_page():
        return send_from_directory(FRONTEND_PAGES, "settings.html")

    @app.route("/student_dashboard")
    @app.route("/student-dashboard")
    def student_dashboard_page():
        return send_from_directory(FRONTEND_PAGES, "student_dashboard.html")

    @app.route("/admin_dashboard")
    @app.route("/admin-dashboard")
    def admin_dashboard_page():
        return send_from_directory(FRONTEND_PAGES, "admin_dashboard.html")

    @app.route("/creator_dashboard")
    @app.route("/creator-dashboard")
    def creator_dashboard_page():
        return send_from_directory(FRONTEND_PAGES, "creator_dashboard.html")

    # ── Creator Admin Management APIs ─────────────────────────
    from BACKEND.middleware.auth_middleware import require_role

    @app.route("/api/admin/verification-logs", methods=["GET"])
    @app.route("/api/admin/auto-verification", methods=["GET"])
    @require_role(["creator", "admin"])
    def get_verification_logs(current_student=None):
        from DATABASE.connection.db_connection import execute_query
        from flask import request
        dept = request.args.get("department")
        section = request.args.get("section")
        sort = request.args.get("sort", "A-Z")
        
        query = """
            SELECT l.*, s.name, s.department, s.class_name 
            FROM auto_verify_log l
            JOIN students s ON l.student_id = s.student_id
            WHERE 1=1
        """
        params = []
        if dept:
            query += " AND s.department = %s"
            params.append(dept)
        if section:
            query += " AND s.class_name = %s"
            params.append(section)
            
        if sort == "Z-A":
            query += " ORDER BY s.name DESC, l.check_time DESC"
        elif sort == "Roll-A-Z":
            query += " ORDER BY s.student_id ASC, l.check_time DESC"
        elif sort == "Roll-Z-A":
            query += " ORDER BY s.student_id DESC, l.check_time DESC"
        else:
            query += " ORDER BY l.check_time DESC"
            
        query += " LIMIT 100"
        logs = execute_query(query, tuple(params), fetch="all") or []
        return jsonify({"success": True, "logs": logs})

    # --- NEW CREATOR APIs ---

    @app.route("/api/users", methods=["GET"])
    @require_role(["creator"])
    def api_get_users(current_student=None):
        from DATABASE.connection.db_connection import execute_query
        print("Users Loaded")
        query = "SELECT student_id, name, email, role, department, is_active, last_login FROM students ORDER BY role DESC, name ASC"
        users = execute_query(query, fetch="all")
        return jsonify({"success": True, "users": users})

    @app.route("/api/make-admin", methods=["POST"])
    @app.route("/api/creator/grant-admin", methods=["POST"])
    @app.route("/api/admin/make-admin", methods=["POST"])
    @require_role(["creator"])
    def api_make_admin(current_student=None):
        from DATABASE.connection.db_connection import execute_insert, execute_query
        from BACKEND.services.auth_service import AuthService
        from flask import request
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '')
        dept = data.get('department', '')

        if not email or not name:
            return jsonify({"success": False, "message": "Email and Name are required"}), 400

        # Check existing
        existing = execute_query("SELECT id, student_id FROM students WHERE email = %s", (email,), fetch="one")
        
        if existing:
            # Update existing user to admin
            execute_insert("UPDATE students SET role = 'admin', department = %s, is_active = 1 WHERE email = %s", (dept, email))
            return jsonify({"success": True, "message": "User elevated to admin access!"})
        else:
            # Create new admin
            if not password:
                return jsonify({"success": False, "message": "Password required for new admin"}), 400
            
            import random
            new_sid = f"ADM{random.randint(10000, 99999)}"
            p_hash = AuthService.hash_password(password)
            
            execute_insert("""
                INSERT INTO students (student_id, name, email, password_hash, department, role, is_active) 
                VALUES (%s, %s, %s, %s, %s, 'admin', 1)
            """, (new_sid, name, email, p_hash, dept))
            
            return jsonify({"success": True, "message": "New admin user created successfully!"})

    @app.route("/api/creator/revoke-admin", methods=["POST"])
    @app.route("/api/remove-admin", methods=["POST"])
    @require_role(["creator"])
    def api_remove_admin(current_student=None):
        from flask import request
        from DATABASE.connection.db_connection import execute_insert
        data = request.get_json() or {}
        sid = data.get('student_id')
        if not sid: 
            return jsonify({"success": False, "message": "student_id missing"}), 400
        
        # Set role back to 'student' (the base user role)
        execute_insert("UPDATE students SET role = 'student' WHERE student_id = %s AND role != 'creator'", (sid,))
        return jsonify({"success": True, "message": "Admin privileges revoked."})

    @app.route("/api/disable-user", methods=["POST"])
    @require_role(["creator"])
    def api_disable_user(current_student=None):
        from flask import request
        from DATABASE.connection.db_connection import execute_insert
        data = request.get_json() or {}
        sid = data.get('student_id')
        if not sid: return jsonify({"success": False, "message": "student_id missing"}), 400
        execute_insert("UPDATE students SET is_active = 0 WHERE student_id = %s AND role != 'creator'", (sid,))
        print(f"User Disabled: {sid}")
        return jsonify({"success": True, "message": "User disabled"})

    @app.route("/api/enable-user", methods=["POST"])
    @require_role(["creator"])
    def api_enable_user(current_student=None):
        from flask import request
        from DATABASE.connection.db_connection import execute_insert
        data = request.get_json() or {}
        sid = data.get('student_id')
        if not sid: return jsonify({"success": False, "message": "student_id missing"}), 400
        execute_insert("UPDATE students SET is_active = 1 WHERE student_id = %s", (sid,))
        print(f"User Enabled: {sid}")
        return jsonify({"success": True, "message": "User enabled"})

    @app.route("/api/system-stats", methods=["GET"])
    @require_role(["creator"])
    def api_system_stats(current_student=None):
        from DATABASE.connection.db_connection import execute_query
        total_users = execute_query("SELECT COUNT(*) as count FROM students", fetch="one")["count"]
        total_admins = execute_query("SELECT COUNT(*) as count FROM students WHERE role = 'admin'", fetch="one")["count"]
        active_users = execute_query("SELECT COUNT(*) as count FROM students WHERE is_active = 1", fetch="one")["count"]
        
        # Simple attendance % today logic
        attendance_today = execute_query("SELECT COUNT(DISTINCT student_id) as count FROM attendance WHERE date = CURRENT_DATE", fetch="one")["count"]
        attendance_pct = (attendance_today / total_users * 100) if total_users > 0 else 0
        
        return jsonify({
            "success": True,
            "stats": {
                "total_users": total_users,
                "total_admins": total_admins,
                "active_users": active_users,
                "attendance_pct": round(attendance_pct, 2)
            }
        })

    @app.route("/api/activity-logs", methods=["GET"])
    @require_role(["creator"])
    def api_activity_logs(current_student=None):
        from DATABASE.connection.db_connection import execute_query
        from datetime import timezone, timedelta
        IST = timezone(timedelta(hours=5, minutes=30))
        query = "SELECT name, last_login, role FROM students WHERE last_login IS NOT NULL ORDER BY last_login DESC LIMIT 20"
        logs = execute_query(query, fetch="all")
        for log in (logs or []):
            ll = log.get("last_login")
            if ll and hasattr(ll, "strftime"):
                if ll.tzinfo is None:
                    ll = ll.replace(tzinfo=timezone.utc)
                log["last_login"] = ll.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({"success": True, "logs": logs})

    # --- /api/creator/* namespaced APIs (frontend uses these) ---

    @app.route("/api/creator/users", methods=["GET"])
    @require_role(["creator"])
    def api_creator_get_users(current_student=None):
        from DATABASE.connection.db_connection import execute_query
        from flask import request
        print("Users Loaded")
        
        dept = request.args.get("department")
        section = request.args.get("section")
        sort = request.args.get("sort", "A-Z")
        
        query = "SELECT student_id, name, email, role, department, class_name as section, is_active, last_login FROM students WHERE 1=1"
        params = []
        
        if dept:
            query += " AND department = %s"
            params.append(dept)
        if section:
            query += " AND class_name = %s"
            params.append(section)
            
        if sort == "Z-A":
            query += " ORDER BY role DESC, name DESC"
        elif sort == "Roll-A-Z":
            query += " ORDER BY role DESC, student_id ASC"
        elif sort == "Roll-Z-A":
            query += " ORDER BY role DESC, student_id DESC"
        else:
            query += " ORDER BY role DESC, name ASC"
            
        users = execute_query(query, tuple(params), fetch="all")
        return jsonify({"success": True, "users": users})

    @app.route("/api/creator/make-admin", methods=["POST"])
    @require_role(["creator"])
    def api_creator_make_admin(current_student=None):
        from DATABASE.connection.db_connection import execute_insert
        data = request.get_json() or {}
        sid = data.get('student_id')
        if not sid:
            return jsonify({"success": False, "message": "student_id missing"}), 400
        execute_insert("UPDATE students SET role = 'admin' WHERE student_id = %s AND role != 'creator'", (sid,))
        print(f"Role Changed: {sid} -> admin")
        return jsonify({"success": True, "message": f"User {sid} promoted to admin"})

    @app.route("/api/creator/remove-admin", methods=["POST"])
    @require_role(["creator"])
    def api_creator_remove_admin(current_student=None):
        from DATABASE.connection.db_connection import execute_insert
        data = request.get_json() or {}
        sid = data.get('student_id')
        if not sid:
            return jsonify({"success": False, "message": "student_id missing"}), 400
        execute_insert("UPDATE students SET role = 'student' WHERE student_id = %s AND role != 'creator'", (sid,))
        print(f"Role Changed: {sid} -> student")
        return jsonify({"success": True, "message": f"Admin {sid} demoted to user"})

    @app.route("/api/creator/disable-user", methods=["POST"])
    @require_role(["creator"])
    def api_creator_disable_user(current_student=None):
        from DATABASE.connection.db_connection import execute_insert
        data = request.get_json() or {}
        sid = data.get('student_id')
        if not sid:
            return jsonify({"success": False, "message": "student_id missing"}), 400
        execute_insert("UPDATE students SET is_active = 0 WHERE student_id = %s AND role != 'creator'", (sid,))
        print(f"User Disabled: {sid}")
        return jsonify({"success": True, "message": f"User {sid} disabled"})

    @app.route("/api/creator/enable-user", methods=["POST"])
    @require_role(["creator"])
    def api_creator_enable_user(current_student=None):
        from DATABASE.connection.db_connection import execute_insert
        data = request.get_json() or {}
        sid = data.get('student_id')
        if not sid:
            return jsonify({"success": False, "message": "student_id missing"}), 400
        execute_insert("UPDATE students SET is_active = 1 WHERE student_id = %s", (sid,))
        print(f"User Enabled: {sid}")
        return jsonify({"success": True, "message": f"User {sid} enabled"})

    @app.route("/api/creator/system-stats", methods=["GET"])
    @require_role(["creator"])
    def api_creator_system_stats(current_student=None):
        from DATABASE.connection.db_connection import execute_query
        total_users   = execute_query("SELECT COUNT(*) as c FROM students", fetch="one")["c"]
        total_admins  = execute_query("SELECT COUNT(*) as c FROM students WHERE role = 'admin'", fetch="one")["c"]
        active_users  = execute_query("SELECT COUNT(*) as c FROM students WHERE is_active = 1", fetch="one")["c"]
        disabled_users = execute_query("SELECT COUNT(*) as c FROM students WHERE is_active = 0", fetch="one")["c"]
        today_present = execute_query(
            "SELECT COUNT(DISTINCT student_id) as c FROM attendance WHERE date = CURRENT_DATE",
            fetch="one")["c"]
        today_absent  = max(total_users - today_present, 0)
        return jsonify({
            "success": True,
            "stats": {
                "total_users":    total_users,
                "total_admins":   total_admins,
                "active_users":   active_users,
                "disabled_users": disabled_users,
                "today_present":  today_present,
                "today_absent":   today_absent,
                "boundary_violations": 0
            }
        })

    @app.route("/api/creator/activity-logs", methods=["GET"])
    @require_role(["creator"])
    def api_creator_activity_logs(current_student=None):
        from DATABASE.connection.db_connection import execute_query
        from datetime import timezone, timedelta
        IST = timezone(timedelta(hours=5, minutes=30))
        query = """
            SELECT name, last_login, role, is_active
            FROM students
            WHERE last_login IS NOT NULL
            ORDER BY last_login DESC
            LIMIT 30
        """
        logs = execute_query(query, fetch="all")
        for log in (logs or []):
            ll = log.get("last_login")
            if ll and hasattr(ll, "strftime"):
                if ll.tzinfo is None:
                    ll = ll.replace(tzinfo=timezone.utc)
                log["last_login"] = ll.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({"success": True, "logs": logs})

    @app.route("/api/system/face-config", methods=["GET"])
    def get_face_config():
        from DATABASE.connection.db_connection import execute_query
        res = execute_query("SELECT setting_value FROM system_config WHERE setting_key = 'face_verification_enabled'", fetch="one")
        val = res["setting_value"] if res else "ON"
        return jsonify({"success": True, "enabled": (val == "ON")})

    @app.route("/api/system/face-config", methods=["POST"])
    @require_role(["creator"])
    def set_face_config(current_student=None):
        from DATABASE.connection.db_connection import execute_insert
        from flask import request
        data = request.get_json() or {}
        enabled = data.get("enabled")
        val = "ON" if enabled else "OFF"
        execute_insert("UPDATE system_config SET setting_value = %s WHERE setting_key = 'face_verification_enabled'", (val,))
        return jsonify({"success": True, "message": f"Face Verification globally turned {val}", "enabled": enabled})

    @app.route("/api/system/fingerprint-config", methods=["GET"])
    def get_fingerprint_config():
        from DATABASE.connection.db_connection import execute_query
        res = execute_query("SELECT setting_value FROM system_config WHERE setting_key = 'fingerprint_verification_enabled'", fetch="one")
        val = res["setting_value"] if res else "OFF"
        return jsonify({"success": True, "enabled": (val == "ON")})

    @app.route("/api/system/fingerprint-config", methods=["POST"])
    @require_role(["creator"])
    def set_fingerprint_config(current_student=None):
        from DATABASE.connection.db_connection import execute_insert
        from flask import request
        data = request.get_json() or {}
        enabled = data.get("enabled")
        val = "ON" if enabled else "OFF"
        execute_insert("UPDATE system_config SET setting_value = %s WHERE setting_key = 'fingerprint_verification_enabled'", (val,))
        return jsonify({"success": True, "message": f"Fingerprint Verification globally turned {val}", "enabled": enabled})

    @app.route("/api/fingerprint/status/<sid>", methods=["GET"])
    def check_fingerprint_status(sid):
        from DATABASE.connection.db_connection import execute_query
        res = execute_query("SELECT fingerprint_credential_id FROM students WHERE student_id = %s", (sid,), fetch="one")
        cred_id = res.get("fingerprint_credential_id") if res else None
        enrolled = bool(cred_id)
        return jsonify({"success": True, "enrolled": enrolled, "credential_id": cred_id})

    @app.route("/api/fingerprint/register", methods=["POST"])
    def register_fingerprint():
        from DATABASE.connection.db_connection import execute_insert
        from flask import request
        data = request.get_json() or {}
        sid = data.get("student_id")
        cred_id = data.get("credential_id")
        pub_key = data.get("public_key")
        if not sid or not cred_id:
            return jsonify({"success": False, "message": "Missing real biometric data"}), 400
        
        execute_insert("UPDATE students SET fingerprint_credential_id = %s, fingerprint_public_key = %s WHERE student_id = %s", (cred_id, pub_key, sid))
        return jsonify({"success": True, "message": "Biometric identity linked successfully."})

    @app.route("/api/face/status/<sid>", methods=["GET"])
    def check_face_status(sid):
        from BACKEND.models.face_model import FaceModel
        has_face = FaceModel.has_face_data(sid)
        return jsonify({"success": True, "enrolled": has_face})

    @app.route("/api/attendance/verify-fingerprint", methods=["POST"])
    def verify_fingerprint():
        from DATABASE.connection.db_connection import execute_query, execute_insert
        from CONFIG.college_location_config import COLLEGE_LAT, COLLEGE_LNG, RADIUS
        from BACKEND.services.geofence_service import calculate_distance
        import datetime
        from flask import request

        data = request.get_json() or {}
        student_id = data.get("student_id")
        lat = data.get("latitude")
        lng = data.get("longitude")
        incoming_cred_id = data.get("credential_id") # verify WebAuthn client return object
        
        if not student_id or not lat or not lng or not incoming_cred_id:
            return jsonify({"success": False, "message": "Missing biometric or telemetry payload"}), 400
            
        # Confirm existence
        res = execute_query("SELECT fingerprint_credential_id FROM students WHERE student_id = %s", (student_id,), fetch="one")
        if not res or not res.get("fingerprint_credential_id"):
            return jsonify({"success": False, "message": "Fingerprint not registered. Please setup first."}), 400
            
        db_cred = res["fingerprint_credential_id"]
        # Secure verification of return payload! Must match expected enrollment key.
        if incoming_cred_id != db_cred:
            return jsonify({"success": False, "message": "Real biometric identity mismatch."}), 401

        distance = calculate_distance(lat, lng, COLLEGE_LAT, COLLEGE_LNG)
        is_inside = distance <= RADIUS
        
        # Fetch global toggles
        conf_face = execute_query("SELECT setting_value FROM system_config WHERE setting_key = 'face_verification_enabled'", fetch="one")
        face_on = (conf_face["setting_value"] == "ON") if conf_face else True

        conf_fp = execute_query("SELECT setting_value FROM system_config WHERE setting_key = 'fingerprint_verification_enabled'", fetch="one")
        fp_on = (conf_fp["setting_value"] == "ON") if conf_fp else False

        # FINAL RULE: Present only if Inside Boundary AND (if required) Face matched AND (if required) Fingerprint matched.
        # This route is Fingerprint verification. If Face is ON, we cannot mark Present yet.
        if face_on:
            final_status = "absent" # Still pending face match
        else:
            final_status = "present" if is_inside else "absent"
        
        now = datetime.datetime.now()
        
        # Step A: Partial commit! Set fingerprint_verified=TRUE. 
        # If Face ON: we will finish committing on Face page. 
        # If Face OFF: we commit final presence RIGHT NOW!
        
        if not face_on:
            # Commit final presence
            execute_insert("""
                INSERT INTO attendance 
                (student_id, date, time, status, latitude, longitude, location_valid, fingerprint_verified, remarks, recorded_by_role, face_enabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, 'Fingerprint verified', 'system', FALSE)
                ON CONFLICT (student_id, date, recorded_by_role) DO UPDATE SET
                    status = EXCLUDED.status,
                    fingerprint_verified = TRUE,
                    remarks = 'Fingerprint + boundary passed',
                    face_enabled = FALSE,
                    marked_at = CURRENT_TIMESTAMP
            """, (student_id, now.date(), now.strftime("%H:%M:%S"), final_status, lat, lng, (True if is_inside else False)))
        else:
             # Intermediate save, but DO NOT seal final status yet
             execute_insert("""
                INSERT INTO attendance 
                (student_id, date, time, status, latitude, longitude, location_valid, fingerprint_verified, remarks, recorded_by_role, face_enabled)
                VALUES (%s, %s, %s, 'absent', %s, %s, %s, TRUE, 'Fingerprint verified. Pending face.', 'system', TRUE)
                ON CONFLICT (student_id, date, recorded_by_role) DO UPDATE SET
                    fingerprint_verified = TRUE,
                    face_enabled = TRUE,
                    marked_at = CURRENT_TIMESTAMP
            """, (student_id, now.date(), now.strftime("%H:%M:%S"), lat, lng, (True if is_inside else False)))
             
        return jsonify({
            "success": True,
            "face_required": face_on,
            "is_inside": is_inside,
            "status": final_status,
            "message": "Fingerprint successfully ingested."
        })

    # --- ADVANCED CREATOR FEATURES ---

    @app.route("/api/creator/all-attendance", methods=["GET"])
    @app.route("/api/creator/attendance-logs", methods=["GET"])
    @require_role(["creator"])
    def api_all_attendance(current_student=None):
        from flask import request
        dept = request.args.get("department")
        section = request.args.get("section")
        sort = request.args.get("sort", "A-Z")
        
        query = "SELECT a.*, s.name, s.department, s.class_name FROM attendance a JOIN students s ON a.student_id = s.student_id WHERE 1=1"
        params = []
        if dept:
            query += " AND s.department = %s"
            params.append(dept)
        if section:
            query += " AND s.class_name = %s"
            params.append(section)
            
        if sort == "Z-A":
            query += " ORDER BY s.name DESC, a.marked_at DESC"
        elif sort == "Roll-A-Z":
            query += " ORDER BY s.student_id ASC, a.marked_at DESC"
        elif sort == "Roll-Z-A":
            query += " ORDER BY s.student_id DESC, a.marked_at DESC"
        else:
            query += " ORDER BY a.marked_at DESC"
            
        query += " LIMIT 500"
        records = execute_query(query, tuple(params), fetch="all") or []
        import datetime
        for r in records:
            if r.get("marked_at") and hasattr(r["marked_at"], "strftime"):
                r["marked_at"] = r["marked_at"].strftime("%Y-%m-%d %H:%M:%S")
            if r.get("date") and hasattr(r["date"], "strftime"):
                r["date"] = r["date"].strftime("%Y-%m-%d")
            if r.get("time") and hasattr(r["time"], "strftime"):
                r["time"] = r["time"].strftime("%H:%M:%S")
        return jsonify({"success": True, "records": records})

    @app.route("/api/creator/boundary-settings", methods=["GET"])
    @require_role(["creator"])
    def api_boundary_settings(current_student=None):
        from DATABASE.connection.db_connection import execute_query
        # Fetching all users' boundary settings (if any exist in a table)
        # For now, fetching from boundary_locations which seems to be the global config
        query = "SELECT * FROM boundary_locations ORDER BY updated_time DESC"
        settings = execute_query(query, fetch="all")
        return jsonify({"success": True, "settings": settings})

    @app.route("/api/creator/gps-history", methods=["GET"])
    @require_role(["creator"])
    def api_gps_history(current_student=None):
        from DATABASE.connection.db_connection import execute_query
        # Basic GPS history from attendance records
        query = "SELECT student_id, latitude, longitude, marked_at FROM attendance ORDER BY marked_at DESC LIMIT 200"
        history = execute_query(query, fetch="all")
        return jsonify({"success": True, "history": history})

    @app.route("/api/creator/reset-today-attendance", methods=["POST"])
    @app.route("/api/creator/reset-attendance", methods=["POST"])
    @require_role(["creator"])
    def api_reset_attendance(current_student=None):
        from DATABASE.connection.db_connection import execute_insert
        # Reset attendance for today - correct column name usage
        execute_insert("DELETE FROM attendance WHERE date = CURRENT_DATE")
        return jsonify({"success": True, "message": "Attendance for today has been reset."})

    # ── Explicit Alias Endpoints Mandatory Implementation ─────────────────
    # (Kept for compatibility with existing JS if any)
    
    @app.route("/set-role", methods=["POST"])
    @require_role(["creator"])
    def api_set_role(current_student=None):
        return api_make_admin(current_student)

    @app.route("/remove-role", methods=["POST"])
    @require_role(["creator"])
    def api_remove_role(current_student=None):
        return api_remove_admin(current_student)

    @app.route("/disable-user", methods=["POST"])
    @require_role(["creator"])
    def api_disable_user_alias(current_student=None):
        return api_disable_user(current_student)

    @app.route("/make-admin", methods=["POST"])
    @require_role(["creator"])
    def api_make_admin_exact_alias(current_student=None):
        return api_make_admin(current_student)

    # ── User Requested Aliases ────────────────────────────────────────

    @app.route("/api/creator/admins", methods=["GET"])
    @require_role(["creator"])
    def api_creator_admins(current_student=None):
        from DATABASE.connection.db_connection import execute_query
        query = "SELECT student_id, name, email, role, department, is_active, last_login FROM students WHERE role = 'admin' ORDER BY name ASC"
        admins = execute_query(query, fetch="all")
        return jsonify({"success": True, "users": admins})



    @app.route("/remove-admin", methods=["POST"])
    @require_role(["creator"])
    def api_remove_admin_exact_alias(current_student=None):
        return api_remove_admin(current_student)


    # ── Admin API: Overview Stats ─────────────────────────────

    @app.route("/api/admin/overview-stats", methods=["GET"])
    @require_role(["creator", "admin"])
    def api_admin_overview_stats(current_student=None):
        from DATABASE.connection.db_connection import execute_query
        total_students = execute_query(
            "SELECT COUNT(*) as c FROM students WHERE role NOT IN ('creator','admin')",
            fetch="one")["c"]
        today_present  = execute_query(
            "SELECT COUNT(DISTINCT student_id) as c FROM attendance WHERE date = CURRENT_DATE AND status = 'present'",
            fetch="one")["c"]
        today_absent   = max(total_students - today_present, 0)

        # Fetch current boundary
        res_loc = execute_query("SELECT latitude, longitude FROM boundary_locations ORDER BY updated_time DESC LIMIT 1", fetch="one")
        if res_loc:
            c_lat = float(res_loc["latitude"])
            c_lng = float(res_loc["longitude"])
        else:
            try:
                from CONFIG.college_location_config import COLLEGE_LAT, COLLEGE_LNG
                c_lat, c_lng = COLLEGE_LAT, COLLEGE_LNG
            except:
                c_lat, c_lng = 0.0, 0.0
            
        def haversine_local(lat1, lon1, lat2, lon2):
            import math
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlam = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        # Count inside/outside from auto_verify_log (latest per student today)
        latest_logs = execute_query("""
            SELECT DISTINCT ON (student_id) student_id, latitude, longitude 
            FROM auto_verify_log 
            WHERE DATE(check_time) = CURRENT_DATE 
            ORDER BY student_id, check_time DESC
        """, fetch="all") or []
        
        inside_count, outside_count = 0, 0
        for log in latest_logs:
            if log.get("latitude") and log.get("longitude"):
                dist = haversine_local(log["latitude"], log["longitude"], c_lat, c_lng)
                if dist <= 50: inside_count += 1
                else: outside_count += 1

        return jsonify({
            "success": True,
            "stats": {
                "total_students":  total_students,
                "today_present":   today_present,
                "today_absent":    today_absent,
                "inside_boundary": inside_count,
                "outside_boundary": outside_count
            }
        })

    # ── Admin API: Boundary Status (Haversine) ────────────────

    @app.route("/api/admin/boundary-status", methods=["GET"])
    @app.route("/api/admin/boundary-checks", methods=["GET"])
    @app.route("/api/creator/boundary-status", methods=["GET"])
    @require_role(["creator", "admin"])
    def api_admin_boundary_status(current_student=None):
        from DATABASE.connection.db_connection import execute_query
        import math

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlam = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        res_loc = execute_query("SELECT latitude, longitude FROM boundary_locations ORDER BY updated_time DESC LIMIT 1", fetch="one")
        if res_loc:
            COLLEGE_LAT = float(res_loc["latitude"])
            COLLEGE_LNG = float(res_loc["longitude"])
        else:
            try:
                from CONFIG.college_location_config import COLLEGE_LAT, COLLEGE_LNG
            except Exception:
                COLLEGE_LAT, COLLEGE_LNG = 0.0, 0.0
        
        try:
            from CONFIG.college_location_config import RADIUS
            ACTIVE_GEOFENCE_RADIUS = RADIUS
        except Exception:
            ACTIVE_GEOFENCE_RADIUS = 50
        from flask import request
        dept = request.args.get("department")
        section = request.args.get("section")
        sort = request.args.get("sort", "A-Z")
        
        query = "SELECT student_id, name, email, department FROM students WHERE is_active = 1 AND role NOT IN ('creator','admin')"
        params = []
        if dept:
            query += " AND department = %s"
            params.append(dept)
        if section:
            query += " AND class_name = %s"
            params.append(section)
            
        if sort == "Z-A":
            query += " ORDER BY name DESC"
        elif sort == "Roll-A-Z":
            query += " ORDER BY student_id ASC"
        elif sort == "Roll-Z-A":
            query += " ORDER BY student_id DESC"
        else:
            query += " ORDER BY name ASC"
            
        students = execute_query(query, tuple(params), fetch="all") or []

        # Get latest GPS log per student from auto_verify_log (Today only)
        logs = execute_query("""
            SELECT DISTINCT ON (student_id)
                student_id, gps_status, latitude, longitude, distance_meters, check_time
            FROM auto_verify_log
            WHERE DATE(check_time) = CURRENT_DATE
            ORDER BY student_id, check_time DESC
        """, fetch="all") or []
        log_map = {l["student_id"]: l for l in logs}

        from datetime import timezone, timedelta
        IST = timezone(timedelta(hours=5, minutes=30))

        result = []
        for s in students:
            log = log_map.get(s["student_id"])
            if log and log.get("latitude") and log.get("longitude"):
                dist = haversine(log["latitude"], log["longitude"], COLLEGE_LAT, COLLEGE_LNG)
                gps_status = "inside" if dist <= ACTIVE_GEOFENCE_RADIUS else "outside"
                ct = log.get("check_time")
                if ct:
                    # DB returns UTC-naive; attach UTC then convert to IST
                    if ct.tzinfo is None:
                        ct = ct.replace(tzinfo=timezone.utc)
                    check_time = ct.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    check_time = None
            else:
                dist, gps_status, check_time = None, "unknown", None

            result.append({
                "student_id": s["student_id"],
                "name":       s["name"],
                "email":      s["email"],
                "department": s["department"],
                "gps_status": gps_status,
                "distance":   round(dist, 1) if dist is not None else None,
                "last_check": check_time
            })
            
        # Sorting should ideally be based on the selected option or by check_time if not specified
        # But we'll retain the requested name sort by not overriding it completely.
        # If user wants A-Z, we'll keep the students order. 
        if sort == "Z-A":
            result.sort(key=lambda x: x.get("name") or "", reverse=True)
        elif sort == "Roll-A-Z":
            result.sort(key=lambda x: x.get("student_id") or "")
        elif sort == "Roll-Z-A":
            result.sort(key=lambda x: x.get("student_id") or "", reverse=True)
        else:
            result.sort(key=lambda x: x.get("name") or "")
            
        return jsonify({"success": True, "students": result})

    # ── Admin API: Mark Attendance ────────────────────────────

    @app.route("/api/admin/mark-attendance", methods=["POST"])
    @require_role(["creator", "admin"])
    def api_admin_mark_attendance(current_student=None):
        from DATABASE.connection.db_connection import execute_query, execute_insert
        from flask import request
        from datetime import datetime, date, time, timedelta, timezone
        IST = timezone(timedelta(hours=5, minutes=30))
        
        data = request.get_json() or {}
        student_id = data.get("student_id")
        status = (data.get("status") or "present").lower()
        distance = data.get("distance")
        
        if status not in ["present", "absent"]:
            status = "present"
            
        if not student_id:
            return jsonify({"success": False, "message": "student_id required"}), 400

        now = datetime.now(IST)
        
        # ── 45-minute Manual Update Lock ──
        existing_rec = execute_query("""
            SELECT marked_at FROM attendance 
            WHERE student_id = %s AND date = %s AND recorded_by_role IN ('admin', 'creator')
            LIMIT 1
        """, (student_id, now.date()), fetch="one")
        
        if existing_rec and existing_rec.get("marked_at"):
            last_at = existing_rec["marked_at"]
            if isinstance(last_at, str):
                try: last_at = datetime.fromisoformat(last_at)
                except: pass
            # FIX: DB returns naive datetime; normalise to UTC-aware before subtracting
            if hasattr(last_at, 'tzinfo') and last_at.tzinfo is None:
                last_at = last_at.replace(tzinfo=timezone.utc)
            diff_mins = (now - last_at).total_seconds() / 60
            if diff_mins < 45:
                return jsonify({
                    "success": False,
                    "message": "Manual attendance can be updated again after 45 minutes."
                }), 403

        marked_by = current_student.get("role", "admin") if current_student else "admin"
        admin_name = current_student.get("name") if current_student else None
        if not admin_name and current_student:
            admin_name = current_student.get("email")
            
        # Remarks for manual update
        remarks = "Attendance manually updated"
        
        try:
            execute_insert("""
                INSERT INTO attendance
                    (student_id, date, time, status, recorded_by_role, remarks, marked_by_name,
                     face_match_status, marked_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'not_attempted', CURRENT_TIMESTAMP)
            """, (
                student_id, now.date(), now.strftime("%H:%M:%S"),
                status, marked_by,
                remarks,
                admin_name
            ))
            return jsonify({"success": True, "message": f"Attendance for today set successfully!"})
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e).lower() or "unique constraint" in str(e).lower():
                return jsonify({"success": False, "message": "Attendance already marked for today."}), 400
            return jsonify({"success": False, "message": "Failed to mark attendance. Database error."}), 500

    @app.route("/api/admin/manual-attendance", methods=["POST"])
    @require_role(["creator", "admin"])
    def api_admin_manual_attendance(current_student=None):
        from DATABASE.connection.db_connection import execute_insert, execute_query
        from flask import request
        from datetime import datetime, date, time, timedelta, timezone
        IST = timezone(timedelta(hours=5, minutes=30))
        data = request.get_json() or {}
        username = data.get("username")
        status   = (data.get("status") or "present").lower()
        if status not in ["present", "absent"]:
            status = "present"
        print(f"Saving manual attendance: {username}, {status}")

        if not username:
            return jsonify({"success": False, "message": "Username required"}), 400
        
        # Resolve username to student_id by checking name or student_id
        user = execute_query("SELECT student_id FROM students WHERE name = %s OR student_id = %s LIMIT 1", (username, username), fetch="one")
        if not user:
            return jsonify({"success": False, "message": f"User not found: {username}"}), 404
        
        sid = user["student_id"]
        now = datetime.now(IST)
        
        # ── 45-minute Manual Update Lock ──
        existing_rec = execute_query("""
            SELECT marked_at FROM attendance 
            WHERE student_id = %s AND date = %s AND recorded_by_role IN ('admin', 'creator')
            LIMIT 1
        """, (sid, now.date()), fetch="one")
        
        if existing_rec and existing_rec.get("marked_at"):
            last_at = existing_rec["marked_at"]
            if isinstance(last_at, str):
                try: last_at = datetime.fromisoformat(last_at)
                except: pass
            # FIX: DB returns naive datetime; normalise to UTC-aware before subtracting
            if hasattr(last_at, 'tzinfo') and last_at.tzinfo is None:
                last_at = last_at.replace(tzinfo=timezone.utc)
            diff_mins = (now - last_at).total_seconds() / 60
            if diff_mins < 45:
                return jsonify({
                    "success": False,
                    "message": "Manual attendance can be updated again after 45 minutes."
                }), 403

        marked_by = current_student.get("role", "admin") if current_student else "admin"
        admin_name = current_student.get("name") if current_student else None
        if not admin_name and current_student:
            admin_name = current_student.get("email")
        
        # Remarks for manual update
        remarks = 'Attendance manually updated'
        
        try:
            execute_insert("""
                INSERT INTO attendance
                    (student_id, date, time, status, recorded_by_role, remarks, marked_by_name,
                     face_match_status, marked_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'not_attempted', CURRENT_TIMESTAMP)
            """, (
                sid, now.date(), now.strftime("%H:%M:%S"),
                status, marked_by,
                remarks,
                admin_name
            ))
            return jsonify({"success": True, "message": f"Set {status.upper()} for {username}"})
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e).lower() or "unique constraint" in str(e).lower():
                return jsonify({"success": False, "message": "Attendance already marked for today."}), 400
            return jsonify({"success": False, "message": "Failed to mark attendance. Database error."}), 500

    @app.route("/api/admin/search-students", methods=["GET"])
    @require_role(["creator", "admin"])
    def api_admin_search_students(current_student=None):
        from flask import request
        from DATABASE.connection.db_connection import execute_query
        q = request.args.get('q', '').strip()
        if not q:
            return jsonify({"success": True, "students": []})
        term = f"%{q}%"
        query = """
            SELECT DISTINCT ON (s.student_id)
                   s.student_id, s.name, s.email, s.department, s.class_name as section,
                   COALESCE(v.gps_status, 'unknown') as gps_status
            FROM students s
            LEFT JOIN auto_verify_log v ON s.student_id = v.student_id
            WHERE (s.name ILIKE %s OR s.email ILIKE %s OR s.student_id ILIKE %s)
              AND s.role NOT IN ('creator', 'admin')
            ORDER BY s.student_id, v.check_time DESC
            LIMIT 8
        """
        results = execute_query(query, (term, term, term), fetch="all")
        return jsonify({"success": True, "students": results or []})


    # ── Admin API: Attendance Logs ────────────────────────────

    @app.route("/api/admin/attendance-logs", methods=["GET"])
    @require_role(["creator", "admin"])
    def api_admin_attendance_logs(current_student=None):
        from flask import request
        dept = request.args.get("department")
        section = request.args.get("section")
        sort = request.args.get("sort", "A-Z")
        
        # Comprehensive query joined with stats for attendance percentage
        # We use LEFT JOIN on attendance to include students who haven't marked today
        query = """
            WITH StudentStats AS (
                SELECT 
                    student_id,
                    COUNT(*) as total_days,
                    SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_days
                FROM attendance
                GROUP BY student_id
            )
            SELECT a.student_id, s.name, s.email, a.date, a.time, s.department, s.class_name,
                   COALESCE(a.status, 'absent') as status,
                   COALESCE(a.recorded_by_role, 'system') as recorded_by_role,
                   a.marked_at, a.face_match_status, a.location_valid, a.remarks,
                   ROUND((COALESCE(stats.present_days, 0)::numeric / NULLIF(stats.total_days, 1)::numeric) * 100, 2) as attendance_percentage
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id AND a.date = CURRENT_DATE
            LEFT JOIN StudentStats stats ON s.student_id = stats.student_id
            WHERE s.role NOT IN ('creator', 'admin') AND s.is_active = 1
        """
        params = []
        if dept:
            query += " AND s.department = %s"
            params.append(dept)
        if section:
            query += " AND s.class_name = %s"
            params.append(section)
            
        # Sorting maps
        if sort == "Z-A":
            query += " ORDER BY s.name DESC"
        elif sort == "Roll-A-Z" or sort == "ID-A-Z":
            query += " ORDER BY s.student_id ASC"
        elif sort == "Roll-Z-A" or sort == "ID-Z-A":
            query += " ORDER BY s.student_id DESC"
        else:
            query += " ORDER BY s.name ASC"
            
        query += " LIMIT 2000"
        records = execute_query(query, tuple(params), fetch="all") or []
        import datetime
        for r in records:
            if r.get("marked_at") and isinstance(r["marked_at"], (datetime.datetime, datetime.date)):
                r["marked_at"] = r["marked_at"].strftime("%Y-%m-%d %H:%M:%S")
            if r.get("date") and hasattr(r["date"], "strftime"):
                r["date"] = r["date"].strftime("%Y-%m-%d")
            else:
                # If no record today, show current date for reporting context if needed
                r["date"] = datetime.date.today().strftime("%Y-%m-%d")
                
            if r.get("time") and hasattr(r["time"], "strftime"):
                r["time"] = r["time"].strftime("%H:%M:%S")
            elif not r.get("time"):
                r["time"] = "N/A"
                
            if r.get("attendance_percentage") is None:
                r["attendance_percentage"] = 0
                
        return jsonify({"success": True, "records": records})

    # ── Serve static assets (css/js) ──────────────────────────
    @app.route("/css/<path:filename>")
    def serve_css(filename):
        return send_from_directory(os.path.join(FRONTEND_ROOT, "css"), filename)

    @app.route("/js/<path:filename>")
    def serve_js(filename):
        return send_from_directory(os.path.join(FRONTEND_ROOT, "js"), filename)

    return app


# if __name__ == "__main__":
#     app = create_app()
#     print("=" * 60)
#     print("  SMART ATTENDANCE SYSTEM")
#     print(f"  Project Root : {PROJECT_ROOT}")
#     print("  Server URL   : http://127.0.0.1:5000")
#     print("=" * 60)
#     app.run(host="0.0.0.0", port=5000, debug=True)
app = create_app()

if __name__ == "__main__":                                                
    print("=" * 60)                                  
    print(" SMART ATTENDANCE SYSTEM")               
    print(f" Project Root : {PROJECT_ROOT}")         
    print(" Server URL : http://127.0.0.1:5000")    
    print("=" * 60)                                 
    app.run(host="0.0.0.0", port=5000, debug=True)  