# ============================================================
# liveness_detection.py — Anti-Spoofing / Liveness Check
# ============================================================

import cv2
import numpy as np
from typing import Optional


class LivenessDetector:
    """
    Passive liveness detection using texture analysis (LBP-based).
    Detects printed photos or screen replays being used to spoof the system.
    """

    # Threshold for LBP variance — real faces have higher texture variance
    LIVENESS_TEXTURE_THRESHOLD = 30.0

    @staticmethod
    def compute_lbp_variance(gray_face: np.ndarray) -> float:
        """
        Compute Local Binary Pattern variance on a grayscale face crop.
        Real faces have richer, more varied texture than printed/screen photos.
        """
        radius = 1
        points = 8
        height, width = gray_face.shape
        lbp = np.zeros_like(gray_face, dtype=np.uint8)

        for y in range(radius, height - radius):
            for x in range(radius, width - radius):
                center = gray_face[y, x]
                binary_string = ""
                for p in range(points):
                    angle = 2 * np.pi * p / points
                    nx = int(round(x + radius * np.cos(angle)))
                    ny = int(round(y - radius * np.sin(angle)))
                    binary_string += "1" if gray_face[ny, nx] >= center else "0"
                lbp[y, x] = int(binary_string, 2)

        return float(np.var(lbp))

    @classmethod
    def check_liveness(cls, frame: np.ndarray, face_location: tuple) -> dict:
        """
        Perform liveness check on a detected face in a frame.

        Args:
            frame         : Full BGR frame from camera
            face_location : Tuple (top, right, bottom, left) of face bounding box

        Returns:
            dict with is_live (bool), score (float), message (str)
        """
        top, right, bottom, left = face_location
        face_crop = frame[top:bottom, left:right]

        if face_crop.size == 0:
            return {"is_live": False, "score": 0.0, "message": "Invalid face crop."}

        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        gray_resized = cv2.resize(gray, (64, 64))

        variance = cls.compute_lbp_variance(gray_resized)
        is_live = variance >= cls.LIVENESS_TEXTURE_THRESHOLD

        return {
            "is_live": is_live,
            "score": round(variance, 2),
            "threshold": cls.LIVENESS_TEXTURE_THRESHOLD,
            "message": "Liveness check passed." if is_live else "Spoofing detected! Please use live camera.",
        }

    @staticmethod
    def check_blur(frame: np.ndarray) -> dict:
        """
        Detect if a frame is blurry (Laplacian variance method).
        Very blurry frames may indicate a photo being held up.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        is_sharp = variance > 100.0

        return {
            "is_sharp": is_sharp,
            "blur_score": round(float(variance), 2),
            "message": "Image quality OK." if is_sharp else "Image too blurry. Please hold still.",
        }
