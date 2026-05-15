# # ============================================================
# # db_config.py — PostgreSQL Database Configuration
# # ============================================================

# import os
# from dotenv import load_dotenv

# # Load environment variables from .env file (if it exists)S
# load_dotenv()


# import os
# import psycopg2

# DATABASE_URL = os.getenv("DATABASE_URL")

# conn = psycopg2.connect(DATABASE_URL)
# cursor = conn.cursor()

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False