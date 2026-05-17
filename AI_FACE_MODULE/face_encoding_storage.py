# ============================================================
# face_encoding_storage.py — Face Encoding Generation
# ============================================================

import numpy as np
import traceback
from typing import Optional


def encode_face_from_image(image_path: str) -> Optional[np.ndarray]:
    """
    Load an image from disk and generate a 128-d face descriptor.
    Uses the exact same robust pipeline as verify (encode_face_from_base64).
    """
    import traceback
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return encode_face_from_base64(image_bytes)
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
    Pipeline (timeout-safe, max image dimension capped at 800px):
      1. Resize to max 800px long-side — prevents gunicorn timeout on large frames
      2. Brightness/contrast boost for dark frames
      3. face_locations(upsample=1, hog) on original → face_encodings
      4. Fallback: horizontally-mirrored image (handles DroidCam/selfie mirror)
    Returns 128-d numpy array or None after all attempts.
    """
    import io
    from PIL import Image, ImageEnhance
    import face_recognition
    import numpy as np

    try:
        image = Image.open(io.BytesIO(base64_bytes)).convert("RGB")

        # ── Step 1: Cap at 800px on the long side (prevents timeout) ─────────
        # A 1280x720 frame after 2x was 2560x1440 → dlib timeout.
        # At 800px max, a 1280x720 becomes 800x450 — still enough for HOG.
        w, h = image.size
        MAX_SIDE = 800
        if max(w, h) > MAX_SIDE:
            scale = MAX_SIDE / max(w, h)
            image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        elif max(w, h) < 300:
            # Too small — upsample to at least 300px so dlib finds the face
            scale = 300 / max(w, h)
            image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        # ── Step 2: Brightness/contrast fix for dark frames ───────────────────
        img_arr = np.array(image)
        mean_brightness = img_arr.mean()
        if mean_brightness < 100:
            factor = min(2.0, 180.0 / max(mean_brightness, 1))
            image = ImageEnhance.Brightness(image).enhance(factor)
            image = ImageEnhance.Contrast(image).enhance(1.2)

        image_np = np.array(image)

        # ── Step 3: Try original orientation ─────────────────────────────────
        locations = face_recognition.face_locations(
            image_np, number_of_times_to_upsample=1, model="hog"
        )
        if locations:
            encodings = face_recognition.face_encodings(
                image_np, known_face_locations=locations, num_jitters=1
            )
            if encodings:
                print(f"[FaceEncoding] Face found (original) locations={locations}")
                return encodings[0]

        # ── Step 4: Fallback — mirror and retry ──────────────────────────────
        mirrored_np = np.fliplr(image_np)
        locations_m = face_recognition.face_locations(
            mirrored_np, number_of_times_to_upsample=1, model="hog"
        )
        if locations_m:
            encodings_m = face_recognition.face_encodings(
                mirrored_np, known_face_locations=locations_m, num_jitters=1
            )
            if encodings_m:
                print(f"[FaceEncoding] Face found (mirrored) locations={locations_m}")
                return encodings_m[0]

        print("[FaceEncoding] No face found after original + mirror attempts.")
        return None

    except Exception as e:
        traceback.print_exc()
        print(f"[FaceEncoding] Error encoding base64 image: {e}")
        return None
