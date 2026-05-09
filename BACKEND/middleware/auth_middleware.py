# ============================================================
# auth_middleware.py — Session Authentication Middleware
# ============================================================

from functools import wraps
from flask import request, jsonify
from BACKEND.models.session_model import SessionModel
from BACKEND.models.student_model import StudentModel


def require_auth(f):
    """
    Decorator to protect routes that require a valid session.
    Reads the 'Authorization: Bearer <token>' header.
    Injects 'current_student' dict into the wrapped function via kwargs.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Authentication required."}), 401

        token = auth_header.split(" ", 1)[1].strip()
        session = SessionModel.get_session(token)

        if not session:
            return jsonify({"success": False, "message": "Session expired or invalid. Please log in again."}), 401

        student = StudentModel.find_by_student_id(session["student_id"])
        if not student:
            return jsonify({"success": False, "message": "Student account not found."}), 401

        kwargs["current_student"] = student
        return f(*args, **kwargs)

    return decorated_function


def require_role(roles):
    """
    Decorator to protect routes based on roles.
    Expects a single role string or a list/tuple of allowed roles.
    """
    if isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"success": False, "message": "Authentication required."}), 401

            token = auth_header.split(" ", 1)[1].strip()
            session = SessionModel.get_session(token)

            if not session:
                return jsonify({"success": False, "message": "Session expired or invalid. Please log in again."}), 401

            student = StudentModel.find_by_student_id(session["student_id"])
            if not student:
                return jsonify({"success": False, "message": "Student account not found."}), 401

            role = student.get("role") or ("creator" if student["email"] == "gowsicklitheswaran@gmail.com" else "student")
            if role not in roles:
                return jsonify({"success": False, "message": f"Unauthorized access. Required role: {', '.join(roles)}"}), 403

            kwargs["current_student"] = student
            return f(*args, **kwargs)

        return decorated_function
    return decorator
