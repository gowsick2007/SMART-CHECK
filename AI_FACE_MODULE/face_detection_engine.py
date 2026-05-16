# ============================================================
# face_detection_engine.py — Face Detection with OpenCV & dlib
# ============================================================

import face_recognition
import numpy as np
from typing import Optional


class FaceDetectionEngine:
    """
    Handles face detection in images and video frames.
    Uses OpenCV's HOG + face_recognition (dlib under the hood).
    """

    def __init__(self, model: str = "hog"):
        """
        Args:
            model: 'hog' (faster, CPU-based) or 'cnn' (accurate, GPU-based)
        """
        self.model = model

    def detect_faces(self, image_path: str):
        """
        Detect faces in an image file.

        Returns:
            List of face location tuples: (top, right, bottom, left)
        """
        image = face_recognition.load_image_file(image_path)
        locations = face_recognition.face_locations(image, model=self.model)
        return locations

    def detect_faces_from_frame(self, frame: np.ndarray):
        """
        Detect faces from an OpenCV BGR frame.

        Args:
            frame: OpenCV image array (BGR)

        Returns:
            List of face location tuples
        """
        # Convert BGR to RGB using numpy (no cv2 dependency)
        rgb_frame = frame[:, :, ::-1]
        locations = face_recognition.face_locations(rgb_frame, model=self.model)
        return locations

    def draw_face_boxes(self, frame: np.ndarray, locations: list, color=(0, 255, 136), label: str = None):
        """
        Draw bounding boxes around detected faces on a frame.

        Returns:
            Annotated frame (np.ndarray)
        """
        import cv2 # Lazy import to avoid libX11 error if unused
        annotated = frame.copy()
        for (top, right, bottom, left) in locations:
            cv2.rectangle(annotated, (left, top), (right, bottom), color, 2)
            if label:
                cv2.putText(annotated, label, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        return annotated

    def has_face(self, image_path: str) -> bool:
        """Quick check: returns True if at least one face is detected."""
        return len(self.detect_faces(image_path)) > 0

    def capture_from_webcam(self, camera_index: int = 0, timeout_seconds: int = 10) -> Optional[np.ndarray]:
        """
        Capture a single frame from the webcam that contains a face.

        Returns:
            np.ndarray frame or None if no face found within timeout
        """
        import cv2 # Lazy import to avoid libX11 error if unused
        cap = cv2.VideoCapture(camera_index)
        import time
        start = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            locations = self.detect_faces_from_frame(frame)
            if locations:
                cap.release()
                return frame

            if time.time() - start > timeout_seconds:
                break

        cap.release()
        return None
