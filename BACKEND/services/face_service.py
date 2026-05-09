# ============================================================
# face_service.py — Face Recognition Business Logic
# ============================================================

import numpy as np
# NOTE: AI_FACE_MODULE is imported lazily (inside methods) so Flask starts
# correctly even if face_recognition/dlib is not yet installed.
from BACKEND.models.face_model import FaceModel
from CONFIG.system_settings import FACE_MATCH_THRESHOLD


def _get_face_matchers():
    """Lazy import of face matching functions."""
    from AI_FACE_MODULE.face_matching_algorithm import compute_face_distance, is_match
    return compute_face_distance, is_match


def _get_encoder():
    """Lazy import of face encoding function."""
    from AI_FACE_MODULE.face_encoding_storage import encode_face_from_image
    return encode_face_from_image


class FaceService:

    @staticmethod
    def enroll_face(student_id: str, image_path: str) -> dict:
        """
        Enroll a student's face from a saved image.
        Generates and stores the 128-d face descriptor.

        Returns:
            dict with success flag and message
        """
        try:
            encode_face_from_image = _get_encoder()
        except ImportError as e:
            return {"success": False, "message": f"Face recognition library not installed: {e}"}

        descriptor = encode_face_from_image(image_path)
        if descriptor is None:
            return {"success": False, "message": "No face detected in the uploaded image. Please try again."}

        FaceModel.save_descriptor(student_id, descriptor.tolist(), image_path=image_path)
        return {"success": True, "message": "Face enrolled successfully."}

    @staticmethod
    def verify_face(student_id: str, live_descriptor: list) -> dict:
        """
        Compare a live face descriptor against the stored descriptor for a student.

        Args:
            student_id      : The student's ID
            live_descriptor : 128-d vector from the live camera frame (as a list)

        Returns:
            dict with matched (bool), confidence (float), message
        """
        try:
            compute_face_distance, is_match = _get_face_matchers()
        except ImportError as e:
            return {"matched": False, "confidence": 0.0, "message": f"Face recognition library not installed: {e}"}

        stored = FaceModel.get_by_student_id(student_id)
        if not stored:
            return {"matched": False, "confidence": 0.0, "message": "No face enrolled for this student."}

        stored_descriptor = np.array(stored["face_descriptor"])
        live_arr = np.array(live_descriptor)

        distance = compute_face_distance(stored_descriptor, live_arr)
        matched = is_match(distance, threshold=FACE_MATCH_THRESHOLD)
        confidence = round(max(0.0, 1.0 - distance), 4)

        return {
            "matched": matched,
            "confidence": confidence,
            "distance": round(distance, 4),
            "message": "Face matched successfully." if matched else "Face does not match. Access denied.",
        }

    @staticmethod
    def identify_student(live_descriptor: list) -> dict:
        """
        Identify a student by comparing their live face against ALL stored faces.
        Returns the best match.

        Args:
            live_descriptor : 128-d vector (as a list)

        Returns:
            dict with student_id, confidence, matched
        """
        try:
            compute_face_distance, is_match = _get_face_matchers()
        except ImportError as e:
            return {"matched": False, "student_id": None, "message": f"Face recognition library not installed: {e}"}

        all_faces = FaceModel.get_all_descriptors()
        if not all_faces:
            return {"matched": False, "student_id": None, "message": "No face data in system."}

        live_arr = np.array(live_descriptor)
        best_match = None
        best_distance = float("inf")

        for record in all_faces:
            stored_arr = np.array(record["face_descriptor"])
            dist = compute_face_distance(stored_arr, live_arr)
            if dist < best_distance:
                best_distance = dist
                best_match = record["student_id"]

        matched = is_match(best_distance, threshold=FACE_MATCH_THRESHOLD)
        confidence = round(max(0.0, 1.0 - best_distance), 4)

        return {
            "matched": matched,
            "student_id": best_match if matched else None,
            "confidence": confidence,
            "distance": round(best_distance, 4),
            "message": f"Identified student: {best_match}" if matched else "No match found.",
        }
