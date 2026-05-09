# ============================================================
# radius_config.py — Geofence Radius Settings
# ============================================================

# Attendance strictly within this radius
ATTENDANCE_RADIUS = 22.5

# Minimum allowed radius (metres)
MIN_RADIUS = 20

# Maximum allowed radius (metres)
MAX_RADIUS = 1000

# Default radius used if not configured (metres)
DEFAULT_RADIUS = 22.5

# Radius presets (displayed in frontend dropdown)
RADIUS_PRESETS = {
    "Strict (22.5m)": 22.5,
    "Standard (200m)": 200,
    "Wide (500m)": 500,
}
