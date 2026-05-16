# ============================================================
# face_encoding_storage.py — Face Encoding Generation
# ============================================================

import numpy as np
from typing import Optional


def encode_face_from_image(image_path: str) -> Optional[np.ndarray]:
    """
    Load an image from disk and generate a 128-d face descriptor.

    Args:
        image_path: Absolute path to the face image

    Returns:
        128-d numpy array (face encoding) or None if no face detected
    """
    import face_recognition
    import numpy as np
    try:
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if not encodings:
            return None
        return encodings[0]  # Return the first detected face encoding
    except Exception as e:
        print(f"[FaceEncoding] Error encoding image {image_path}: {e}")
        return None


def encode_face_from_frame(frame: np.ndarray) -> Optional[np.ndarray]:
    """
    Generate a 128-d face descriptor from an OpenCV BGR frame.

    Args:
        frame: OpenCV BGR image array

    Returns:
        128-d numpy array or None
    """
    import face_recognition
    import numpy as np
    try:
        # Convert BGR to RGB using numpy slicing (no cv2 needed)
        rgb = frame[:, :, ::-1]
        encodings = face_recognition.face_encodings(rgb)
        if not encodings:
            return None
        return encodings[0]
    except Exception as e:
        print(f"[FaceEncoding] Error encoding frame: {e}")
        return None


def encode_face_from_base64(base64_bytes: bytes) -> Optional[np.ndarray]:
    """
    Decode a base64 image and generate a face encoding.

    Args:
        base64_bytes: Raw bytes of a JPEG/PNG image

    Returns:
        128-d numpy array or None
    """
    import io
    from PIL import Image
    import face_recognition
    import numpy as np

    try:
        image = Image.open(io.BytesIO(base64_bytes)).convert("RGB")
        image_np = np.array(image)
        encodings = face_recognition.face_encodings(image_np)
        if not encodings:
            return None
        return encodings[0]
    except Exception as e:
        print(f"[FaceEncoding] Error encoding base64 image: {e}")
        return None
