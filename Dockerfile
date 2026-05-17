FROM python:3.11-slim

WORKDIR /app

# Install system libraries required by dlib/face_recognition on headless Linux.
# libx11-6     — satisfies dlib's libX11.so.6 runtime dependency
# libglib2.0-0 — required by several dlib/Pillow native dependencies
# libsm6 libxext6 libxrender1 — X11 session/extension/render libraries
# cmake build-essential — needed to compile dlib from source if no wheel is found
RUN apt-get update && apt-get install -y --no-install-recommends \
        libx11-6 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        cmake \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD gunicorn BACKEND.app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
