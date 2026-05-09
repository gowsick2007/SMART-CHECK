# ============================================================
# attendance_validator.py — Pre-Attendance Validation Logic
# ============================================================

from ATTENDANCE_MODULE.status_manager import is_already_marked
from UTILS.time_utils import get_current_date, is_within_attendance_window
from GPS_LOCATION_MODULE.geo_fence_validator import GeoFenceValidator
from BACKEND.models.face_model import FaceModel
from CONFIG.radius_config import ATTENDANCE_RADIUS


class AttendanceValidator:
    """
    Validates all pre-conditions before attendance is marked.
    Returns a structured validation report.
    """

    def __init__(self):
        self.geo_validator = GeoFenceValidator(radius_m=ATTENDANCE_RADIUS)

    def validate_all(self, student_id: str, latitude: float, longitude: float) -> dict:
        """
        Run all validations:
          1. Time window check
          2. Duplicate check (already marked today)
          3. GPS geo-fence check
          4. Face enrollment check (has a stored face)

        Returns:
            dict with passed (bool), checks (dict of individual results)
        """
        today = get_current_date()
        checks = {}

        # 1. Time window
        time_ok = is_within_attendance_window()
        checks["time_window"] = {
            "passed": time_ok,
            "message": "Within attendance window." if time_ok else "Outside attendance hours.",
        }

        # 2. Already marked
        already_done = is_already_marked(student_id, today)
        checks["duplicate"] = {
            "passed": not already_done,
            "message": "Not yet marked today." if not already_done else "Attendance already marked for today.",
        }

        # 3. Geo-fence
        geo_result = self.geo_validator.validate(latitude, longitude)
        checks["geofence"] = {
            "passed": geo_result["allowed"],
            "message": geo_result["message"],
            "distance_m": geo_result["distance_m"],
        }

        # 4. Face enrolled
        has_face = FaceModel.has_face_data(student_id)
        checks["face_enrolled"] = {
            "passed": has_face,
            "message": "Face data found." if has_face else "No face enrolled. Please scan your face first.",
        }

        all_passed = all(c["passed"] for c in checks.values())
        return {"passed": all_passed, "checks": checks}
