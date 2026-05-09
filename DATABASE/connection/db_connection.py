# ============================================================
# db_connection.py — PostgreSQL Connection (psycopg2)
# ============================================================

import sys
import os
import psycopg2
import psycopg2.extras

# Ensure project root is in path for imports
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from BACKEND.config.db_config import DB_CONFIG


def get_connection():
    """
    Returns a new psycopg2 connection using the configured DB settings.
    Automatically creates the database and required tables if they do not exist.
    """
    _ensure_database_and_tables()
    try:
        # First attempt to connect to the target database directly
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname=DB_CONFIG["database"],
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        conn.autocommit = True
        return conn

    except psycopg2.OperationalError as e:
        err_msg = str(e).lower()

        # If database does not exist → create it then reconnect
        if "does not exist" in err_msg or "invalid catalog" in err_msg:
            try:
                admin_conn = psycopg2.connect(
                    host=DB_CONFIG["host"],
                    port=DB_CONFIG["port"],
                    user=DB_CONFIG["user"],
                    password=DB_CONFIG["password"],
                    dbname="postgres",  # connect to default admin DB
                )
                admin_conn.autocommit = True
                with admin_conn.cursor() as cur:
                    db_name = DB_CONFIG["database"]
                    cur.execute(
                        f"SELECT 1 FROM pg_database WHERE datname = %s", (db_name,)
                    )
                    if not cur.fetchone():
                        cur.execute(f'CREATE DATABASE "{db_name}"')
                admin_conn.close()

                # Reconnect to the newly created database
                conn = psycopg2.connect(
                    host=DB_CONFIG["host"],
                    port=DB_CONFIG["port"],
                    user=DB_CONFIG["user"],
                    password=DB_CONFIG["password"],
                    dbname=DB_CONFIG["database"],
                    cursor_factory=psycopg2.extras.RealDictCursor,
                )
                conn.autocommit = True
                return conn

            except Exception as inner_e:
                raise RuntimeError(
                    f"\n{'='*60}\n"
                    f"[DATABASE ERROR]\n"
                    f"Could not create database '{DB_CONFIG['database']}'.\n"
                    f"Detail: {inner_e}\n"
                    f"{'='*60}\n"
                ) from inner_e

        elif "password authentication" in err_msg or "authentication failed" in err_msg:
            raise RuntimeError(
                f"\n{'='*60}\n"
                f"[DATABASE AUTHENTICATION ERROR]\n"
                f"PostgreSQL rejected the login for user '{DB_CONFIG['user']}'.\n\n"
                f"ACTION REQUIRED:\n"
                f"1. Open: BACKEND/config/db_config.py\n"
                f"2. Set the correct password for your PostgreSQL user.\n"
                f"   (Currently set to: '{DB_CONFIG['password']}')\n"
                f"{'='*60}\n"
            ) from e

        elif "connection refused" in err_msg or "could not connect" in err_msg:
            raise RuntimeError(
                f"\n{'='*60}\n"
                f"[DATABASE CONNECTION ERROR]\n"
                f"Cannot reach PostgreSQL server at {DB_CONFIG['host']}:{DB_CONFIG['port']}.\n\n"
                f"ACTION REQUIRED:\n"
                f"1. Ensure PostgreSQL is running.\n"
                f"2. Check that port {DB_CONFIG['port']} is correct.\n"
                f"{'='*60}\n"
            ) from e

        else:
            raise RuntimeError(f"[DB] Cannot connect to PostgreSQL: {e}") from e


def _ensure_database_and_tables():
    """Ensure database and tables exist."""
    # Check if we already initialized to avoid overhead on every query
    if hasattr(_ensure_database_and_tables, "initialized") and _ensure_database_and_tables.initialized:
        return

    # First, try to create the database if missing
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"], port=DB_CONFIG["port"],
            user=DB_CONFIG["user"], password=DB_CONFIG["password"],
            dbname=DB_CONFIG["database"]
        )
        conn.close()
    except psycopg2.OperationalError as e:
        err_msg = str(e).lower()
        if "does not exist" in err_msg or "invalid catalog" in err_msg:
            try:
                admin_conn = psycopg2.connect(
                    host=DB_CONFIG["host"], port=DB_CONFIG["port"],
                    user=DB_CONFIG["user"], password=DB_CONFIG["password"],
                    dbname="postgres"
                )
                admin_conn.autocommit = True
                with admin_conn.cursor() as cur:
                    db_name = DB_CONFIG["database"]
                    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                    if not cur.fetchone():
                        cur.execute(f'CREATE DATABASE "{db_name}"')
                admin_conn.close()
            except Exception as inner_e:
                pass

    # Now create tables if missing
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"], port=DB_CONFIG["port"],
            user=DB_CONFIG["user"], password=DB_CONFIG["password"],
            dbname=DB_CONFIG["database"]
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    phone VARCHAR(20),
                    department VARCHAR(100),
                    class_name VARCHAR(50),
                    password_hash VARCHAR(255) NOT NULL,
                    face_enrolled BOOLEAN DEFAULT FALSE,
                    face_descriptor TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    token VARCHAR(255) UNIQUE NOT NULL,
                    student_id VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(50) NOT NULL,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    location_valid BOOLEAN,
                    face_match_status VARCHAR(20),
                    face_confidence DOUBLE PRECISION,
                    remarks TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS auto_verify_log (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(50),
                    check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    gps_status VARCHAR(20),
                    face_status VARCHAR(20),
                    final_status VARCHAR(20),
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    distance_meters DOUBLE PRECISION
                );
            """)
            cur.execute("""
                ALTER TABLE auto_verify_log ADD COLUMN IF NOT EXISTS distance_meters DOUBLE PRECISION;
            """)
            cur.execute("""
                ALTER TABLE auto_verify_log ADD COLUMN IF NOT EXISTS final_status VARCHAR(20);
            """)
            cur.execute("""
                ALTER TABLE students ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'student';
            """)
            cur.execute("""
                ALTER TABLE attendance ADD COLUMN IF NOT EXISTS recorded_by_role VARCHAR(20) DEFAULT 'student';
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS boundary_config (
                    id SERIAL PRIMARY KEY,
                    boundary_name VARCHAR(255),
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS boundary_locations (
                    id SERIAL PRIMARY KEY,
                    boundary_name VARCHAR(255),
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                UPDATE students SET role = 'creator' WHERE email = 'gowsicklitheswaran@gmail.com';
            """)
        conn.close()
        _ensure_database_and_tables.initialized = True
    except Exception as e:
        print(f"[DB] Error creating tables: {e}")


def execute_query(query: str, params: tuple = (), fetch: str = "all"):
    """
    Execute a SELECT query and return results.

    Args:
        query  : SQL query string (use %s for parameters)
        params : Tuple of parameters (parameterized, safe against SQL injection)
        fetch  : 'all' = list of dicts | 'one' = single dict | 'none' = None

    Returns:
        Result rows or None
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if fetch == "all":
                return cursor.fetchall()
            elif fetch == "one":
                return cursor.fetchone()
            else:
                return None
    finally:
        conn.close()


def execute_insert(query: str, params: tuple = ()):
    """
    Execute an INSERT / UPDATE / DELETE and return lastrowid (via RETURNING id).
    For PostgreSQL, INSERT must use RETURNING id to get the inserted row ID.

    Returns:
        lastrowid (int) for INSERT with RETURNING, or 0 otherwise
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()
            try:
                row = cursor.fetchone()
                if row:
                    # Support both dict-style and index-style results
                    if isinstance(row, dict):
                        return list(row.values())[0]
                    return row[0]
            except Exception:
                pass
            return 0
    finally:
        conn.close()
