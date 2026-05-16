// ============================================================
// auto_verification.js — Background Attendance Service
// ============================================================

const VERIFICATION_INTERVAL = 30 * 60 * 1000; // 30 minutes
let isVerifying = false;

function isWithinSchedule() {
    const now = new Date();
    const hour = now.getHours();
    return (hour >= 9 && hour < 17); // 9:00 AM to 4:59:59 PM
}

function updateScheduleUI() {
    const statusEl = document.getElementById('schedule-status');
    const serviceBadge = document.getElementById('service-status');
    const timerDisplay = document.getElementById('countdown-timer') || document.getElementById('auto-check-timer');
    
    const running = isWithinSchedule();
    
    if (statusEl) {
        statusEl.textContent = running ? "RUNNING" : "STOPPED";
        statusEl.style.color = running ? "var(--accent-cyan)" : "var(--accent-red)";
    }
    
    if (serviceBadge) {
        serviceBadge.textContent = running ? "Service Running" : "Outside Schedule";
        serviceBadge.className = running ? "badge badge-present" : "badge badge-absent";
    }

    if (!running && timerDisplay) {
        timerDisplay.textContent = "--:--";
    }
    
    return running;
}

// ── Background Service Logic ───────────────────────────────
async function runAutoVerification() {
    updateScheduleUI();
    if (!isWithinSchedule()) {
        console.log("[AutoVerify] Outside active schedule (9 AM - 5 PM). Paused.");
        return;
    }
    if (isVerifying) return;
    
    const user = JSON.parse(localStorage.getItem('sat_student') || localStorage.getItem('user') || '{}');
    if (!user || !user.student_id) return;

    const lastCheck = localStorage.getItem('last_auto_verification') || 0;
    const now = Date.now();

    if (now - lastCheck < VERIFICATION_INTERVAL) {
        console.log("[AutoVerify] Next check in:", Math.round((VERIFICATION_INTERVAL - (now - lastCheck))/1000/60), "mins");
        updateCountdownUI(VERIFICATION_INTERVAL - (now - lastCheck));
        return;
    }

    console.log("[AutoVerify] Starting background verification...");
    isVerifying = true;

    try {
        // 1. GPS Verification
        const pos = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true });
        });

        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;

        // 2. Mock Face Check (Silent)
        // For production, we'd use a hidden video capture as implemented before
        const faceVerified = true; 

        // 3. Mark Attendance / Auto-Check
        const token = localStorage.getItem('sat_token');
        const res = await fetch('https://smart-check-production.up.railway.app/api/attendance/auto-mark', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                student_id: user.student_id,
                latitude: lat,
                longitude: lng,
                face_verified: faceVerified
            })
        });
        
        const data = await res.json();
        
        if (data.success) {
            localStorage.setItem('last_auto_verification', Date.now());
            localStorage.setItem('last_auto_status', data.is_inside ? 'inside' : 'outside');
            
            // Notification System
            if (data.is_inside) {
                showToast("Location Verified: Inside Boundary", "success");
            } else {
                showToast("Warning: Outside Campus Boundary!", "warning");
            }
            
            // Dispatch event for UI updates (Dashboard, AutoVerify page)
            window.dispatchEvent(new CustomEvent('autoVerificationComplete', { detail: data }));
        }

    } catch (err) {
        console.error("[AutoVerify] Error:", err);
    } finally {
        isVerifying = false;
    }
}

function updateCountdownUI(ms) {
    const timerEl = document.getElementById('auto-check-timer') || document.getElementById('countdown-timer');
    if (!timerEl) return;
    
    const totalSecs = Math.floor(ms / 1000);
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    timerEl.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
}

function showToast(message, type) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fa-solid ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle'}"></i> <span>${message}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

// ── Initialization ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    if (!isLoggedIn) return;

    console.log("[AutoVerify] Service active");
    
    // Initial run
    runAutoVerification();
    
    // Run background loop check every 1 second for countdown
    setInterval(() => {
        updateScheduleUI();
        if (!isWithinSchedule()) return; // Halt counting/running outside schedule
        
        const lastCheck = parseInt(localStorage.getItem('last_auto_verification') || 0);
        const lastStatus = localStorage.getItem('last_auto_status') || 'inside';
        const now = Date.now();
        const diff = now - lastCheck;
        
        // If last was outside, use a 5-minute interval for grace period re-checks
        // otherwise use the standard 30-minute interval.
        const currentInterval = (lastStatus === 'outside') ? (5 * 60 * 1000) : VERIFICATION_INTERVAL;
        
        if (diff >= currentInterval) {
            runAutoVerification();
        } else {
            updateCountdownUI(currentInterval - diff);
        }
    }, 1000);
});
