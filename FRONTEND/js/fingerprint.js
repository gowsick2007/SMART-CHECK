let currentCoords = null;
let isEnrolled = false;
let savedCredentialId = null;
let isScanning = false;
let user = {};

document.addEventListener('DOMContentLoaded', async () => {
    const userStr = localStorage.getItem('sat_student') || localStorage.getItem('user') || '{}';
    user = JSON.parse(userStr);
    
    checkWebAuthnSupport();
    initGPSLock();
    checkFingerprintEnrollment();
});

function checkWebAuthnSupport() {
    if (!window.PublicKeyCredential) {
        const status = document.getElementById('scan-status');
        if(status) {
            status.textContent = "BIOMETRIC NOT SUPPORTED";
            status.style.color = "var(--accent-red)";
        }
        const desc = document.getElementById('scan-desc') || document.querySelector('.scan-instructions p');
        if (desc) {
             desc.innerHTML = "<strong style='color:#ff6b6b'>Biometric authentication not supported on this device / browser.</strong>";
        }
        window.showToast("Browser doesn't support platform biometric", "error");
        // Disable UI visually
        document.getElementById('scan-wrapper').style.opacity = "0.5";
        document.getElementById('scan-wrapper').onclick = null;
        isScanning = true; // prevent clicks
    }
}

// Basic utility to convert base64 string back to ArrayBuffer for create/get APIs
function base64ToBuffer(b64) {
    const bin = window.atob(b64.replace(/-/g, '+').replace(/_/g, '/'));
    const len = bin.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) bytes[i] = bin.charCodeAt(i);
    return bytes.buffer;
}

async function checkFingerprintEnrollment() {
    if (!user.student_id) return;
    try {
        const res = await fetch(`/api/fingerprint/status/${user.student_id}`);
        const data = await res.json();
        isEnrolled = !!data.enrolled;
        savedCredentialId = data.credential_id;
        
        const desc = document.getElementById('scan-desc') || document.querySelector('.scan-instructions p');
        if (desc) {
            desc.innerHTML = isEnrolled ? "Scan Registered Finger to Mark Attendance" : "<strong>FIRST TIME SETUP:</strong> Register Device Biometric";
        }
        const status = document.getElementById('scan-status');
        if (status) {
            status.textContent = isEnrolled ? "READY TO AUTHENTICATE" : "REGISTER DEVICE";
        }
    } catch (e) { console.error("Enrollment lookup failed", e); }
}

async function initGPSLock() {
    const lockStatus = document.getElementById('gps-lock-status');
    if (!navigator.geolocation) {
        if(lockStatus) lockStatus.innerHTML = `<i class="fa-solid fa-circle-exclamation" style="color:var(--accent-red)"></i> Geolocation not supported.`;
        return;
    }
    navigator.geolocation.getCurrentPosition((pos) => {
        currentCoords = pos.coords;
        if(lockStatus) lockStatus.innerHTML = `<i class="fa-solid fa-circle-check" style="color:var(--accent-green)"></i> GPS Coordinates Locked`;
    }, (err) => {
        console.error(err);
        if(lockStatus) lockStatus.innerHTML = `<i class="fa-solid fa-circle-xmark" style="color:var(--accent-red)"></i> GPS Denied!`;
    });
}

