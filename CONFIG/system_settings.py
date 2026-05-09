# ============================================================
# system_settings.py — Global System Settings
# ============================================================

SYSTEM_NAME = "Smart Attendance System"
SYSTEM_VERSION = "1.0.0"

# Attendance marking window (24-hour format)
ATTENDANCE_START_TIME = "08:00"
ATTENDANCE_END_TIME = "22:00"

# Late threshold — after this time, student is marked 'late' instead of 'present'
LATE_THRESHOLD_TIME = "09:30"

# Face recognition match threshold (lower = stricter)
# Typical range: 0.4 (strict) to 0.6 (lenient)
FACE_MATCH_THRESHOLD = 0.5

# Liveness detection
LIVENESS_CHECK_ENABLED = True

# Max failed face attempts before lockout
MAX_FACE_ATTEMPTS = 5

# Allowed departments list
DEPARTMENTS = [
    "Computer Science",
    "AI&DS",
    "IT",
    "ECE",
    "Information Technology",
    "Electronics",
    "Mechanical Engineering",
    "Civil Engineering",
    "Business Administration",
    "Mathematics",
    "Physics",
]

# Allowed class names
CLASS_NAMES = ["I Year", "II Year", "III Year", "IV Year", "Section A", "Section B", "Section C"]
