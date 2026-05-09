from flask import Blueprint
from BACKEND.controllers.auto_verify_controller import auto_verify_check, get_auto_verify_history

auto_verify_bp = Blueprint("auto_verify", __name__, url_prefix="/api/auto-verify")

auto_verify_bp.route("/check", methods=["POST"])(auto_verify_check)
auto_verify_bp.route("/history", methods=["GET"])(get_auto_verify_history)
