#!/usr/bin/env python3
"""
setup_db.py — Initialize the PostgreSQL Database
Run this ONCE before starting the application.

Usage:
    python setup_db.py
"""

import sys
import os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
import psycopg2.extras
from BACKEND.config.db_config import DB_CONFIG


def run_sql_file(cursor, filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        sql = f.read()

    # Split by semicolon, skip empty statements
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    for stmt in statements:
        try:
            cursor.execute(stmt)
            print(f"  [OK] Executed: {stmt[:70]}")
        except Exception as e:
            print(f"  [FAIL] {stmt[:70]} --> {e}")


def ensure_database_exists():
    """Connect to the default 'postgres' DB and create our DB if needed."""
    try:
        admin_conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname="postgres",
        )
        admin_conn.autocommit = True
        db_name = DB_CONFIG["database"]
        with admin_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE "{db_name}"')
                print(f"  [OK] Database '{db_name}' created.")
            else:
                print(f"  [OK] Database '{db_name}' already exists.")
        admin_conn.close()
    except Exception as e:
        print(f"\n[ERROR] Could not connect to PostgreSQL server: {e}")
        print("   Check BACKEND/config/db_config.py for correct credentials.")
        sys.exit(1)


def main():
    print("=" * 60)
    print("  Smart Attendance System -- PostgreSQL Database Setup")
    print("=" * 60)

    # Step 1: Ensure the database exists
    ensure_database_exists()

    # Step 2: Connect to the target database and run table SQL files
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname=DB_CONFIG["database"],
        )
        conn.autocommit = True
        print(f"\n[OK] Connected to PostgreSQL database: {DB_CONFIG['database']}")
    except Exception as e:
        print(f"\n[ERROR] Could not connect to database '{DB_CONFIG['database']}': {e}")
        sys.exit(1)

    sql_files = [
        'DATABASE/postgresql/students_table.sql',
        'DATABASE/postgresql/attendance_table.sql',
        'DATABASE/postgresql/face_data_table.sql',
        'DATABASE/postgresql/session_table.sql',
    ]

    with conn.cursor() as cursor:
        for sql_file in sql_files:
            path = os.path.join(os.path.dirname(__file__), sql_file)
            print(f"\n[FILE] Running: {sql_file}")
            run_sql_file(cursor, path)

    conn.close()
    print("\n" + "=" * 60)
    print("  [DONE] PostgreSQL database setup complete!")
    print("  Run the server with:  python BACKEND/app.py")
    print("=" * 60)


if __name__ == '__main__':
    main()
