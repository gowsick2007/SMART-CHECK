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
        
        const endpoint = isEnrollMode ? '/api/face/enroll' : '/api/face/verify';
        const payload = isEnrollMode ? { image_base64: imageData } : { student_id: user.student_id, image: imageData };
        
        const res = await fetch(`https://smart-check-production.up.railway.app${endpoint}`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        
        if (data.success) {
            if(wrapper) {
                wrapper.classList.remove('is-scanning');
                wrapper.classList.add('success');
            }
            statusText.textContent = isEnrollMode ? "ENROLLMENT COMPLETE" : "IDENTITY VERIFIED";
            progressBar.style.width = "100%";
            window.showToast(isEnrollMode ? "Face enrolled successfully!" : "Verification successful!", "success");
            
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 2000);
        } else {
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
