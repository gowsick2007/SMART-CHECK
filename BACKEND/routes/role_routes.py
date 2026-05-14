# ============================================================
# admin_routes.py
# ============================================================
from flask import Blueprint
from BACKEND.controllers.admin_controller import get_student_monitoring, mark_attendance

admin_bp = Blueprint("admin_extra", __name__)

admin_bp.route("/api/admin/monitoring", methods=["GET"])(get_student_monitoring)
admin_bp.route("/api/admin/verify-attendance", methods=["POST"])(mark_attendance)

# ============================================================
# creator_routes.py
# ============================================================
from flask import Blueprint
from BACKEND.controllers.creator_controller import get_all_users, update_user_role, toggle_user_status, delete_user

creator_bp = Blueprint("creator_extra", __name__)

creator_bp.route("/api/creator/users", methods=["GET"])(get_all_users)
creator_bp.route("/api/creator/update-role", methods=["POST"])(update_user_role)
creator_bp.route("/api/creator/toggle-status", methods=["POST"])(toggle_user_status)
creator_bp.route("/api/creator/delete-user", methods=["POST"])(delete_user)
creator_bp.route("/api/creator/remove-user", methods=["POST"])(delete_user)
