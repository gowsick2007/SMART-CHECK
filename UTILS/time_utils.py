# ============================================================
# time_utils.py — Time Utility Helpers
# ============================================================

from datetime import datetime, time as dtime
import pytz
from CONFIG.system_settings import (
    ATTENDANCE_START_TIME, ATTENDANCE_END_TIME, LATE_THRESHOLD_TIME
)

IST = pytz.timezone("Asia/Kolkata")


def get_current_date() -> str:
    """Returns today's date as 'YYYY-MM-DD' in IST."""
    return datetime.now(IST).strftime("%Y-%m-%d")


def get_current_time() -> str:
    """Returns current time as 'HH:MM:SS' in IST."""
    return datetime.now(IST).strftime("%H:%M:%S")


def get_current_datetime_ist() -> datetime:
    """Returns current datetime object in IST."""
    return datetime.now(IST)


def is_within_attendance_window() -> bool:
    """
    Returns True if current time is within the allowed attendance window.
    Uses ATTENDANCE_START_TIME and ATTENDANCE_END_TIME from system_settings.
    """
    now = datetime.now(IST).time()
    parts_s = ATTENDANCE_START_TIME.split(":")
    parts_e = ATTENDANCE_END_TIME.split(":")
    start = dtime(int(parts_s[0]), int(parts_s[1]))
    end = dtime(int(parts_e[0]), int(parts_e[1]))
    return start <= now <= end


def get_attendance_status(time_str: str) -> str:
    """
    Determine if a student should be 'present' or 'late' based on time.
    """
    try:
        parts = time_str.split(":")
        current = dtime(int(parts[0]), int(parts[1]))
        late_parts = LATE_THRESHOLD_TIME.split(":")
        late = dtime(int(late_parts[0]), int(late_parts[1]))
        return "late" if current > late else "present"
    except Exception:
        return "present"


def format_datetime_display() -> str:
    """Human-friendly full datetime string."""
    return datetime.now(IST).strftime("%A, %d %B %Y — %I:%M %p IST")
