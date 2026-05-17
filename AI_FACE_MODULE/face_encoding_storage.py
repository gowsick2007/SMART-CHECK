# ============================================================
# face_encoding_storage.py — Face Encoding Generation
# ============================================================

import numpy as np
import traceback
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
    from PIL import Image
    try:
        rgb = np.array(Image.open(image_path).convert("RGB"))
        encodings = face_recognition.face_encodings(rgb)
        if not encodings:
            return None
        return encodings[0]  # Return the first detected face encoding
    except Exception as e:
        traceback.print_exc()
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
        traceback.print_exc()
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
        # Upsample small webcam frames so HOG detector reliably finds faces.
        # Webcam captures are often 320×240 or similar; dlib needs ~80px face height.
        min_side = 400
        w, h = image.size
        if w < min_side or h < min_side:
            scale = max(min_side / w, min_side / h)
            image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        image_np = np.array(image)
        encodings = face_recognition.face_encodings(image_np, num_jitters=1)
        if not encodings:
            return None
        return encodings[0]
    except Exception as e:
        traceback.print_exc()
        print(f"[FaceEncoding] Error encoding base64 image: {e}")
        return None
