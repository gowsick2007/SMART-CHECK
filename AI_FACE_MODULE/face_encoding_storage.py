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
    Tries multiple strategies to maximise detection on low-quality webcam frames:
      1. 2x upsample (mandatory — dlib needs ~80px face height)
      2. Brightness/contrast enhancement for dark frames
      3. face_locations(upsample=2, model='hog') → face_encodings with known locations
      4. Fallback: horizontally-mirrored image (handles camera mirror variants)

    Returns 128-d numpy array or None if no face found after all attempts.
    """
    import io
    from PIL import Image, ImageEnhance
    import face_recognition
    import numpy as np

    try:
        image = Image.open(io.BytesIO(base64_bytes)).convert("RGB")

        # ── Step 1: 2x upsample ───────────────────────────────────────────────
        w, h = image.size
        image = image.resize((w * 2, h * 2), Image.LANCZOS)

        # ── Step 2: Brightness/contrast fix for dark frames ───────────────────
        # Compute mean brightness; boost if too dark (< 100/255)
        img_arr = np.array(image)
        mean_brightness = img_arr.mean()
        if mean_brightness < 100:
            factor = min(2.5, 180.0 / max(mean_brightness, 1))
            image = ImageEnhance.Brightness(image).enhance(factor)
            image = ImageEnhance.Contrast(image).enhance(1.3)

        image_np = np.array(image)

        # ── Step 3: Try original orientation ─────────────────────────────────
        locations = face_recognition.face_locations(
            image_np, number_of_times_to_upsample=2, model="hog"
        )
        if locations:
            encodings = face_recognition.face_encodings(image_np, known_face_locations=locations, num_jitters=1)
            if encodings:
                print(f"[FaceEncoding] Face detected (original) — locations: {locations}")
                return encodings[0]

        # ── Step 4: Fallback — horizontally mirror the frame and retry ────────
        mirrored_np = np.fliplr(image_np)
        locations_m = face_recognition.face_locations(
            mirrored_np, number_of_times_to_upsample=2, model="hog"
        )
        if locations_m:
            encodings_m = face_recognition.face_encodings(mirrored_np, known_face_locations=locations_m, num_jitters=1)
            if encodings_m:
                print(f"[FaceEncoding] Face detected (mirrored fallback) — locations: {locations_m}")
                return encodings_m[0]

        print("[FaceEncoding] No face found after original + mirror attempts.")
        return None

    except Exception as e:
        traceback.print_exc()
        print(f"[FaceEncoding] Error encoding base64 image: {e}")
        return None
