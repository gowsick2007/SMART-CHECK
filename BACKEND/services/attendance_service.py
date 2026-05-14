# ============================================================
# attendance_service.py — Attendance Business Logic
# ============================================================

from datetime import date, datetime
from BACKEND.models.attendance_model import AttendanceModel
from BACKEND.models.student_model import StudentModel
from BACKEND.services.geofence_service import GeofenceService
from BACKEND.services.face_service import FaceService
from UTILS.time_utils import get_current_date, get_current_time, is_within_attendance_window, get_attendance_status
from CONFIG.system_settings import FACE_MATCH_THRESHOLD


class AttendanceService:

    @staticmethod
    def mark_attendance(student_id: str, latitude: float, longitude: float,
                        live_descriptor: list, radius: float = None, is_periodic: bool = False) -> dict:
        """
        Core auto-attendance engine.
        Conditions:
            1. GPS must be within geo-fence boundary
            2. Face descriptor must match stored face

        Returns:
            dict with success, status, and details
        """
        today = get_current_date()
        now = get_current_time()

        # Check if attendance already marked today
        existing = AttendanceModel.get_by_student_and_date(student_id, today)
        if existing and not is_periodic:
            return {
                "success": False,
                "already_marked": True,
                "message": f"Attendance already marked for today ({today}).",
                "record": existing,
            }

        # Check attendance window
        if not is_within_attendance_window():
            return {"success": False, "message": "Attendance marking is not allowed at this time."}

        # Step 1: GPS Geo-fence check
        geo_result = GeofenceService.is_within_boundary(latitude, longitude, radius)
        location_valid = geo_result["allowed"]

        if not location_valid:
            # Store failed attempt
            AttendanceModel.create(
                student_id=student_id, date=today, time=now, status="absent",
                latitude=latitude, longitude=longitude, location_valid=False,
                face_match_status="not_attempted", remarks="Outside geo-fence boundary"
            )
            return {
                "success": False,
                "location_valid": False,
                "message": f"You are {geo_result['distance_m']}m away. Must be within {geo_result['radius_m']}m of college.",
            }

        # Step 2: Face recognition check
        face_result = FaceService.verify_face(student_id, live_descriptor)
        face_matched = face_result["matched"]
        face_confidence = face_result["confidence"]

        if not face_matched:
            AttendanceModel.create(
                student_id=student_id, date=today, time=now, status="absent",
                latitude=latitude, longitude=longitude, location_valid=True,
                face_match_status="failed", face_confidence=face_confidence,
                remarks="Face verification failed"
            )
            return {
                "success": False,
                "location_valid": True,
                "face_matched": False,
                "message": "Face verification failed. Attendance not marked.",
            }

        # Both checks passed — determine status
        attendance_status = "present"

        record_id = AttendanceModel.create(
            student_id=student_id, date=today, time=now, status="present",
            latitude=latitude, longitude=longitude, location_valid=True,
            face_match_status="success", face_confidence=face_confidence,
            remarks=f"Distance: {geo_result['distance_m']}m from campus center"
        )

        return {
            "success": True,
            "status": attendance_status,
            "location_valid": True,
            "face_matched": True,
            "face_confidence": face_confidence,
            "distance_m": geo_result["distance_m"],
            "record_id": record_id,
            "message": f"Attendance marked as '{attendance_status}' at {now}.",
        }

    @staticmethod
    def get_history(student_id: str, limit: int = 30):
        """Fetch attendance history for a student."""
        return AttendanceModel.get_by_student(student_id, limit=limit)

    @staticmethod
    def get_summary(student_id: str):
        """Get attendance summary statistics."""
        return AttendanceModel.get_summary(student_id)

    @staticmethod
    def get_by_date_range(student_id, start_date, end_date):
        return AttendanceModel.filter_by_date_range(student_id, start_date, end_date)
