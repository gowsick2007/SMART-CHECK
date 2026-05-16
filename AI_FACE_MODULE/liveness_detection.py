# ============================================================
# liveness_detection.py — Anti-Spoofing / Liveness Check
# ============================================================

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
            frame         : Full RGB or BGR frame as np.ndarray
            face_location : Tuple (top, right, bottom, left) of face bounding box

        Returns:
            dict with is_live (bool), score (float), message (str)
        """
        top, right, bottom, left = face_location
        face_crop = frame[top:bottom, left:right]

        if face_crop.size == 0:
            return {"is_live": False, "score": 0.0, "message": "Invalid face crop."}

        # Convert to grayscale using luminosity weights (no cv2)
        if face_crop.ndim == 3 and face_crop.shape[2] >= 3:
            gray = (0.299 * face_crop[:, :, 0] +
                    0.587 * face_crop[:, :, 1] +
                    0.114 * face_crop[:, :, 2]).astype(np.uint8)
        else:
            gray = face_crop.astype(np.uint8)

        # Resize to 64x64 using numpy (nearest-neighbour)
        h, w = gray.shape
        row_idx = (np.arange(64) * h / 64).astype(int)
        col_idx = (np.arange(64) * w / 64).astype(int)
        gray_resized = gray[np.ix_(row_idx, col_idx)]

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
        Detect if a frame is blurry (Laplacian variance method, pure numpy).
        Very blurry frames may indicate a photo being held up.
        """
        # Convert to grayscale with luminosity weights (no cv2)
        if frame.ndim == 3 and frame.shape[2] >= 3:
            gray = (0.299 * frame[:, :, 0] +
                    0.587 * frame[:, :, 1] +
                    0.114 * frame[:, :, 2])
        else:
            gray = frame.astype(float)

        # 3x3 Laplacian kernel
        kernel = np.array([[0,  1, 0],
                           [1, -4, 1],
                           [0,  1, 0]], dtype=float)
        from numpy.lib.stride_tricks import sliding_window_view
        padded = np.pad(gray, 1, mode='reflect')
        windows = sliding_window_view(padded, (3, 3))
        laplacian = (windows * kernel).sum(axis=(-2, -1))
        variance = float(np.var(laplacian))

        is_sharp = variance > 100.0
        return {
            "is_sharp": is_sharp,
            "blur_score": round(variance, 2),
            "message": "Image quality OK." if is_sharp else "Image too blurry. Please hold still.",
        }
