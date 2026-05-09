# ============================================================
# session_model.py — Login Session Model
# ============================================================

import uuid
from datetime import datetime, timedelta
from DATABASE.connection.db_connection import execute_query, execute_insert


SESSION_EXPIRY_HOURS = 8


class SessionModel:
    TABLE = "login_sessions"

    @staticmethod
    def create_session(student_id, ip_address=None, user_agent=None):
        """Create a new session token for a student."""
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)

        query = """
            INSERT INTO login_sessions (student_id, session_token, ip_address, user_agent, expires_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        execute_insert(query, (student_id, token, ip_address, user_agent, expires_at))
        return token

    @staticmethod
    def get_session(token):
        """Retrieve a valid, active session by token."""
        query = """
            SELECT * FROM login_sessions
            WHERE session_token = %s
              AND is_active = 1
              AND expires_at > NOW()
        """
        return execute_query(query, (token,), fetch="one")

    @staticmethod
    def invalidate_session(token):
        """Mark a session as logged out."""
        query = """
            UPDATE login_sessions
            SET is_active = 0, logout_at = NOW()
            WHERE session_token = %s
        """
        execute_insert(query, (token,))

    @staticmethod
    def invalidate_all_sessions(student_id):
        """Invalidate all active sessions for a student (logout everywhere)."""
        query = """
            UPDATE login_sessions
            SET is_active = 0, logout_at = NOW()
            WHERE student_id = %s AND is_active = 1
        """
        execute_insert(query, (student_id,))

    @staticmethod
    def is_valid(token):
        """Check if a session token is still valid."""
        return SessionModel.get_session(token) is not None
