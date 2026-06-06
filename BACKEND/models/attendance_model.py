# ============================================================
# attendance_model.py — Attendance Record Model
# ============================================================

from DATABASE.connection.db_connection import execute_query, execute_insert


class AttendanceModel:
    TABLE = "attendance"

    @staticmethod
    def create(student_id, date, time, status, latitude, longitude,
               location_valid, face_match_status, face_confidence=None, remarks=None):
        """Insert a new attendance history record. Always INSERT — never overwrite."""
        query = """
            INSERT INTO attendance
                (student_id, date, time, status, latitude, longitude,
                 location_valid, face_match_status, face_confidence, remarks, recorded_by_role,
                 marked_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'system', CURRENT_TIMESTAMP)
            RETURNING id
        """
        location_val_bool = bool(location_valid)
        return execute_insert(query, (
            student_id, date, time, status, latitude, longitude,
            location_val_bool, face_match_status, face_confidence, remarks
        ))

    @staticmethod
    def get_by_student(student_id, limit=50):
        """
        Fetch combined history: attendance records (manual + daily summary)
        UNION auto_verify_log (every 30-min auto-verify event).
        Ordered by timestamp DESC so the most recent event appears first.
        """
        query = """
            SELECT
                date,
                time,
                status,
                latitude,
                longitude,
                location_valid,
                face_match_status,
                NULL        AS face_confidence,
                remarks,
                recorded_by_role,
                NULL        AS marked_by_name,
                marked_at
            FROM attendance
            WHERE student_id = %s AND coalesce(recorded_by_role, '') != 'system'

            UNION ALL

            SELECT
                DATE(v.check_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')  AS date,
                DATE_TRUNC('second', v.check_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')::time AS time,
                v.final_status            AS status,
                v.latitude,
                v.longitude,
                (v.gps_status = 'inside') AS location_valid,
                v.face_status             AS face_match_status,
                NULL                      AS face_confidence,
                CONCAT(
                    ROUND(v.distance_meters::numeric, 1)::text, 'm ',
                    v.gps_status,
                    ' | Face: ', v.face_status
                )                         AS remarks,
                'system'                  AS recorded_by_role,
                NULL                      AS marked_by_name,
                v.check_time              AS marked_at
            FROM (
                SELECT DISTINCT ON (
                    DATE(check_time),
                    (EXTRACT(HOUR FROM check_time)::int * 2
                     + FLOOR(EXTRACT(MINUTE FROM check_time) / 30))::int
                )
                    *
                FROM auto_verify_log
                WHERE student_id = %s
                ORDER BY
                    DATE(check_time) DESC,
                    (EXTRACT(HOUR FROM check_time)::int * 2
                     + FLOOR(EXTRACT(MINUTE FROM check_time) / 30))::int DESC,
                    check_time DESC
            ) v

            ORDER BY marked_at DESC
            LIMIT %s
        """
        return execute_query(query, (student_id, student_id, limit), fetch="all")

    @staticmethod
    def get_by_student_and_date(student_id, date):
        """Check if automated attendance was already marked for a specific date (get latest)."""
        query = "SELECT * FROM attendance WHERE student_id = %s AND date = %s AND recorded_by_role = 'system' ORDER BY marked_at DESC LIMIT 1"
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

    # FIX 3: update_status() REMOVED — all writes must be INSERT-only.
    # Do NOT re-add an UPDATE here. To correct a record, INSERT a new row.

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
                SELECT date_trunc('week',
                    (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')::date
                )::date AS monday
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
                SELECT date_trunc('week',
                    (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')::date
                )::date AS monday
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
    """
    Core auto-verification function.

    Rules:
    - 30-minute strict throttle per student (checked against auto_verify_log)
    - 10-second anti-rapid filter
    - INSIDE + face_enrolled=True + face_verified=True => PRESENT
    - INSIDE + face not enrolled OR mismatch => ABSENT, face_status='not_registered'/'failed'
    - OUTSIDE => start 5-min grace timer
    - Still OUTSIDE after 5 min => ABSENT
    - Every valid 30-min check inserts NEW record into BOTH:
        attendance (student history)
        auto_verify_log (admin panel)
    """
    from DATABASE.connection.db_connection import get_connection
    from datetime import datetime, timezone, timedelta
    # Use stdlib timezone — no external dependency, no NameError risk
    IST = timezone(timedelta(hours=5, minutes=30))
    UTC = timezone.utc
    try:
        conn = get_connection()
        import psycopg2.extras
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        now = datetime.now(IST)          # IST-aware
        now_utc = now.astimezone(UTC)    # UTC-aware (for DB comparisons)
        current_date = now.date()

        from CONFIG.college_location_config import RADIUS
        # 15m tolerance for mobile GPS drift
        ALLOWED_RADIUS = RADIUS + 15
        is_inside = distance <= ALLOWED_RADIUS
        gps_status = 'inside' if is_inside else 'outside'

        # ── Step 1: Check face enrollment + descriptor from students table ──────
        cursor.execute(
            "SELECT face_enrolled, face_descriptor FROM students WHERE student_id = %s",
            (student_id,)
        )
        student_row = cursor.fetchone()
        face_enrolled = bool(student_row.get('face_enrolled')) if student_row else False
        face_has_descriptor = bool(student_row.get('face_descriptor')) if student_row else False

        # If enrolled flag is True but descriptor is NULL → treat as not registered
        if face_enrolled and not face_has_descriptor:
            face_enrolled = False

        # Resolve face status label for auto_verify_log
        if not face_enrolled:
            face_status_label = 'not_registered'
            face_verified = False          # force False — cannot verify unregistered face
        elif face_verified:
            face_status_label = 'success'
        else:
            face_status_label = 'failed'

        # ── Step 2: Determine final status ────────────────────────────────────
        # PRESENT only if: INSIDE + face enrolled + face matched
        current_status = 'present' if (is_inside and face_enrolled and face_verified) else 'absent'

        # ── Step 3: 30-min throttle — check auto_verify_log (NOT attendance) ──
        cursor.execute("""
            SELECT id, check_time, final_status, gps_status, face_status
            FROM auto_verify_log
            WHERE student_id = %s
            ORDER BY check_time DESC LIMIT 1
        """, (student_id,))
        last_log = cursor.fetchone()
        
        should_update_id = None

        if last_log:
            # DB check_time is naive UTC — make it UTC-aware, then compare with now_utc
            ct = last_log['check_time']
            if ct.tzinfo is None:
                ct = ct.replace(tzinfo=UTC)   # treat naive DB value as UTC
            diff_secs = (now_utc - ct).total_seconds()

            # Anti-rapid filter: block if < 10 seconds since last insert
            if diff_secs < 10:
                cursor.close()
                conn.close()
                return {
                    "success": True,
                    "status": last_log['final_status'],
                    "is_inside": is_inside,
                    "inserted": False,
                    "blocked": "rapid"
                }

            diff_mins = diff_secs / 60

            # Standard 30-min block: same status within 30 mins => skip
            if diff_mins < 30:
                # Exception: student just moved INSIDE from OUTSIDE → insert immediately
                was_outside = (last_log['gps_status'] == 'outside')
                just_came_inside = is_inside and was_outside
                # Exception 2: successful face verification overrides previous failed background checks
                is_new_face_success = face_verified and last_log['face_status'] != 'success'
                
                if not just_came_inside and not is_new_face_success:
                    cursor.close()
                    conn.close()
                    return {
                        "success": True,
                        "status": last_log['final_status'],
                        "is_inside": is_inside,
                        "inserted": False,
                        "blocked": "throttle",
                        "next_check_mins": round(30 - diff_mins, 1)
                    }
                else:
                    should_update_id = last_log['id']

        # ── Step 4: Grace period for OUTSIDE ──────────────────────────────────
        grace_timer_started_at = None
        grace_timer_passed = False
        if not is_inside:
            # Fetch earliest outside entry today for grace calculation
            cursor.execute("""
                SELECT check_time FROM auto_verify_log
                WHERE student_id = %s
                  AND DATE(check_time) = %s
                  AND gps_status = 'outside'
                ORDER BY check_time ASC LIMIT 1
            """, (student_id, current_date))
            first_outside = cursor.fetchone()
            if first_outside:
                grace_timer_started_at = first_outside['check_time']
                # FIX 2: DB value may be naive UTC; normalise to UTC-aware before diff
                if grace_timer_started_at.tzinfo is None:
                    grace_timer_started_at = grace_timer_started_at.replace(tzinfo=UTC)
                elapsed = (now_utc - grace_timer_started_at).total_seconds()
                grace_timer_passed = elapsed > 300  # 5 minutes
            else:
                grace_timer_started_at = now
                grace_timer_passed = False

        # ── Step 5: Build remarks ─────────────────────────────────────────────
        dist_suffix = "INSIDE" if is_inside else "OUTSIDE"
        grace_suffix = ""
        if not is_inside:
            if grace_timer_passed:
                grace_suffix = " (Grace Expired → ABSENT)"
            else:
                grace_suffix = " (Grace Period Active)"
        if not face_enrolled:
            face_suffix = " | Face: NOT REGISTERED"
        elif not face_verified:
            face_suffix = " | Face: MISMATCH"
        else:
            face_suffix = " | Face: MATCHED"
        remarks = f"{distance:.1f}m {dist_suffix}{grace_suffix}{face_suffix}"

        # ── Step 6: Insert or Update auto_verify_log (admin panel) ────────────
        if should_update_id:
            cursor.execute("""
                UPDATE auto_verify_log
                SET latitude = %s, longitude = %s, distance_meters = %s, gps_status = %s,
                    face_status = %s, final_status = %s, check_time = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                lat, lng, distance, gps_status, face_status_label, current_status, should_update_id
            ))
        else:
            cursor.execute("""
                INSERT INTO auto_verify_log
                (student_id, latitude, longitude, distance_meters, gps_status,
                 face_status, final_status, check_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (
                student_id, lat, lng, distance,
                gps_status, face_status_label, current_status
            ))

        # ── Step 7: Daily summary row in attendance (one per student per day) ────
        face_match_col = 'success' if face_verified else 'failed'
        if should_update_id and current_status == 'present':
            cursor.execute("""
                UPDATE attendance
                SET status = 'present', face_match_status = %s, remarks = %s, marked_at = CURRENT_TIMESTAMP
                WHERE student_id = %s AND date = %s AND recorded_by_role = 'system'
            """, (face_match_col, remarks, student_id, current_date))
        else:
            cursor.execute("""
                INSERT INTO attendance
                    (student_id, date, time, status, latitude, longitude,
                     location_valid, face_match_status, remarks, recorded_by_role,
                     grace_timer_started_at, grace_timer_passed, marked_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'system', %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (student_id, date, recorded_by_role) DO NOTHING
            """, (
                student_id, current_date, now.strftime("%H:%M:%S"),
                current_status, lat, lng,
                bool(is_inside), face_match_col, remarks,
                grace_timer_started_at, grace_timer_passed
            ))


        conn.commit()
        cursor.close()
        conn.close()

        return {
            "success": True,
            "status": current_status,
            "is_inside": is_inside,
            "face_enrolled": face_enrolled,
            "face_status": face_status_label,
            "grace_timer_passed": grace_timer_passed,
            "inserted": True
        }

    except Exception as e:
        print(f"[store_auto_check] DB Error: {e}")
        import traceback; traceback.print_exc()
        return {"success": False, "status": "error", "grace_time_remaining": 0}
