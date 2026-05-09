# ============================================================
# geo_fence_validator.py — Geo-Fence Boundary Validator
# ============================================================

from GPS_LOCATION_MODULE.geo_distance_calculator import haversine_distance
from CONFIG.college_location_config import COLLEGE_LOCATION
from CONFIG.radius_config import ATTENDANCE_RADIUS

class GeoFenceValidator:
    """
    Validates whether a GPS coordinate is within the defined geo-fence boundary.
    """

    def __init__(self, center_lat=None, center_lon=None, radius_m=None):
        self.center_lat = center_lat or COLLEGE_LOCATION["latitude"]
        self.center_lon = center_lon or COLLEGE_LOCATION["longitude"]
        self.radius_m = radius_m or ATTENDANCE_RADIUS

    def validate(self, student_lat: float, student_lon: float) -> dict:
        """
        Full validation result.

        Returns:
            dict:
                allowed    : bool — True if within boundary
                distance_m : float — actual distance to college centre
                radius_m   : int — configured fence radius
                message    : str — human-readable result
        """
        distance = haversine_distance(
            self.center_lat, self.center_lon,
            student_lat, student_lon
        )
        allowed = distance <= self.radius_m

        return {
            "allowed": allowed,
            "distance_m": distance,
            "radius_m": self.radius_m,
            "center_lat": self.center_lat,
            "center_lon": self.center_lon,
            "student_lat": student_lat,
            "student_lon": student_lon,
            "message": (
                f"Within boundary ({distance}m of {self.radius_m}m limit)."
                if allowed
                else f"Outside boundary! {distance}m away, limit is {self.radius_m}m."
            ),
        }

    def is_allowed(self, student_lat: float, student_lon: float) -> bool:
        """Quick boolean check."""
        return self.validate(student_lat, student_lon)["allowed"]

    def set_radius(self, radius_m: int):
        """Update the geo-fence radius at runtime."""
        self.radius_m = radius_m
        return self


# Singleton instance (uses college_location_config defaults)
default_validator = GeoFenceValidator()
