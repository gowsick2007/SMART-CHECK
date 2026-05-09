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

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from BACKEND.config.server_config import DevelopmentConfig
from BACKEND.routes.auth_routes import auth_bp
from BACKEND.routes.student_routes import student_bp, location_bp
from BACKEND.routes.attendance_routes import attendance_bp
from BACKEND.routes.face_routes import face_bp
from BACKEND.routes.admin_routes import admin_bp
from BACKEND.routes.auto_verify_routes import auto_verify_bp
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

    # CORS — allow all origins including 'null' (sent by browsers when HTML is opened from file://)
    CORS(app)

    # Register all Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(location_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(face_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auto_verify_bp)

    # Register global error handlers
    register_error_handlers(app)

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
        
        if lat is None or lng is None:
            return jsonify({"success": False, "error": "Bad Request", "message": "Latitude and longitude are required."}), 400
            
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

# Active radius — strictly set to 22.5m for attendance validation
ACTIVE_GEOFENCE_RADIUS = 22.5  # metres

COLLEGE_LAT = {lat}
COLLEGE_LNG = {lng}
RADIUS = ACTIVE_GEOFENCE_RADIUS
"""
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print("Error writing college_location_config.py:", e)
            
        return jsonify({
            "success": True
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

# Active radius — strictly set to 22.5m for attendance validation
ACTIVE_GEOFENCE_RADIUS = 22.5  # metres

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
    def index():
        return send_from_directory(FRONTEND_PAGES, "login.html")

    @app.route("/register")
    def register_page():
        return send_from_directory(FRONTEND_PAGES, "register.html")

    @app.route("/dashboard")
    def dashboard():
        return send_from_directory(FRONTEND_PAGES, "dashboard.html")

    @app.route("/profile")
    def profile():
        return send_from_directory(FRONTEND_PAGES, "profile.html")

    @app.route("/history")
    def history():
        return send_from_directory(FRONTEND_PAGES, "attendance_history.html")

    @app.route("/face-scan")
    def face_scan():
        return send_from_directory(FRONTEND_PAGES, "face_scan.html")

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
    @app.route("/api/creator/admins", methods=["GET"])
    def get_creator_admins():
        from DATABASE.connection.db_connection import execute_query
        admins = execute_query("SELECT student_id, name, email, department, role FROM students WHERE role = 'admin'", fetch="all")
        return jsonify({"success": True, "admins": admins})

    @app.route("/api/creator/admins", methods=["POST"])
    def create_creator_admin():
        from flask import request
        from DATABASE.connection.db_connection import execute_query, execute_insert
        from BACKEND.services.auth_service import AuthService
        data = request.get_json() or {}
        student_id = data.get("student_id", "").strip()
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        department = data.get("department", "").strip()
        
        if not student_id or not name or not email or not password:
            return jsonify({"success": False, "message": "All fields are required"}), 400
            
        exists = execute_query("SELECT id FROM students WHERE student_id = %s OR email = %s", (student_id, email), fetch="one")
        if exists:
            return jsonify({"success": False, "message": "Admin with this ID or Email already exists"}), 400
            
        password_hash = AuthService.hash_password(password)
        execute_insert("""
            INSERT INTO students (student_id, name, email, password_hash, department, role, class_name, year)
            VALUES (%s, %s, %s, %s, %s, 'admin', 'Section A', 'Admin Year')
        """, (student_id, name, email, password_hash, department))
        
        return jsonify({"success": True, "message": "Admin created successfully"})

    @app.route("/api/creator/admins/<student_id>", methods=["DELETE"])
    def delete_creator_admin(student_id):
        from DATABASE.connection.db_connection import execute_query, execute_insert
        admin = execute_query("SELECT email, role FROM students WHERE student_id = %s", (student_id,), fetch="one")
        if admin:
            if admin["email"] == "gowsicklitheswaran@gmail.com" or admin["role"] == "creator":
                return jsonify({"success": False, "message": "Super Admin Creator cannot be deleted"}), 400
                
        execute_insert("DELETE FROM students WHERE student_id = %s AND role = 'admin'", (student_id,))
        return jsonify({"success": True, "message": "Admin deleted successfully"})

    # ── Serve static assets (css/js) ──────────────────────────
    @app.route("/css/<path:filename>")
    def serve_css(filename):
        return send_from_directory(os.path.join(FRONTEND_ROOT, "css"), filename)

    @app.route("/js/<path:filename>")
    def serve_js(filename):
        return send_from_directory(os.path.join(FRONTEND_ROOT, "js"), filename)

    return app


if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("  SMART ATTENDANCE SYSTEM — Flask Server")
    print(f"  Project Root : {PROJECT_ROOT}")
    print("  Server URL   : http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
