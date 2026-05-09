# ============================================================
# face_utils.py — Face Recognition Utility Helpers
# ============================================================

import numpy as np
import json


def descriptor_to_list(descriptor: np.ndarray) -> list:
    """Convert a numpy 128-d array to a Python list (for JSON serialization)."""
    return descriptor.tolist()


def list_to_descriptor(descriptor_list: list) -> np.ndarray:
    """Convert a Python list back to a numpy array."""
    return np.array(descriptor_list, dtype=np.float64)


def descriptors_from_json(json_str: str) -> np.ndarray:
    """Parse a JSON string into a numpy descriptor array."""
    return np.array(json.loads(json_str), dtype=np.float64)


def euclidean_distance(a: list, b: list) -> float:
    """Compute Euclidean (L2) distance between two descriptor lists."""
    return float(np.linalg.norm(np.array(a) - np.array(b)))


def confidence_from_distance(distance: float) -> float:
    """
    Convert L2 distance to a 0–1 confidence score.
    Distance 0.0 → confidence 1.0 (perfect match)
    Distance 1.0+ → confidence 0.0
    """
    return round(max(0.0, 1.0 - distance), 4)


def is_valid_descriptor(descriptor) -> bool:
    """Check if a descriptor is a valid 128-element list/array."""
    if isinstance(descriptor, (list, np.ndarray)):
        return len(descriptor) == 128
    return False
