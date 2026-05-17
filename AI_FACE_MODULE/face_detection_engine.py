# ============================================================
# face_detection_engine.py — Face Detection with PIL & dlib
# ============================================================

import numpy as np
from PIL import Image
from typing import Optional


class FaceDetectionEngine:
    """
    Handles face detection in images and video frames.
    Uses PIL + face_recognition (dlib under the hood). No OpenCV required.
    face_recognition is imported lazily to avoid libX11.so.6 error at startup.
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
        import face_recognition  # lazy: avoids libX11 at startup
        rgb = np.array(Image.open(image_path).convert("RGB"))
        locations = face_recognition.face_locations(rgb, model=self.model)
        return locations

    def detect_faces_from_frame(self, frame: np.ndarray):
        """
        Detect faces from a BGR frame (numpy array).

        Args:
            frame: BGR image array (numpy)

        Returns:
            List of face location tuples
        """
        import face_recognition  # lazy: avoids libX11 at startup
        # Convert BGR to RGB using numpy (no cv2 dependency)
        rgb_frame = frame[:, :, ::-1]
        locations = face_recognition.face_locations(rgb_frame, model=self.model)
        return locations

    def draw_face_boxes(self, frame: np.ndarray, locations: list, color=(0, 255, 136), label: str = None):
        """
        Draw bounding boxes around detected faces on a frame.
        NOTE: Server-side annotation is not used in production; returns frame unchanged.

        Returns:
            Original frame (np.ndarray) — no annotation without a display library.
        """
        # OpenCV removed — server-side drawing not required for headless operation.
        return frame.copy()

    def has_face(self, image_path: str) -> bool:
        """Quick check: returns True if at least one face is detected."""
        return len(self.detect_faces(image_path)) > 0

    def capture_from_webcam(self, camera_index: int = 0, timeout_seconds: int = 10) -> Optional[np.ndarray]:
        """
        Webcam capture is handled by the browser (getUserMedia) in this system.
        Server-side capture via OpenCV is not supported in the headless deployment.
        """
        raise NotImplementedError(
            "Webcam capture is handled by the browser. "
            "OpenCV VideoCapture has been removed from this server."
        )
