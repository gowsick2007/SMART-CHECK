import sys
import os
import psycopg2
import psycopg2.extras

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from BACKEND.config.db_config import DATABASE_URL


def get_connection():
    _ensure_database_and_tables()
    conn = psycopg2.connect(
        DATABASE_URL,
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    conn.autocommit = True
    return conn


def _ensure_database_and_tables():
    if hasattr(_ensure_database_and_tables, "initialized") and _ensure_database_and_tables.initialized:
        return

    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
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
                    year VARCHAR(50),
                    class_name VARCHAR(50),
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'student',
                    is_active INTEGER DEFAULT 1,
                    face_enrolled BOOLEAN DEFAULT FALSE,
                    face_descriptor TEXT,
                    fingerprint_template TEXT,
                    fingerprint_credential_id TEXT,
                    fingerprint_public_key TEXT,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS login_sessions (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(50) NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    is_active INTEGER DEFAULT 1,
                    expires_at TIMESTAMP NOT NULL,
                    logout_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    recorded_by_role VARCHAR(20) DEFAULT 'student',
                    marked_by_name VARCHAR(100),
                    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    grace_timer_started_at TIMESTAMP,
                    grace_timer_passed BOOLEAN DEFAULT FALSE,
                    fingerprint_verified BOOLEAN DEFAULT FALSE,
                    face_enabled BOOLEAN DEFAULT TRUE
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
                CREATE TABLE IF NOT EXISTS system_config (
                    setting_key VARCHAR(100) PRIMARY KEY,
                    setting_value VARCHAR(100) NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS year VARCHAR(50);")
            cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'student';")
            cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS is_active INTEGER DEFAULT 1;")
            cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS fingerprint_template TEXT;")
            cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS fingerprint_credential_id TEXT;")
            cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS fingerprint_public_key TEXT;")
            cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;")

            cur.execute("ALTER TABLE login_sessions ADD COLUMN IF NOT EXISTS is_active INTEGER DEFAULT 1;")
            cur.execute("ALTER TABLE login_sessions ADD COLUMN IF NOT EXISTS logout_at TIMESTAMP;")

            cur.execute("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS recorded_by_role VARCHAR(20) DEFAULT 'student';")
            cur.execute("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS marked_by_name VARCHAR(100);")
            cur.execute("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
            cur.execute("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS grace_timer_started_at TIMESTAMP;")
            cur.execute("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS grace_timer_passed BOOLEAN DEFAULT FALSE;")
            cur.execute("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS fingerprint_verified BOOLEAN DEFAULT FALSE;")
            cur.execute("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS face_enabled BOOLEAN DEFAULT TRUE;")

            cur.execute("""
                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'attendance_student_id_date_key') THEN
                        ALTER TABLE attendance DROP CONSTRAINT attendance_student_id_date_key;
                    END IF;

                    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'unique_student_date') THEN
                        ALTER TABLE attendance DROP CONSTRAINT unique_student_date;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'attendance_student_id_date_role_key'
                    ) THEN
                        ALTER TABLE attendance
                        ADD CONSTRAINT attendance_student_id_date_role_key
                        UNIQUE (student_id, date, recorded_by_role);
                    END IF;
                END $$;
            """)

            cur.execute("""
                UPDATE students
                SET role = 'creator'
                WHERE email = 'gowsicklitheswaran@gmail.com';
            """)

        conn.close()
        _ensure_database_and_tables.initialized = True

    except Exception as e:
        print(f"[DB] Error creating tables: {e}")


def execute_query(query: str, params: tuple = (), fetch: str = "all"):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if fetch == "all":
                return cursor.fetchall()
            elif fetch == "one":
                return cursor.fetchone()
            return None
    finally:
        conn.close()


def execute_insert(query: str, params: tuple = ()):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()
            try:
                row = cursor.fetchone()
                if row:
                    if isinstance(row, dict):
                        return list(row.values())[0]
                    return row[0]
            except Exception:
                pass
            return 0
    finally:
        conn.close()