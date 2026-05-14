# ============================================================
# attendance_model.py — Attendance Record Model
# ============================================================

from DATABASE.connection.db_connection import execute_query, execute_insert


class AttendanceModel:
    TABLE = "attendance"

    @staticmethod
    def create(student_id, date, time, status, latitude, longitude,
               location_valid, face_match_status, face_confidence=None, remarks=None):
        """Insert or update an attendance record (UPSERT)."""
        query = """
            INSERT INTO attendance
                (student_id, date, time, status, latitude, longitude,
                 location_valid, face_match_status, face_confidence, remarks, recorded_by_role)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'system')
            ON CONFLICT (student_id, date, recorded_by_role) DO UPDATE SET
                time = EXCLUDED.time,
                status = EXCLUDED.status,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                location_valid = EXCLUDED.location_valid,
                face_match_status = EXCLUDED.face_match_status,
                face_confidence = EXCLUDED.face_confidence,
                remarks = EXCLUDED.remarks,
                marked_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        location_val_int = 1 if location_valid else 0
        return execute_insert(query, (
            student_id, date, time, status, latitude, longitude,
            location_val_int, face_match_status, face_confidence, remarks
        ))

    @staticmethod
    def get_by_student(student_id, limit=30):
        """Fetch recent attendance records for a student."""
        query = """
            SELECT * FROM attendance
            WHERE student_id = %s
            ORDER BY marked_at DESC
            LIMIT %s
        """
        return execute_query(query, (student_id, limit), fetch="all")

    @staticmethod
    def get_by_student_and_date(student_id, date):
        """Check if automated attendance was already marked for a specific date."""
        query = "SELECT * FROM attendance WHERE student_id = %s AND date = %s AND recorded_by_role = 'system'"
        return execute_query(query, (student_id, date), fetch="one")

    @staticmethod
    def get_all_by_date(date):
        """Get all attendance records for a given date."""
        query = """
            SELECT a.*, s.name, s.department, s.class_name
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.date = %s
            ORDER BY a.time ASC
        """
        return execute_query(query, (date,), fetch="all")

    @staticmethod
    def get_summary(student_id):
        """Get attendance count summary (present/absent/late) for a student."""
        query = """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) AS present_count,
                SUM(CASE WHEN status = 'absent'  THEN 1 ELSE 0 END) AS absent_count,
                SUM(CASE WHEN status = 'late'    THEN 1 ELSE 0 END) AS late_count
            FROM attendance
            WHERE student_id = %s
        """
        return execute_query(query, (student_id,), fetch="one")

    @staticmethod
    def update_status(attendance_id, status):
        """Update the status of an existing attendance record."""
        query = "UPDATE attendance SET status = %s WHERE id = %s"
        execute_insert(query, (status, attendance_id))

    @staticmethod
    def filter_by_date_range(student_id, start_date, end_date):
        """Fetch attendance records within a date range."""
        query = """
            SELECT * FROM attendance
            WHERE student_id = %s AND date BETWEEN %s AND %s
            ORDER BY date DESC
        """
        return execute_query(query, (student_id, start_date, end_date), fetch="all")

    @staticmethod
    def get_weekly_summary(student_id):
        """Calculate weekly stats since Monday and array of 7 daily stats."""
        # Get the aggregated stats
        query_total = """
            WITH week_bounds AS (
                SELECT date_trunc('week', CURRENT_DATE)::date as monday
            ),
            daily_status AS (
                SELECT student_id, date, 
                       MAX(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as is_present
                FROM attendance
                WHERE student_id = %s AND date >= (SELECT monday FROM week_bounds)
                GROUP BY student_id, date
            )
            SELECT
                COUNT(*) AS total,
                SUM(is_present) AS present_count
            FROM daily_status
        """
        row = execute_query(query_total, (student_id,), fetch="one")
        total = row["total"] if row and row["total"] else 0
        present = row["present_count"] if row and row["present_count"] else 0
        percentage = int(round((present / total * 100), 0)) if total > 0 else 0

        # Get granular day-by-day boolean values (100 or 0)
        query_days = """
            WITH week_bounds AS (
                SELECT date_trunc('week', CURRENT_DATE)::date as monday
            ),
            day_series AS (
                SELECT (monday + i * INTERVAL '1 day')::date as target_date, (i + 1) as dow_num
                FROM week_bounds, generate_series(0, 6) AS i
            )
            SELECT 
                ds.target_date,
                COALESCE(MAX(CASE WHEN a.status = 'present' THEN 100 ELSE 0 END), 0) as presence_val
            FROM day_series ds
            LEFT JOIN attendance a ON a.student_id = %s AND a.date = ds.target_date
            GROUP BY ds.target_date
            ORDER BY ds.target_date
        """
        days_rows = execute_query(query_days, (student_id,), fetch="all") or []
        daily_data = [int(r["presence_val"]) for r in days_rows]
        # Guarantee 7 elements just in case
        while len(daily_data) < 7: daily_data.append(0)

        return {
            "total_records": total,
            "present_count": present,
            "percentage": percentage,
            "daily_data": daily_data
        }


def store_auto_check(student_id, lat, lng, distance, status, face_verified=False):
    from DATABASE.connection.db_connection import get_connection
    from datetime import datetime, timedelta
    try:
        conn = get_connection()
        import psycopg2.extras
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        now = datetime.now()
        current_date = now.date()
        
        from CONFIG.college_location_config import RADIUS
        is_inside = distance <= RADIUS
        gps_status = 'inside' if is_inside else 'outside'

        # 1. ALWAYS Save to raw log (even outside hours)
        cursor.execute("""
            INSERT INTO auto_verify_log 
            (student_id, latitude, longitude, distance_meters, gps_status, final_status, check_time)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (student_id, lat, lng, distance, gps_status, status))
        
        # 2. Hard enforcement of 9 AM - 9 PM schedule for ATTENDANCE marking
        if not (9 <= now.hour < 21): 
            cursor.close()
            conn.close()
            return {
                "success": False, 
                "message": "Outside active verification hours (9 AM - 9 PM)", 
                "status": "idle", 
                "is_inside": is_inside,
                "grace_timer_passed": False,
                "grace_time_remaining": 0
            }
        
        # 3. Fetch existing timer data for today
        cursor.execute("""
            SELECT status, recorded_by_role, marked_at,
                   grace_timer_started_at, grace_timer_passed, fingerprint_verified 
            FROM attendance 
            WHERE student_id = %s AND date = %s AND recorded_by_role = 'system'
        """, (student_id, current_date))
        existing = cursor.fetchone()
        
        timer_start = None
        timer_passed = False
        last_status = None
        last_role = 'system'
        last_at = None
        
        if existing:
            timer_start = existing.get('grace_timer_started_at')
            timer_passed = bool(existing.get('grace_timer_passed'))
            last_status = existing.get('status')
            last_role = existing.get('recorded_by_role', 'system')
            last_at = existing.get('marked_at')
        
        # 4. Calculate Grace Timer states
        if not is_inside:
            # OUTSIDE: Initialize or check duration
            if not timer_start:
                timer_start = now # Start timer now
            
            elapsed = (now - timer_start).total_seconds()
            if elapsed > 300: # 5 mins
                timer_passed = True
        
        location_valid = 1 if is_inside else 0
        
        # ── Status Calculation ──
        # We now trust the 'status' passed from the route, which already 
        # accounts for global toggles (Face ON/OFF etc).
        # We only ensure distance-based grace timer logic if needed.
        
        dist_suffix = "inside" if is_inside else "outside"
        remarks = f"{distance:.1f}m {dist_suffix}"
        
        # Face match display logic for history: Matched only if real face verified
        face_match_status = 'success' if face_verified else 'not_attempted'
        
        # ── 30-minute Auto Update Throttle ──
        should_update_history = True
        
        # 2. If existing is system, throttle updates to every 30 mins unless status changed
        if last_at and last_role == 'system':
            if isinstance(last_at, str):
                try: last_at = datetime.fromisoformat(last_at)
                except: pass
            diff_auto = (now - last_at).total_seconds() / 60
            if diff_auto < 30 and last_status == status:
                should_update_history = False

        if should_update_history:
            # Upsert core attendance record
            cursor.execute("""
                INSERT INTO attendance
                    (student_id, date, time, status, latitude, longitude,
                     location_valid, face_match_status, remarks, recorded_by_role,
                     grace_timer_started_at, grace_timer_passed, marked_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'system', %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (student_id, date, recorded_by_role) DO UPDATE SET
                    status = EXCLUDED.status,
                    time = EXCLUDED.time,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    location_valid = EXCLUDED.location_valid,
                    face_match_status = EXCLUDED.face_match_status,
                    remarks = EXCLUDED.remarks,
                    grace_timer_started_at = COALESCE(attendance.grace_timer_started_at, EXCLUDED.grace_timer_started_at),
                    grace_timer_passed = EXCLUDED.grace_timer_passed,
                    marked_at = CURRENT_TIMESTAMP
            """, (
                student_id, current_date, now.strftime("%H:%M:%S"), status, 
                lat, lng, location_valid, face_match_status, remarks,
                timer_start, timer_passed
            ))
        
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Calculate return data
        remaining = 0
        if timer_start and not is_inside and not timer_passed:
            current_elapsed = (datetime.now() - timer_start).total_seconds()
            remaining = max(0, 300 - current_elapsed)
            
        return {
            "success": True,
            "status": status,
            "is_inside": is_inside,
            "grace_timer_passed": timer_passed,
            "grace_time_remaining": int(remaining)
        }
    except Exception as e:
        print(f"Database Error in store_auto_check: {e}")
        return {"success": False, "status": "error", "grace_time_remaining": 0}

