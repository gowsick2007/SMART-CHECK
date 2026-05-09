# ============================================================
# student_routes.py — Student API Routes
# ============================================================

from flask import Blueprint
from BACKEND.controllers.student_controller import get_profile, get_all_students, get_student_by_id

student_bp = Blueprint("student", __name__, url_prefix="/api/student")
location_bp = Blueprint("location", __name__, url_prefix="/api/location")

student_bp.route("/profile", methods=["GET"])(get_profile)
student_bp.route("/all", methods=["GET"])(get_all_students)
student_bp.route("/<student_id>", methods=["GET"])(get_student_by_id)


from BACKEND.middleware.auth_middleware import require_auth

@location_bp.route("/save-boundary", methods=["POST"])
@location_bp.route("/save-boundary-location", methods=["POST"])
@location_bp.route("/confirm_boundary", methods=["POST"])
@student_bp.route("/update-location", methods=["POST"])
def save_boundary():
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
    _HERE = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(_HERE))
    config_path = os.path.join(_PROJECT_ROOT, "CONFIG", "college_location_config.py")
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

