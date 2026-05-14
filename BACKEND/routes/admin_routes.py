from flask import Blueprint
from BACKEND.controllers.admin_controller import admin_login, get_all_students, get_today_summary, require_admin

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

admin_bp.route("/login", methods=["POST"])(admin_login)
admin_bp.route("/all-students-old", methods=["GET"])(get_all_students)
admin_bp.route("/today-summary", methods=["GET"])(get_today_summary)


@admin_bp.route('/boundary-check', methods=['GET'])
@require_admin
def boundary_check():
    from flask import request, jsonify
    from BACKEND.controllers.admin_controller import get_boundary_status_check
    student_id = request.args.get('student_id', '')
    result = get_boundary_status_check(student_id)
    return jsonify(result)


@admin_bp.route('/all-students', methods=['GET'])
@require_admin
def all_students():
    from flask import request, jsonify
    from BACKEND.controllers.admin_controller import get_all_students_list
    result = get_all_students_list()
    return jsonify(result)

