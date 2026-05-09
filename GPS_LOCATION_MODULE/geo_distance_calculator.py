# ============================================================
# geo_distance_calculator.py — Haversine Distance Engine
# ============================================================

import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the shortest great-circle distance between two GPS coordinates
    using the Haversine formula.

    Args:
        lat1, lon1 : Start point (e.g., college) in decimal degrees
        lat2, lon2 : End point (e.g., student) in decimal degrees

    Returns:
        Distance in metres (float)

    Example:
        dist = haversine_distance(13.0827, 80.2707, 13.0830, 80.2710)
        # Returns approx 37.5 metres
    """
    R = 6_371_000  # Earth's mean radius in metres

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2.0) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 3)


def metres_to_km(metres: float) -> float:
    """Convert metres to kilometres."""
    return round(metres / 1000.0, 4)


def get_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the initial bearing from point 1 to point 2 (in degrees).
    Useful for showing direction to college.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    x = math.sin(delta_lambda) * math.cos(phi2)
    y = (math.cos(phi1) * math.sin(phi2) -
         math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda))

    theta = math.atan2(x, y)
    bearing = (math.degrees(theta) + 360) % 360
    return round(bearing, 2)
