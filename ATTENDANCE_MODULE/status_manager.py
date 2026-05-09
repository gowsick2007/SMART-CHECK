# ============================================================
# status_manager.py — Attendance Status Determination
# ============================================================

from datetime import datetime, time as dtime
from CONFIG.system_settings import LATE_THRESHOLD_TIME, ATTENDANCE_START_TIME, ATTENDANCE_END_TIME


def parse_time(time_str: str) -> dtime:
    """Parse 'HH:MM' string into a time object."""
    h, m = map(int, time_str.split(":"))
    return dtime(h, m)


def determine_status(current_time_str: str) -> str:
    """
    Determine if a student should be marked 'present' or 'late'
    based on the current time.

    Args:
        current_time_str: 'HH:MM:SS' or 'HH:MM' string

    Returns:
        'present', 'late', or 'absent'
    """
    try:
        parts = current_time_str.split(":")
        current = dtime(int(parts[0]), int(parts[1]))
        late_threshold = parse_time(LATE_THRESHOLD_TIME)
        end_time = parse_time(ATTENDANCE_END_TIME)

        if current > end_time:
            return "absent"
        elif current > late_threshold:
            return "late"
        else:
            return "present"
    except Exception:
        return "present"


def is_already_marked(student_id: str, date_str: str) -> bool:
    """Check if attendance was already recorded for a student today."""
    from BACKEND.models.attendance_model import AttendanceModel
    record = AttendanceModel.get_by_student_and_date(student_id, date_str)
    return record is not None
