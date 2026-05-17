// ============================================================
// face_verification.js — Face Recognition UI Logic
// ============================================================

let stream = null;
let isScanning = false;

document.addEventListener('DOMContentLoaded', () => {
    initCamera();
});

async function initCamera() {
    const video = document.getElementById('camera-preview');
    
    // Check mode
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('mode') === 'enroll') {
        const header = document.querySelector('.scanner-header h1');
        if (header) header.textContent = "BIOMETRIC ENROLLMENT";
        const btn = document.getElementById('scan-btn');
        if (btn) btn.innerHTML = '<i class="fa-solid fa-face-viewfinder"></i> CAPTURE & ENROLL';
        const sub = document.querySelector('.scanner-header p');
        if (sub) sub.textContent = "Register your face data to enable secure attendance marking.";
    }

    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: "user"
            } 
        });
        video.srcObject = stream;
        video.onloadedmetadata = () => video.play();
    } catch (err) {
        console.error("Camera access denied:", err);
        window.showToast("Camera access denied. Please check permissions.", "error");
    }
}

async function startScan() {
    if (isScanning) return;
    
    const urlParams = new URLSearchParams(window.location.search);
    const isEnrollMode = urlParams.get('mode') === 'enroll';
    
    isScanning = true;
    const btn = document.getElementById('scan-btn');
    const statusText = document.getElementById('scan-status');
    const progressBar = document.getElementById('scan-progress');
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> ' + (isEnrollMode ? 'ENROLLING...' : 'SCANNING...');
    statusText.textContent = isEnrollMode ? "CAPTURING BIOMETRIC PROFILE..." : "ALGORITHM ANALYZING FACE...";
    
    const wrapper = document.getElementById('scanner-container');
    if(wrapper) {
        wrapper.classList.remove('success', 'failed');
        wrapper.classList.add('is-scanning');
    }
    
    // UI Progress Animation
    let progress = 0;
    const interval = setInterval(() => {
        progress += 1.5;
        progressBar.style.width = `${Math.min(progress, 100)}%`;
        if (progress >= 100) clearInterval(interval);
    }, 50);

    try {
        const video = document.getElementById('camera-preview');
        const canvas = document.createElement('canvas');
        // Use actual video pixel dimensions
        canvas.width  = video.videoWidth  || 640;
        canvas.height = video.videoHeight || 480;
        const ctx = canvas.getContext('2d');
        // Flip horizontally to correct DroidCam/selfie mirror effect.
        // face_recognition needs a geometrically correct (unmirrored) face.
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const imageData = canvas.toDataURL('image/jpeg', 0.95);

        const user = JSON.parse(localStorage.getItem('sat_student') || '{}');
        const token = localStorage.getItem('sat_token');
        
        let lat = null, lng = null;
        if (!isEnrollMode) {
            try {
                const pos = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000, maximumAge: 0 });
                });
                lat = pos.coords.latitude;
                lng = pos.coords.longitude;
            } catch(e) {
                console.warn("Could not get GPS location", e);
            }
        }
        
        const endpoint = isEnrollMode ? '/api/face/enroll' : '/api/face/verify';
        const payload = isEnrollMode 
            ? { image_base64: imageData } 
            : { student_id: user.student_id, image: imageData, latitude: lat, longitude: lng };
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 25000); // 25s hard limit

        let res, data;
        try {
            res = await fetch(`https://smart-check-production.up.railway.app${endpoint}`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload),
                signal: controller.signal
            });
        } catch (fetchErr) {
            clearTimeout(timeoutId);
            if (fetchErr.name === 'AbortError') {
                statusText.textContent = "REQUEST TIMED OUT";
                window.showToast("Request timed out. Server is processing — please try again.", "error");
            } else {
                window.showToast("Network error. Check your connection.", "error");
            }
            resetUI();
            return;
        }
        clearTimeout(timeoutId);

        try {
            data = await res.json();
        } catch (_) {
            // Server returned non-JSON (e.g. 502 from Railway)
            statusText.textContent = "SERVER ERROR";
            window.showToast("Server error. Please try again in a moment.", "error");
            resetUI();
            return;
        }

        if (data.success) {
            if(wrapper) {
                wrapper.classList.remove('is-scanning');
                wrapper.classList.add('success');
            }
            statusText.textContent = isEnrollMode ? "ENROLLMENT COMPLETE" : "ATTENDANCE MARKED PRESENT";
            progressBar.style.width = "100%";
            
            if (!isEnrollMode && data.is_inside) {
                show3DSuccessPopup();
            } else {
                window.showToast(isEnrollMode ? "Face enrolled successfully!" : data.message || "Verification successful!", "success");
            }
            
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 3000);
        } else {
            // Check if not registered
            if (data.face_status === 'not_registered') {
                statusText.textContent = "FACE NOT REGISTERED";
                window.showToast("Face not registered. Please enroll your face first.", "error");
                btn.innerHTML = '<i class="fa-solid fa-user-plus"></i> ENROLL FACE NOW';
                btn.onclick = () => { window.location.href = 'face_verification.html?mode=enroll'; };
                btn.disabled = false;
                wrapper?.classList.remove('is-scanning');
                return;
            }
            if(wrapper) {
                wrapper.classList.remove('is-scanning');
                wrapper.classList.add('failed');
            }
            statusText.textContent = data.message || "VERIFICATION FAILED";
            window.showToast(data.message || "Action failed.", "error");
            resetUI();
        }
    } catch (err) {
        console.error("Scan Error:", err);
        window.showToast("Server connection error.", "error");
        resetUI();
    } finally {
        isScanning = false;
    }
}

