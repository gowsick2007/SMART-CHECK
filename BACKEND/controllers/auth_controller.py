# ============================================================
# auth_controller.py — Authentication Controller (Route Handlers)
# ============================================================

from flask import request, jsonify
from BACKEND.services.auth_service import AuthService


def register():
    """POST /api/auth/register"""
    data = request.get_json()
    required = ["student_id", "name", "email", "password", "department", "year"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "message": f"Missing fields: {', '.join(missing)}"}), 400

    result = AuthService.register_student(data)
    status = 201 if result["success"] else 409
    return jsonify(result), status


def login():
    """POST /api/auth/login"""
    data = request.get_json()
    identifier = data.get("identifier") or data.get("student_id") or data.get("email", "")
    password = data.get("password", "")

    if not identifier or not password:
        return jsonify({"success": False, "message": "Identifier and password are required."}), 400

    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent", "")
    result = AuthService.login(identifier, password, ip=ip, user_agent=user_agent)
    status = 200 if result["success"] else 401
    return jsonify(result), status

def creator_login():
    """POST /api/auth/creator/login"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    CREATOR_EMAIL = 'gowsicklitheswaran@gmail.com'
    CREATOR_PASSWORD = 'your_creator_password_here'  # TODO: set securely

    if email != CREATOR_EMAIL:
        return jsonify({"success": False, "message": "Creator access denied"}), 403
    if password != CREATOR_PASSWORD:
        return jsonify({"success": False, "message": "Invalid creator password"}), 401

    import jwt, datetime
    from BACKEND.config.server_config import Config
    token = jwt.encode({
        "email": email,
        "role": "creator",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, Config.SECRET_KEY, algorithm="HS256")

    return jsonify({
        "success": True,
        "token": token,
        "role": "creator",
        "student": {
            "name": "System Creator",
            "email": email,
            "role": "creator"
        }
    })


def logout():
    """POST /api/auth/logout"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        result = AuthService.logout(token)
        return jsonify(result), 200
    return jsonify({"success": False, "message": "No active session found."}), 400


def validate_token():
    """GET /api/auth/validate"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        session = AuthService.validate_token(token)
        if session:
            return jsonify({"success": True, "valid": True, "student_id": session["student_id"]}), 200
    return jsonify({"success": False, "valid": False}), 401
