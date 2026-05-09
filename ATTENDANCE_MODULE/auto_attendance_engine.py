# ============================================================
# auto_attendance_engine.py — Automated Attendance Orchestrator
# ============================================================

from BACKEND.services.attendance_service import AttendanceService
from UTILS.time_utils import get_current_date, get_current_time, is_within_attendance_window


class AutoAttendanceEngine:
    """
    The core engine that orchestrates the full attendance marking pipeline:
      1. Check time window
      2. GPS geo-fence validation
      3. Face verification
      4. Mark attendance automatically (no manual input)
    """

    def __init__(self):
        pass

    def run(self, student_id: str, latitude: float, longitude: float,
            face_descriptor: list, radius: float = None) -> dict:
        """
        Execute the full attendance pipeline for a student.

        Args:
            student_id     : The student's unique ID
            latitude       : Student's current GPS latitude
            longitude      : Student's current GPS longitude
            face_descriptor: 128-d face vector from the live camera
            radius         : Override geo-fence radius (optional)

        Returns:
            Result dict with status, success, and detailed info
        """
        # Gate 1: Time window
        if not is_within_attendance_window():
            return {
                "success": False,
                "step_failed": "time_window",
                "message": f"Attendance marking is only allowed during school hours.",
                "timestamp": f"{get_current_date()} {get_current_time()}",
            }

        # Gate 2 & 3: GPS + Face (delegated to AttendanceService)
        result = AttendanceService.mark_attendance(
            student_id=student_id,
            latitude=latitude,
            longitude=longitude,
            live_descriptor=face_descriptor,
            radius=radius,
        )

        result["timestamp"] = f"{get_current_date()} {get_current_time()}"
        return result
