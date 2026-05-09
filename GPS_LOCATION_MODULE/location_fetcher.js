# ============================================================
# location_fetcher.js  (GPS_LOCATION_MODULE)
# This is the SERVER-SIDE companion logic description.
# The actual browser-side fetching is in FRONTEND/js/location.js
# This file re-exports the Python-usable geo utilities.
# ============================================================

# NOTE: This file is a stub placeholder for the GPS location module.
# Browser-side GPS fetching is handled in FRONTEND/js/location.js
# Backend validation is handled by geo_fence_validator.py

"""
GPS Location Module — Python Backend Side

This module provides:
  1. A description of how the browser fetches GPS
  2. The Python-side distance calculator and geo-fence validator
"""

# Re-export for convenience
from GPS_LOCATION_MODULE.geo_distance_calculator import haversine_distance
from GPS_LOCATION_MODULE.geo_fence_validator import GeoFenceValidator

__all__ = ["haversine_distance", "GeoFenceValidator"]
