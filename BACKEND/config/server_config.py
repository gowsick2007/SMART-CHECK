# ============================================================
# server_config.py — Flask Server Configuration
# ============================================================

import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "smart_attendance_super_secret_key_2024")
    DEBUG = True
    TESTING = False
    HOST = "0.0.0.0"
    PORT = 5000

    # Upload folder for face images
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads", "faces")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

    # CORS
    CORS_ORIGINS = ["http://localhost:5500", "http://127.0.0.1:5500"]

    # Session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "change_this_in_production!")


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
