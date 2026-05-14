import sys
import os
sys.path.insert(0, r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE")
from DATABASE.connection.db_connection import execute_query
import math

def test_logic():
    try:
        from CONFIG.college_location_config import COLLEGE_LAT, COLLEGE_LNG, ACTIVE_GEOFENCE_RADIUS
    except:
        COLLEGE_LAT, COLLEGE_LNG, ACTIVE_GEOFENCE_RADIUS = 0,0,22.5
    
    print("Fetching students...")
    students = execute_query(
        "SELECT student_id, name, email, department FROM students WHERE is_active = 1 AND role NOT IN ('creator','admin') ORDER BY name ASC",
        fetch="all") or []
    print(f"Found {len(students)} students.")
    
    print("Fetching logs...")
    logs = execute_query("""
        SELECT DISTINCT ON (student_id)
            student_id, gps_status, latitude, longitude, distance_meters, check_time
        FROM auto_verify_log
        ORDER BY student_id, check_time DESC
    """, fetch="all") or []
    print(f"Found {len(logs)} logs.")

if __name__ == "__main__":
    test_logic()
