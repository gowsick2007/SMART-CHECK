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
                (student_id, name, email, phone, password_hash, department, year, class_name, role, is_active)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            RETURNING id
        """
        return execute_insert(
            query,
            (student_id, name, email, phone, password_hash, department, year, class_name, role)
        )

    @staticmethod
    def find_by_student_id(student_id):
        """Fetch student by their student_id (case-insensitive)."""
        print(f"[DB] Searching for student_id: {student_id}")
        query = "SELECT * FROM students WHERE LOWER(student_id) = LOWER(%s) AND (is_active = 1 OR is_active IS NULL)"
        res = execute_query(query, (student_id,), fetch="one")
        if not res:
            print(f"[DB] No student found for id: {student_id}")
        return res

    @staticmethod
    def find_by_email(email):
        """Fetch student by email address (case-insensitive)."""
        print(f"[DB] Searching for email: {email}")
        query = "SELECT * FROM students WHERE LOWER(email) = LOWER(%s) AND (is_active = 1 OR is_active IS NULL)"
        res = execute_query(query, (email,), fetch="one")
        if not res:
            print(f"[DB] No student found for email: {email}")
        return res

    @staticmethod
    def find_by_id(student_db_id):
        """Fetch student by primary key id."""
        query = "SELECT * FROM students WHERE id = %s AND (is_active = 1 OR is_active IS NULL)"
        return execute_query(query, (student_db_id,), fetch="one")

    @staticmethod
    def get_all(department=None, class_name=None):
        """Fetch all active students, optionally filtered."""
        base = "SELECT * FROM students WHERE (is_active = 1 OR is_active IS NULL) AND LOWER(role) = 'student'"
        if department and class_name:
            query = base + " AND department = %s AND class_name = %s"
            return execute_query(query, (department, class_name), fetch="all")
        elif department:
            query = base + " AND department = %s"
            return execute_query(query, (department,), fetch="all")
        else:
            return execute_query(base, fetch="all")

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
    def exists(student_id=None, email=None, phone=None):
        """Check if a student already exists by student_id, email, or phone."""
        if student_id:
            res = execute_query("SELECT id FROM students WHERE LOWER(student_id) = LOWER(%s)", (student_id,), fetch="one")
            return res is not None
        if email:
            res = execute_query("SELECT id FROM students WHERE LOWER(email) = LOWER(%s)", (email,), fetch="one")
            return res is not None
        if phone:
            res = execute_query("SELECT id FROM students WHERE phone = %s", (phone,), fetch="one")
            return res is not None
        return False
