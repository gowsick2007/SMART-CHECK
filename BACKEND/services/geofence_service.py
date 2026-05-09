# ============================================================
# geofence_service.py — GPS Geo-Fence Validation
# ============================================================

import math
from CONFIG.college_location_config import COLLEGE_LOCATION, ACTIVE_GEOFENCE_RADIUS
import os
import json
from flask import request

# Dynamically expose the config to the frontend by generating a static JSON file
# that location.js can fetch. This prevents hardcoding the coordinates in JS.
try:
    frontend_config_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "FRONTEND", "js", "college_config.json"
    )
    with open(frontend_config_path, "w") as f:
        json.dump({
            "lat": COLLEGE_LOCATION["latitude"],
            "lon": COLLEGE_LOCATION["longitude"],
            "radius": ACTIVE_GEOFENCE_RADIUS
        }, f)
except Exception as e:
    print(f"[GeofenceService] Failed to write frontend config: {e}")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two GPS points using the
    Haversine formula.

    Returns:
        Distance in metres.
    """
    R = 6371000  # Earth's radius in metres

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
 
calculate_distance = haversine_distance


class GeofenceService:

    COLLEGE_LAT = COLLEGE_LOCATION["latitude"]
    COLLEGE_LON = COLLEGE_LOCATION["longitude"]
    RADIUS = ACTIVE_GEOFENCE_RADIUS

    @classmethod
    def is_within_boundary(cls, student_lat: float, student_lon: float, radius: float = None) -> dict:
        """
        Check whether a student's GPS coordinates are within the college geo-fence.

        Args:
            student_lat : Student's current latitude
            student_lon : Student's current longitude
            radius      : Override radius in metres (optional)

        Returns:
            dict with allowed (bool), distance_m (float), radius_m (float)
        """
        radius = radius or cls.RADIUS
        
        c_lat = cls.COLLEGE_LAT
        c_lon = cls.COLLEGE_LON
        try:
            if request and request.is_json:
                data = request.get_json(silent=True) or {}
                if "college_lat" in data and "college_lon" in data:
                    c_lat = float(data["college_lat"])
                    c_lon = float(data["college_lon"])
        except Exception:
            pass

        distance = haversine_distance(c_lat, c_lon, student_lat, student_lon)

        return {
            "allowed": distance <= radius,
            "distance_m": round(distance, 2),
            "radius_m": radius,
            "college_lat": c_lat,
            "college_lon": c_lon,
        }

    @classmethod
    def validate(cls, lat, lon, radius=None) -> bool:
        """Simple boolean check — returns True if within boundary."""
        return cls.is_within_boundary(lat, lon, radius)["allowed"]
