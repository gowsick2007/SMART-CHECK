# ============================================================
# student_model.py — Student Data Model
# ============================================================

from DATABASE.connection.db_connection import execute_query, execute_insert


class StudentModel:
    TABLE = "students"

    @staticmethod
    def create(student_id, name, email, phone, password_hash, department, year, class_name, role="student"):
        """Insert a new student record with separate year and class_name columns."""
        query = """
            INSERT INTO students
                (student_id, name, email, phone, password_hash, department, year, class_name, role)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        return execute_insert(
            query,
            (student_id, name, email, phone, password_hash, department, year, class_name, role)
        )

    @staticmethod
    def find_by_student_id(student_id):
        """Fetch student by their student_id."""
        query = "SELECT * FROM students WHERE student_id = %s AND is_active = 1"
        return execute_query(query, (student_id,), fetch="one")

    @staticmethod
    def find_by_email(email):
        """Fetch student by email address."""
        query = "SELECT * FROM students WHERE email = %s AND is_active = 1"
        return execute_query(query, (email,), fetch="one")

    @staticmethod
    def find_by_id(student_db_id):
        """Fetch student by primary key id."""
        query = "SELECT * FROM students WHERE id = %s AND is_active = 1"
        return execute_query(query, (student_db_id,), fetch="one")

    @staticmethod
    def get_all(department=None, class_name=None):
        """Fetch all active students, optionally filtered."""
        if department and class_name:
            query = "SELECT * FROM students WHERE department = %s AND class_name = %s AND is_active = 1"
            return execute_query(query, (department, class_name), fetch="all")
        elif department:
            query = "SELECT * FROM students WHERE department = %s AND is_active = 1"
            return execute_query(query, (department,), fetch="all")
        else:
            return execute_query("SELECT * FROM students WHERE is_active = 1", fetch="all")

    @staticmethod
    def update_profile_image(student_id, image_path):
        """Update the profile image path."""
        query = "UPDATE students SET profile_image = %s WHERE student_id = %s"
        execute_insert(query, (image_path, student_id))

    @staticmethod
    def deactivate(student_id):
        """Soft-delete a student (set is_active = 0)."""
        query = "UPDATE students SET is_active = 0 WHERE student_id = %s"
        execute_insert(query, (student_id,))

    @staticmethod
    def exists(student_id=None, email=None):
        """Check if a student already exists by student_id or email."""
        if student_id:
            res = execute_query("SELECT id FROM students WHERE student_id = %s", (student_id,), fetch="one")
            return res is not None
        if email:
            res = execute_query("SELECT id FROM students WHERE email = %s", (email,), fetch="one")
            return res is not None
        return False
