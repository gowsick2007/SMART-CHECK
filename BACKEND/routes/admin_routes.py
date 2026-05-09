from flask import Blueprint
from BACKEND.controllers.admin_controller import admin_login, get_all_students, get_boundary_status, get_today_summary

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

admin_bp.route("/login", methods=["POST"])(admin_login)
admin_bp.route("/all-students-old", methods=["GET"])(get_all_students)
admin_bp.route("/boundary-status", methods=["GET"])(get_boundary_status)
admin_bp.route("/today-summary", methods=["GET"])(get_today_summary)


@admin_bp.route('/boundary-check', methods=['GET'])
def boundary_check():
    from flask import request, jsonify
    from BACKEND.controllers.admin_controller import get_boundary_status_check
    student_id = request.args.get('student_id', '')
    result = get_boundary_status_check(student_id)
    return jsonify(result)


@admin_bp.route('/all-students', methods=['GET'])
def all_students():
    from flask import request, jsonify
    from BACKEND.controllers.admin_controller import get_all_students_list
    result = get_all_students_list()
    return jsonify(result)

