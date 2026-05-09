# ============================================================
# timestamp_generator.py — Timestamp Utilities
# ============================================================

from datetime import datetime
import pytz


IST = pytz.timezone("Asia/Kolkata")


def get_ist_now() -> datetime:
    """Return the current datetime in IST (India Standard Time)."""
    return datetime.now(IST)


def get_current_date_ist() -> str:
    """Return today's date as 'YYYY-MM-DD' in IST."""
    return get_ist_now().strftime("%Y-%m-%d")


def get_current_time_ist() -> str:
    """Return current time as 'HH:MM:SS' in IST."""
    return get_ist_now().strftime("%H:%M:%S")


def get_datetime_display() -> str:
    """Return a human-friendly datetime string."""
    return get_ist_now().strftime("%d %B %Y, %I:%M %p IST")


def format_date(date_str: str) -> str:
    """Convert 'YYYY-MM-DD' to 'DD Mon YYYY'."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except Exception:
        return date_str


def format_time(time_str: str) -> str:
    """Convert 'HH:MM:SS' to '12-hour AM/PM' format."""
    try:
        dt = datetime.strptime(time_str, "%H:%M:%S")
        return dt.strftime("%I:%M %p")
    except Exception:
        return time_str
