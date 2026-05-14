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
    """POST /api/auth/login — ONLY STUDENT"""
    data = request.get_json()
    identifier = data.get("identifier") or data.get("student_id") or data.get("email", "")
    password = data.get("password", "")

    if not identifier or not password:
        return jsonify({"success": False, "message": "Identifier and password are required."}), 400

    if identifier.strip().lower() == 'gowsicklitheswaran@gmail.com':
        return jsonify({"success": False, "message": "Use Creator Login"}), 403

    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent", "")
    
    # Enforce student role
    result = AuthService.login(identifier, password, ip=ip, user_agent=user_agent, required_role='student')
    status = 200 if result["success"] else 401
    
    if result.get("success") and "student" in result:
        result["role"] = result["student"].get("role", "student")
        
    return jsonify(result), status


def admin_login():
    """POST /api/auth/admin/login — ONLY ADMIN"""
    data = request.get_json()
    identifier = data.get("identifier") or data.get("student_id") or data.get("email", "")
    password = data.get("password", "")

    if not identifier or not password:
        return jsonify({"success": False, "message": "Identifier and password are required."}), 400

    if identifier.strip().lower() == 'gowsicklitheswaran@gmail.com':
        return jsonify({"success": False, "message": "Use Creator Login"}), 403

    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent", "")
    
    # Enforce admin role
    result = AuthService.login(identifier, password, ip=ip, user_agent=user_agent, required_role='admin')
    status = 200 if result["success"] else 401
    
    if result.get("success") and "student" in result:
        result["role"] = result["student"].get("role", "admin")
        
    return jsonify(result), status

import jwt
import datetime
from BACKEND.config.server_config import Config, CREATOR_PASSWORD

def creator_login():
    """POST /api/auth/creator/login"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    CREATOR_EMAIL = 'gowsicklitheswaran@gmail.com'

    if email != CREATOR_EMAIL:
        return jsonify({
            'success': False,
            'message': 'Creator access denied.'
        }), 403

    # Direct comparison for gowsi2007
    if password != CREATOR_PASSWORD and password != 'gowsi2007':
        return jsonify({
            'success': False,
            'message': 'Invalid password.'
        }), 401

    from BACKEND.models.student_model import StudentModel
    from BACKEND.services.auth_service import AuthService
    from BACKEND.models.session_model import SessionModel
    
    student = StudentModel.find_by_email(email)
    if not student:
        StudentModel.create(
            student_id='CREATOR',
            name='Gowsick M',
            email=email,
            phone='0000000000',
            password_hash=AuthService.hash_password(password),
            department='AI&DS',
            year='Admin Year',
            class_name='Section A',
            role='creator'
        )
        student = StudentModel.find_by_email(email)

    # Update last_login
    from DATABASE.connection.db_connection import execute_insert
    execute_insert("UPDATE students SET last_login = CURRENT_TIMESTAMP WHERE student_id = %s", (student['student_id'],))

    token = SessionModel.create_session(student["student_id"], ip_address=request.remote_addr, user_agent=request.headers.get("User-Agent", ""))

    return jsonify({
        'success': True,
        'token': token,
        'role': 'creator',
        'user': {
            'name': student['name'],
            'email': student['email'],
            'role': 'creator',
            'department': student['department'],
            'section': student['class_name'],
            'student_id': student['student_id']
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
