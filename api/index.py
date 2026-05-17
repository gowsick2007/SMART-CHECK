import os
import sys
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Force-remove OpenCV packages that cause libX11.so.6 on headless Linux servers.
# Runs silently: no error if already absent. Must happen BEFORE face_recognition import.
subprocess.run(
    [sys.executable, "-m", "pip", "uninstall", "-y",
     "opencv-python", "opencv-contrib-python", "opencv-python-headless"],
    capture_output=True
)

from BACKEND.app import app