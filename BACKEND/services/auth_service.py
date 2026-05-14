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
    def verify_password(plain_password: str, hashed_password) -> bool:
        """Verify a plain password against the stored hash (supports plain text fallback)."""
        try:
            if not hashed_password:
                print("[AUTH DEBUG] Stored hash is empty")
                return False
                
            # If stored password is NOT a bcrypt hash (doesn't start with $), compare directly
            if isinstance(hashed_password, str) and not hashed_password.startswith('$'):
                print("[AUTH DEBUG] Non-bcrypt hash detected, using plain comparison")
                return plain_password == hashed_password
            
            # Strip potential whitespace/padding from DB
            if isinstance(hashed_password, str):
                hashed_password = hashed_password.strip().encode('utf-8')
            elif isinstance(hashed_password, bytes):
                hashed_password = hashed_password.strip()
            
            plain_bytes = plain_password.encode('utf-8')
            
            # Bcrypt comparison
            result = bcrypt.checkpw(plain_bytes, hashed_password)
            print(f"[AUTH DEBUG] Bcrypt check result: {'SUCCESS' if result else 'FAILED'}")
            return result
        except Exception as e:
            print(f"[AUTH DEBUG] ERROR during verification: {e}")
            # Final fallback: maybe it was stored as plain text but checkpw failed
            return plain_password == str(hashed_password)

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
        class_name  = data.get("class_section", data.get("class_name", "")).strip()
        password    = data.get("password", "")

        print(f"[REGISTRATION] Attempting to register student: {student_id} ({email})")

        # Basic presence checks
        if not student_id: return {"success": False, "message": "Student ID is required."}
        if not name: return {"success": False, "message": "Name is required."}
        if not email: return {"success": False, "message": "Email is required."}
        if not password: return {"success": False, "message": "Password is required."}

        # Duplicate checks (Student ID, Email, or Phone)
        if StudentModel.exists(student_id=student_id) or StudentModel.exists(email=email) or (phone and StudentModel.exists(phone=phone)):
            print(f"[REGISTRATION] Failed: Account duplicate found for ID {student_id}, Email {email}, or Phone {phone}")
            return {"success": False, "message": "Account already exists. Please login."}

        password_hash = AuthService.hash_password(password)
        role = data.get("role") or ("creator" if email == "gowsicklitheswaran@gmail.com" else "student")

        try:
            new_id = StudentModel.create(
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
            print(f"[REGISTRATION] Success! New Student DB ID: {new_id}")
        except Exception as e:
            print(f"[REGISTRATION] CRITICAL DATABASE ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Database error: {str(e)}"}

        return {"success": True, "message": "Registration successful."}

    @staticmethod
    def login(identifier: str, password: str, ip=None, user_agent=None, required_role=None) -> dict:
        """
        Authenticate a student by student_id or email with optional role enforcement.
        """
        identifier = identifier.strip().lower()
        print("LOGIN EMAIL:", identifier)

        # Try student_id first, then email (lowercased)
        student = StudentModel.find_by_student_id(identifier)
        lookup_method = "student_id"
        
        if not student:
            print(f"[LOGIN DEBUG] Student ID lookup failed, trying email...")
            student = StudentModel.find_by_email(identifier)
            lookup_method = "email"

        if not student:
            print(f"[LOGIN DEBUG] No student found via {lookup_method}")
            return {"success": False, "message": "Account not found. Please create account."}

        print("USER FOUND:", student)

        # Role enforcement before password check for slightly better security/feedback
        user_role = student.get("role") or "student"
        if required_role and user_role != required_role:
            if required_role == 'student':
                return {"success": False, "message": "Invalid student credentials"}
            elif required_role == 'admin':
                return {"success": False, "message": "Invalid admin credentials"}
            else:
                return {"success": False, "message": f"Unauthorized role access."}
        
        # Stored hash preview
        stored_hash = student.get("password_hash", "")
        hash_preview = (stored_hash[:7] + "...") if stored_hash else "EMPTY"
        print(f"[LOGIN DEBUG] Stored hash preview: {hash_preview}")

        # Verify password
        if not AuthService.verify_password(password, stored_hash):
            return {"success": False, "message": "Invalid credentials."}

        print(f"[LOGIN DEBUG] Login SUCCESS for {student['student_id']}")
        
        # Update last_login
        from DATABASE.connection.db_connection import execute_insert
        execute_insert("UPDATE students SET last_login = CURRENT_TIMESTAMP WHERE student_id = %s", (student['student_id'],))
        
        token = SessionModel.create_session(student["student_id"], ip_address=ip, user_agent=user_agent)

        student_data = {
            "id": student["id"],
            "student_id": student["student_id"],
            "name": student["name"],
            "email": student["email"],
            "department": student.get("department"),
            "class_name": student.get("class_name"),
            "profile_image": student.get("profile_image"),
            "role": user_role
        }
        
        # Strict enforcement per explicit directive: ensure returned payload has flat role property
        return {
            "success": True,
            "message": "Login successful.",
            "token": token,
            "role": student_data["role"],
            "student": student_data,
            "user": student_data # Alias for compatibility
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