async function triggerScan() {
    if (isScanning || !window.PublicKeyCredential) return;
    if (!currentCoords) {
        window.showToast("Waiting for GPS Lock...", "warning");
        return;
    }
    if (!user.student_id) {
        window.showToast("Invalid Session", "error");
        return;
    }
    
    isScanning = true;
    const wrapper = document.getElementById('scan-wrapper');
    const status = document.getElementById('scan-status');
    const icon = document.getElementById('finger-icon');
    
    wrapper.classList.add('is-animating');
    status.textContent = isEnrolled ? "AWAITING BIOMETRIC..." : "PREPARING REGISTRATION...";
    
    try {
        // --- DUAL FORK: REGISTER VS VERIFY ---
        if (!isEnrolled) {
            // STEP 1: REAL WEBAUTHN CREATE (REGISTER)
            const challenge = new Uint8Array(32);
            window.crypto.getRandomValues(challenge);
            const userIdBytes = new TextEncoder().encode(user.student_id);

            const publicKeyCredentialCreationOptions = {
                challenge: challenge,
                rp: { name: "Smart Attendance System", id: window.location.hostname },
                user: { id: userIdBytes, name: user.email || user.student_id, displayName: user.name || user.student_id },
                pubKeyCredParams: [{ alg: -7, type: "public-key" }, { alg: -257, type: "public-key" }],
                authenticatorSelection: {
                    authenticatorAttachment: "platform", // Forces device native biometric (Fingerprint/Face/Hello)
                    userVerification: "required"
                },
                timeout: 60000
            };

            const credential = await navigator.credentials.create({ publicKey: publicKeyCredentialCreationOptions });
            
            if (!credential) throw new Error("Biometric enrollment declined by user.");

            // Extact native identifier returned upon REAL successful touch
            const credId = credential.id; 

            const regRes = await fetch('/api/fingerprint/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ student_id: user.student_id, credential_id: credId, public_key: "stored_in_attestation" })
            });
            const regData = await regRes.json();
            
            if (regData.success) {
                 wrapper.classList.remove('is-animating');
                 wrapper.classList.add('success-state');
                 status.textContent = "REGISTRATION COMPLETE";
                 window.showToast("Device linked successfully. Reloading...", "success");
                 setTimeout(() => window.location.reload(), 1500);
            } else { throw new Error(regData.message); }
            
        } else {
            // STEP 2: REAL WEBAUTHN GET (VERIFY)
            if (!savedCredentialId) throw new Error("Local identity mapping missing.");

            const challengeVerify = new Uint8Array(32);
            window.crypto.getRandomValues(challengeVerify);

            const publicKeyCredentialRequestOptions = {
                challenge: challengeVerify,
                rpId: window.location.hostname,
                allowCredentials: [{
                    type: "public-key",
                    id: base64ToBuffer(savedCredentialId)
                }],
                userVerification: "required", // Prompts physical action
                timeout: 60000
            };

            const assertion = await navigator.credentials.get({ publicKey: publicKeyCredentialRequestOptions });
            
            if (!assertion) throw new Error("Verification aborted.");

            // Verify endpoint payload submission
            const verifyRes = await fetch('/api/attendance/verify-fingerprint', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    student_id: user.student_id,
                    latitude: currentCoords.latitude,
                    longitude: currentCoords.longitude,
                    credential_id: assertion.id
                })
            });
            const data = await verifyRes.json();
            
            wrapper.classList.remove('is-animating');
            
            if (data.success) {
                wrapper.classList.add('success-state');
                icon.className = "fa-solid fa-circle-check";
                status.textContent = "VERIFICATION SUCCESSFUL";
                status.style.color = "var(--accent-green)";
                window.showToast("Physical Biometric Verified!", "success");
                
                setTimeout(() => {
                    if (data.face_required) {
                        window.showToast("Next: Facial Verification...", "info");
                        setTimeout(() => window.location.href = 'face_verification.html', 800);
                    } else {
                        const isInside = data.is_inside;
                        window.showToast(isInside ? "Marked Present!" : "Marked Outside Boundary.", isInside ? "success" : "warning");
                        setTimeout(() => window.location.href = 'dashboard.html', 1200);
                    }
                }, 1000);
            } else {
                throw new Error(data.message || "Verification failed");
            }
        }
    } catch (err) {
        wrapper.classList.remove('is-animating');
        status.textContent = "SCAN ABORTED / FAILED";
        status.style.color = "var(--accent-red)";
        isScanning = false;
        console.error("Biometric Failure:", err);
        window.showToast(err.message || "Touch sensor to authenticate.", "error");
    }
}

function showToast(message, type) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fa-solid fa-info-circle"></i> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 500);
    }, 3500);
}
window.showToast = showToast;
