# ============================================================
# auth_routes.py — Authentication API Routes
# ============================================================

from flask import Blueprint, request, jsonify
from BACKEND.controllers.auth_controller import register, login, logout, validate_token, creator_login

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Register routes
auth_bp.route("/register", methods=["POST"])(register)
auth_bp.route("/login", methods=["POST"])(login)
auth_bp.route("/creator/login", methods=["POST"])(creator_login)
auth_bp.route("/logout", methods=["POST"])(logout)
auth_bp.route("/validate", methods=["GET"])(validate_token)