function resetUI() {
    const btn = document.getElementById('scan-btn');
    const statusText = document.getElementById('scan-status');
    const progressBar = document.getElementById('scan-progress');
    
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-face-viewfinder"></i> AUTHENTICATE IDENTITY';
    
    const wrapper = document.getElementById('scanner-container');
    if(wrapper) wrapper.classList.remove('is-scanning', 'success', 'failed');
    setTimeout(() => {
        statusText.textContent = "READY FOR SCAN";
        progressBar.style.width = "0%";
    }, 3000);
}

// Stop camera when leaving
window.addEventListener('beforeunload', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
});

function show3DSuccessPopup() {
    if (!document.getElementById('success-popup-styles')) {
        const style = document.createElement('style');
        style.id = 'success-popup-styles';
        style.textContent = `
            .success-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(8px); display: flex; justify-content: center; align-items: center; z-index: 9999; perspective: 1000px; }
            .success-card { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); padding: 40px; border-radius: 20px; border: 1px solid rgba(0, 255, 204, 0.4); box-shadow: 0 0 40px rgba(0, 255, 204, 0.3), inset 0 0 20px rgba(0, 255, 204, 0.1); text-align: center; color: white; transform-style: preserve-3d; animation: popIn3D 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; }
            .success-icon { font-size: 60px; color: #00ffcc; text-shadow: 0 0 20px rgba(0,255,204,0.8); margin-bottom: 20px; transform: translateZ(50px); animation: floatIcon 2s ease-in-out infinite alternate; }
            .success-title { margin: 0 0 10px 0; font-size: 28px; letter-spacing: 2px; transform: translateZ(30px); color: #00ffcc; }
            .success-text { margin: 0; font-size: 16px; opacity: 0.9; transform: translateZ(20px); }
            .success-status { color: #00ffcc; }
            @keyframes popIn3D { 0% { transform: scale(0.5) rotateX(45deg) rotateY(-45deg); opacity: 0; } 100% { transform: scale(1) rotateX(0deg) rotateY(0deg); opacity: 1; } }
            @keyframes floatIcon { 0% { transform: translateZ(50px) translateY(0px); } 100% { transform: translateZ(50px) translateY(-10px); } }
        `;
        document.head.appendChild(style);
    }

    const popup = document.createElement('div');
    popup.className = 'success-overlay';
    popup.innerHTML = `
        <div class="success-card">
            <div class="success-icon"><i class="fa-solid fa-shield-check"></i></div>
            <h2 class="success-title">ATTENDANCE MARKED</h2>
            <p class="success-text">Face matched and you are inside campus.<br><strong class="success-status">STATUS: PRESENT</strong></p>
        </div>
    `;
    document.body.appendChild(popup);
}
