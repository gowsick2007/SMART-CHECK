# ============================================================
# session_manager.py — Session Utility Helper
# ============================================================

from BACKEND.models.session_model import SessionModel
from BACKEND.models.student_model import StudentModel


class SessionManager:
    """High-level session management helper."""

    @staticmethod
    def get_current_student(token: str):
        """
        Validate a session token and return the corresponding student.

        Returns:
            Student dict or None if invalid/expired
        """
        if not token:
            return None
        session = SessionModel.get_session(token)
        if not session:
            return None
        student = StudentModel.find_by_student_id(session["student_id"])
        return student

    @staticmethod
    def is_authenticated(token: str) -> bool:
        """Returns True if the token corresponds to an active session."""
        return SessionModel.is_valid(token)

    @staticmethod
    def end_session(token: str):
        """Invalidate the given session token."""
        SessionModel.invalidate_session(token)

    @staticmethod
    def end_all_sessions(student_id: str):
        """End all active sessions for a student (logout everywhere)."""
        SessionModel.invalidate_all_sessions(student_id)
