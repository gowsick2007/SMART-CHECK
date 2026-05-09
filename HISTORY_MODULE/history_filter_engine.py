# ============================================================
# history_filter_engine.py — History Filtering & Search
# ============================================================

from BACKEND.models.attendance_model import AttendanceModel


class HistoryFilterEngine:
    """
    Provides flexible filtering of attendance records for the history page.
    """

    @staticmethod
    def filter(student_id: str, status: str = None, start_date: str = None,
               end_date: str = None, limit: int = 50) -> list:
        """
        Filter attendance records with optional status and date range filters.

        Args:
            student_id : The student's ID
            status     : 'present', 'absent', 'late', or None (all)
            start_date : 'YYYY-MM-DD' start date (optional)
            end_date   : 'YYYY-MM-DD' end date (optional)
            limit      : Max records to return

        Returns:
            List of filtered attendance record dicts
        """
        if start_date and end_date:
            records = AttendanceModel.filter_by_date_range(student_id, start_date, end_date)
        else:
            records = AttendanceModel.get_by_student(student_id, limit=limit)

        if status and status in ("present", "absent", "late"):
            records = [r for r in records if r["status"] == status]

        return records[:limit]

    @staticmethod
    def search_by_date(student_id: str, date_str: str) -> dict:
        """Fetch a specific day's attendance record."""
        return AttendanceModel.get_by_student_and_date(student_id, date_str)

    @staticmethod
    def get_streak(student_id: str) -> dict:
        """
        Calculate the current consecutive present/late streak for a student.
        """
        records = AttendanceModel.get_by_student(student_id, limit=365)
        streak = 0
        for record in records:
            if record["status"] in ("present", "late"):
                streak += 1
            else:
                break  # Streak broken
        return {"streak": streak, "unit": "days"}
