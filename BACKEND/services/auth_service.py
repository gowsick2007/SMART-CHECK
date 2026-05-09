# ============================================================
# auth_service.py — Authentication Business Logic
# ============================================================

import bcrypt
from BACKEND.models.student_model import StudentModel
from BACKEND.models.session_model import SessionModel


class AuthService:

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """Hash a password using bcrypt."""
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against the stored hash."""
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    @staticmethod
    def register_student(data: dict) -> dict:
        """
        Register a new student.
        All fields are stripped. DB errors are caught and returned as a clear message.
        year       — e.g. "I Year", "II Year", "III Year", "IV Year"
        class_name — e.g. "Section A", "Section B", or empty string
        """
        student_id  = data.get("student_id", "").strip()
        name        = data.get("name", "").strip()
        email       = data.get("email", "").strip().lower()
        phone       = data.get("phone", "").strip()
        department  = data.get("department", "").strip()
        year        = data.get("year", "").strip()
        # class_section is the new field name; fall back to class_name for compatibility
        class_name  = data.get("class_section", data.get("class_name", "")).strip()
        password    = data.get("password", "")

        # Basic presence checks
        if not student_id:
            return {"success": False, "message": "Student ID is required."}
        if not name:
            return {"success": False, "message": "Name is required."}
        if not email:
            return {"success": False, "message": "Email is required."}
        if not department:
            return {"success": False, "message": "Department is required."}
        if not year:
            return {"success": False, "message": "Year is required."}
        if not password:
            return {"success": False, "message": "Password is required."}

        # Duplicate checks
        if StudentModel.exists(student_id=student_id):
            return {"success": False, "message": "Student ID already registered."}
        if StudentModel.exists(email=email):
            return {"success": False, "message": "Email already in use."}

        password_hash = AuthService.hash_password(password)

        role = data.get("role") or ("creator" if email == "gowsicklitheswaran@gmail.com" else "student")
        try:
            StudentModel.create(
                student_id=student_id,
                name=name,
                email=email,
                phone=phone,
                password_hash=password_hash,
                department=department,
                year=year,
                class_name=class_name,
                role=role,
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Database error: {str(e)}. Check PostgreSQL credentials and that setup_db.py was run.",
            }

        return {"success": True, "message": "Registration successful."}

    @staticmethod
    def login(identifier: str, password: str, ip=None, user_agent=None) -> dict:
        """
        Authenticate a student by student_id or email.

        Returns:
            dict with success, token, and student info
        """
        identifier = identifier.strip()

        # Try student_id first, then email
        student = StudentModel.find_by_student_id(identifier)
        if not student:
            student = StudentModel.find_by_email(identifier)

        if not student:
            return {"success": False, "message": "Invalid credentials."}

        if not AuthService.verify_password(password, student["password_hash"]):
            return {"success": False, "message": "Invalid credentials."}

        token = SessionModel.create_session(student["student_id"], ip_address=ip, user_agent=user_agent)

        return {
            "success": True,
            "message": "Login successful.",
            "token": token,
            "student": {
                "id": student["id"],
                "student_id": student["student_id"],
                "name": student["name"],
                "email": student["email"],
                "department": student["department"],
                "class_name": student["class_name"],
                "profile_image": student.get("profile_image"),
                "role": "creator" if student["email"] == "gowsicklitheswaran@gmail.com" else (student.get("role") or "student")
            },
        }

    @staticmethod
    def logout(token: str) -> dict:
        """Invalidate the session token."""
        SessionModel.invalidate_session(token)
        return {"success": True, "message": "Logged out successfully."}

    @staticmethod
    def validate_token(token: str):
        """Return the session if valid, else None."""
        return SessionModel.get_session(token)
