# ============================================================
# db_config.py — PostgreSQL Database Configuration
# ============================================================

import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("PG_HOST", "localhost"),
    "port":     int(os.getenv("PG_PORT", 5432)),
    "user":     os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "gowsi"),
    "database": os.getenv("PG_DATABASE", "smart_attendance"),
}

# SQLAlchemy URI (used by Flask-SQLAlchemy if switching)
SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

SQLALCHEMY_TRACK_MODIFICATIONS = False
