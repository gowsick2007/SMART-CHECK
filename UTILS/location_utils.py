# ============================================================
# location_utils.py — GPS/Location Utility Helpers
# ============================================================

from GPS_LOCATION_MODULE.geo_distance_calculator import haversine_distance, get_bearing
from CONFIG.college_location_config import COLLEGE_LOCATION


def get_distance_to_college(student_lat: float, student_lon: float) -> float:
    """Returns the straight-line distance from student to college in metres."""
    return haversine_distance(
        COLLEGE_LOCATION["latitude"], COLLEGE_LOCATION["longitude"],
        student_lat, student_lon
    )


def get_direction_to_college(student_lat: float, student_lon: float) -> dict:
    """Returns bearing and cardinal direction from student to college."""
    bearing = get_bearing(student_lat, student_lon,
                          COLLEGE_LOCATION["latitude"], COLLEGE_LOCATION["longitude"])

    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(bearing / 45) % 8
    cardinal = directions[index]

    return {
        "bearing_degrees": bearing,
        "direction": cardinal,
        "college_name": COLLEGE_LOCATION["name"],
    }


def format_coordinates(lat: float, lon: float) -> str:
    """Format coordinates as a readable string."""
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    return f"{abs(lat):.4f}°{lat_dir}, {abs(lon):.4f}°{lon_dir}"
