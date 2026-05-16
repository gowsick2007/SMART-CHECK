# ============================================================
# face_matching_algorithm.py — Face Comparison & Matching
# ============================================================

from typing import List, Optional


def compute_face_distance(stored_descriptor: np.ndarray, live_descriptor: np.ndarray) -> float:
    """
    Compute L2 Euclidean distance between two 128-d face descriptors.

    Args:
        stored_descriptor : 128-d numpy array (from database)
        live_descriptor   : 128-d numpy array (from live camera)

    Returns:
        Distance as float. Lower = more similar. Typically < 0.5 = same person.
    """
    import numpy as np
    return float(np.linalg.norm(stored_descriptor - live_descriptor))


def is_match(distance: float, threshold: float = 0.5) -> bool:
    """
    Determine if a face distance indicates a match.

    Args:
        distance  : L2 distance between descriptors
        threshold : Maximum distance to consider a match (default 0.5)

    Returns:
        True if matched
    """
    return distance <= threshold


def find_best_match(live_descriptor: np.ndarray, candidates: List[dict], threshold: float = 0.5) -> dict:
    """
    Find the best matching student from a list of stored descriptors.

    Args:
        live_descriptor : 128-d numpy array of the live face
        candidates      : List of dicts with keys: student_id, face_descriptor (np.ndarray or list)
        threshold       : Match threshold

    Returns:
        dict with: student_id, distance, matched (bool)
    """
    best_distance = float("inf")
    best_student_id = None
    import numpy as np

    for candidate in candidates:
        stored = np.array(candidate["face_descriptor"])
        distance = compute_face_distance(stored, live_descriptor)
        if distance < best_distance:
            best_distance = distance
            best_student_id = candidate["student_id"]

    return {
        "student_id": best_student_id,
        "distance": round(best_distance, 4),
        "matched": is_match(best_distance, threshold),
        "confidence": round(max(0.0, 1.0 - best_distance), 4),
    }


def batch_compare(live_descriptor: np.ndarray, stored_descriptors: List[np.ndarray], threshold: float = 0.5):
    """
    Batch compare using face_recognition's built-in compare_faces.

    Returns:
        List of booleans indicating matches
    """
    import face_recognition
    results = face_recognition.compare_faces(stored_descriptors, live_descriptor, tolerance=threshold)
    distances = face_recognition.face_distance(stored_descriptors, live_descriptor)
    return results, distances.tolist()
