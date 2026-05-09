# ============================================================
# attendance_model.py — Attendance Record Model
# ============================================================

from DATABASE.connection.db_connection import execute_query, execute_insert


class AttendanceModel:
    TABLE = "attendance"

    @staticmethod
    def create(student_id, date, time, status, latitude, longitude,
               location_valid, face_match_status, face_confidence=None, remarks=None):
        """Insert a new attendance record."""
        query = """
            INSERT INTO attendance
                (student_id, date, time, status, latitude, longitude,
                 location_valid, face_match_status, face_confidence, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        return execute_insert(query, (
            student_id, date, time, status, latitude, longitude,
            location_valid, face_match_status, face_confidence, remarks
        ))

    @staticmethod
    def get_by_student(student_id, limit=30):
        """Fetch recent attendance records for a student."""
        query = """
            SELECT * FROM attendance
            WHERE student_id = %s
            ORDER BY date DESC, time DESC
            LIMIT %s
        """
        return execute_query(query, (student_id, limit), fetch="all")

    @staticmethod
    def get_by_student_and_date(student_id, date):
        """Check if attendance was already marked for a specific date."""
        query = "SELECT * FROM attendance WHERE student_id = %s AND date = %s"
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


def store_auto_check(student_id, lat, lng, distance, status):
    from DATABASE.connection.db_connection import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    gps_status = 'inside' if status == 'present' else 'outside'
    cursor.execute("""
        INSERT INTO auto_verify_log 
        (student_id, latitude, longitude, distance_meters, gps_status, final_status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (student_id, lat, lng, distance, gps_status, status))
    conn.commit()
    cursor.close()
    conn.close()

