# ============================================================
# creator_controller.py — Creator Actions (Super Admin)
# ============================================================

from flask import request, jsonify
from DATABASE.connection.db_connection import execute_query, execute_insert
from BACKEND.middleware.auth_middleware import require_role

@require_role(["creator"])
def get_all_users(current_student=None):
    """GET /api/creator/users"""
    query = "SELECT student_id, name, email, role, department, is_active FROM students ORDER BY role DESC, name ASC"
    users = execute_query(query, fetch="all")
    return jsonify({"success": True, "users": users})

@require_role(["creator"])
def update_user_role(current_student=None):
    """POST /api/creator/update-role"""
    data = request.get_json()
    student_id = data.get("student_id")
    new_role = data.get("role") # student or admin
    
    if not student_id or new_role not in ["student", "admin"]:
        return jsonify({"success": False, "message": "Invalid parameters"}), 400
        
    query = "UPDATE students SET role = %s WHERE student_id = %s"
    execute_insert(query, (new_role, student_id))
    
    return jsonify({"success": True, "message": f"User {student_id} updated to {new_role}"})

@require_role(["creator"])
def toggle_user_status(current_student=None):
    """POST /api/creator/toggle-status"""
    data = request.get_json()
    student_id = data.get("student_id")
    is_active = data.get("is_active") # 1 or 0
    
    if student_id == 'CREATOR' or student_id == 'ADMIN':
        return jsonify({"success": False, "message": "Cannot modify internal core accounts."}), 400

    query = "UPDATE students SET is_active = %s WHERE student_id = %s"
    execute_insert(query, (is_active, student_id))
    
    status_text = "activated" if is_active == 1 else "deactivated"
    return jsonify({"success": True, "message": f"User {student_id} has been {status_text}."})

@require_role(["creator"])
def delete_user(current_student=None):
    """POST /api/creator/delete-user"""
    data = request.get_json()
    student_id = data.get("student_id")
    
    if student_id == 'CREATOR':
        return jsonify({"success": False, "message": "Cannot delete core Creator account."}), 400
        
    # Cleanly remove attendance logs and student record safely
    execute_insert("DELETE FROM auto_verify_log WHERE student_id = %s", (student_id,))
    execute_insert("DELETE FROM attendance WHERE student_id = %s", (student_id,))
    execute_insert("DELETE FROM students WHERE student_id = %s", (student_id,))
    
    return jsonify({"success": True, "message": f"User {student_id} deleted successfully."})
