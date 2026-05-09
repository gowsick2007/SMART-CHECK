// ============================================================
// face.js — Camera, Face Detection & Descriptor (face-api.js)
// Uses face-api.js CDN for browser-based face recognition
// ============================================================

// Load face-api.js from CDN dynamically
(function loadFaceApi() {
  const script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js';
  script.onload = () => { console.log('[FaceJS] face-api.js loaded'); };
  document.head.appendChild(script);
})();

const MODELS_URL = 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights';

let modelsLoaded    = false;
let cameraStream    = null;
let detectionLoop   = null;
let lastDescriptor  = null;
let faceDetected    = false;

// ── Load face-api models ──────────────────────────────────────
async function loadFaceModels() {
  if (modelsLoaded) return true;
  try {
    await faceapi.nets.tinyFaceDetector.loadFromUri(MODELS_URL);
    await faceapi.nets.faceLandmark68TinyNet.loadFromUri(MODELS_URL);
    await faceapi.nets.faceRecognitionNet.loadFromUri(MODELS_URL);
    modelsLoaded = true;
    console.log('[FaceJS] Models loaded');
    return true;
  } catch (e) {
    console.error('[FaceJS] Failed to load models:', e);
    return false;
  }
}

// ── Start webcam ──────────────────────────────────────────────
async function startCamera(videoId = 'camera-video', statusId = 'camera-status') {
  const videoEl = document.getElementById(videoId);
  const statusEl = document.getElementById(statusId);

  if (!videoEl) return false;

  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480, facingMode: 'user' },
      audio: false,
    });
    videoEl.srcObject = cameraStream;
    if (statusEl) statusEl.textContent = 'Camera active — loading face models…';

    await loadFaceModels();

    if (statusEl) statusEl.textContent = 'Ready — position your face in the circle';
    startFaceDetectionLoop(videoEl, statusId);

    document.getElementById('start-cam-btn') && (document.getElementById('start-cam-btn').disabled = true);
    document.getElementById('stop-cam-btn')  && (document.getElementById('stop-cam-btn').disabled  = false);
    return true;
  } catch (e) {
    if (statusEl) statusEl.textContent = 'Camera access denied';
    showToast('Camera permission denied. Please allow access.', 'error');
    return false;
  }
}

// ── Stop webcam ───────────────────────────────────────────────
function stopCamera() {
  if (detectionLoop) { clearInterval(detectionLoop); detectionLoop = null; }
  if (cameraStream) { cameraStream.getTracks().forEach(t => t.stop()); cameraStream = null; }
  faceDetected   = false;
  lastDescriptor = null;

  const videoEl = document.getElementById('camera-video');
  if (videoEl) videoEl.srcObject = null;

  const statusEl = document.getElementById('camera-status');
  if (statusEl) statusEl.textContent = 'Camera stopped';

  document.getElementById('start-cam-btn') && (document.getElementById('start-cam-btn').disabled = false);
  document.getElementById('stop-cam-btn')  && (document.getElementById('stop-cam-btn').disabled  = true);

  updateFaceLiveCheck(false);
}

// ── Continuous detection loop ─────────────────────────────────
function startFaceDetectionLoop(videoEl, statusId) {
  const statusEl = document.getElementById(statusId);
  const options  = new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 });

  detectionLoop = setInterval(async () => {
    if (!videoEl || !videoEl.readyState || videoEl.readyState < 2) return;
    if (!modelsLoaded) return;

    try {
      const detection = await faceapi
        .detectSingleFace(videoEl, options)
        .withFaceLandmarks(true)
        .withFaceDescriptor();

      if (detection) {
        faceDetected   = true;
        lastDescriptor = Array.from(detection.descriptor);
        if (statusEl) statusEl.textContent = `Face detected (${(detection.detection.score * 100).toFixed(0)}% confidence)`;
        updateFaceLiveCheck(true);
        checkReadyToMark();
      } else {
        faceDetected   = false;
        lastDescriptor = null;
        if (statusEl) statusEl.textContent = 'Looking for face… position within the circle';
        updateFaceLiveCheck(false);
      }
    } catch (e) {
      // Silently ignore transient detection errors
    }
  }, 800);
}

// ── Capture a single descriptor from current frame ───────────
async function captureFaceDescriptor(videoId = 'camera-video') {
  const videoEl = document.getElementById(videoId);
  if (!videoEl || !modelsLoaded) return null;

  const options = new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 });
  const result  = await faceapi
    .detectSingleFace(videoEl, options)
    .withFaceLandmarks(true)
    .withFaceDescriptor();

  if (!result) return null;
  return Array.from(result.descriptor);
}

// ── Get the most recently detected descriptor ─────────────────
function getLastDescriptor() { return lastDescriptor; }
function isFaceDetected()    { return faceDetected; }

// ── Update the UI checklist item for face live status ─────────
function updateFaceLiveCheck(detected) {
  const el = document.getElementById('check-face-live');
  if (!el) return;
  if (detected) {
    el.textContent  = 'Detected';
    el.className    = 'check-status check-ok';
  } else {
    el.textContent  = 'Waiting…';
    el.className    = 'check-status check-wait';
  }
}

// ── Enable "Mark Attendance" button when all conditions met ───
function checkReadyToMark() {
  const markBtn = document.getElementById('mark-btn');
  if (!markBtn) return;

  const gpsOk  = document.getElementById('check-gps')?.classList.contains('check-ok') ||
                 document.getElementById('check-gps')?.textContent.includes('Inside');
  const faceOk = faceDetected;

  markBtn.disabled = !(gpsOk && faceOk);
}
