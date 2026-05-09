# ============================================================
# attendance_logger.py — Attendance History Logging
# ============================================================

from BACKEND.models.attendance_model import AttendanceModel
from ATTENDANCE_MODULE.timestamp_generator import format_date, format_time


class AttendanceLogger:
    """
    Provides structured logging and retrieval of attendance history.
    """

    @staticmethod
    def log_event(student_id: str, status: str, latitude: float, longitude: float,
                  face_match_status: str, face_confidence: float = None, remarks: str = None) -> int:
        """
        Manually log an attendance event.

        Returns:
            New record ID
        """
        from UTILS.time_utils import get_current_date, get_current_time
        today = get_current_date()
        now = get_current_time()

        return AttendanceModel.create(
            student_id=student_id,
            date=today,
            time=now,
            status=status,
            latitude=latitude,
            longitude=longitude,
            location_valid=(latitude is not None and longitude is not None),
            face_match_status=face_match_status,
            face_confidence=face_confidence,
            remarks=remarks,
        )

    @staticmethod
    def get_history(student_id: str, limit: int = 30) -> list:
        """
        Retrieve attendance history with human-friendly formatting.
        """
        records = AttendanceModel.get_by_student(student_id, limit=limit)
        for r in records:
            r["date_display"] = format_date(str(r["date"]))
            r["time_display"] = format_time(str(r["time"]))
        return records

    @staticmethod
    def get_monthly_summary(student_id: str, year: int, month: int) -> dict:
        """
        Summarize attendance for a specific month.
        """
        import calendar
        start = f"{year:04d}-{month:02d}-01"
        last_day = calendar.monthrange(year, month)[1]
        end = f"{year:04d}-{month:02d}-{last_day:02d}"

        records = AttendanceModel.filter_by_date_range(student_id, start, end)
        present = sum(1 for r in records if r["status"] == "present")
        late = sum(1 for r in records if r["status"] == "late")
        absent = sum(1 for r in records if r["status"] == "absent")
        total_days = last_day

        return {
            "student_id": student_id,
            "month": f"{calendar.month_name[month]} {year}",
            "total_working_days": total_days,
            "present": present,
            "late": late,
            "absent": absent,
            "attendance_percentage": round((present + late) / max(total_days, 1) * 100, 2),
        }
