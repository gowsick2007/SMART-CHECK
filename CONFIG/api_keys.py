# ============================================================
# api_keys.py — External API Keys & Secrets
# ============================================================

import os

# JWT / Token Secret (also set in server_config)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change_me_in_production_jwt_secret")

# Token expiry in seconds (default: 8 hours)
JWT_EXPIRY_SECONDS = 8 * 60 * 60

# Google Maps API Key (optional — for map display in frontend)
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

# SMTP Email (optional — for password reset)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
