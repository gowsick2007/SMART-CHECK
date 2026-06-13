// ============================================================
// dashboard.js — Student Dashboard Logic
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
    startClock();
});

function initDashboard() {
    const user = JSON.parse(localStorage.getItem('sat_student') || localStorage.getItem('user') || '{}');
    if (!user.name) {
        window.location.href = 'login.html';
        return;
    }

    // 1. Update Profile Avatar & Name
    document.getElementById('student-name').textContent = user.name;
    const initial = user.name.charAt(0).toUpperCase();
    const avatarEl = document.getElementById('user-avatar');
    if (avatarEl) avatarEl.textContent = initial;

    // Show Role Label for system tracking
    const role = localStorage.getItem('userRole') || 'student';
    const adminLabel = document.getElementById('admin-label-container');
    if (adminLabel) {
        adminLabel.style.display = 'block';
        if (role === 'creator') {
            adminLabel.innerHTML = `<span style="font-size: 10px; color: #f1c40f; text-transform: uppercase; letter-spacing: 2px; font-weight: 800; background: rgba(241,196,15,0.1); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(241,196,15,0.2);">CREATOR DASHBOARD</span>`;
        } else if (role === 'admin') {
            adminLabel.innerHTML = `<span style="font-size: 10px; color: #00ff88; text-transform: uppercase; letter-spacing: 2px; font-weight: 800; background: rgba(0,255,136,0.1); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(0,255,136,0.2);">ADMIN DASHBOARD</span>`;
        } else {
            adminLabel.innerHTML = `<span style="font-size: 10px; color: #00d2ff; text-transform: uppercase; letter-spacing: 2px; font-weight: 800; background: rgba(0,210,255,0.1); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(0,210,255,0.2);">USER DASHBOARD</span>`;
        }
    }

    // 2. Load Attendance Summary (which then paints real chart data)
    loadAttendanceSummary(user.student_id);

    // 3. Initial Geofence Check (Immediate)
    updateGeofenceUI();
    setInterval(updateGeofenceUI, 10000); // Check every 10s for UI

    // 4. Face Registration Check
    checkFaceRegistration(user.student_id);
}

function startClock() {
    const clockEl = document.getElementById('live-clock');
    const dateEl = document.getElementById('live-date');
    function update() {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        dateEl.textContent = now.toLocaleDateString([], { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    }
    update();
    setInterval(update, 1000);
}

async function loadAttendanceSummary(studentId) {
    const token = localStorage.getItem('sat_token');
    try {
        const res = await fetch(`/api/attendance/weekly-summary?student_id=${studentId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        if (data.success) {
            const pct = data.percentage || 0;
            document.getElementById('total-attendance').textContent = `${pct}%`;
            const progressBar = document.getElementById('attendance-progress');
            if (progressBar) progressBar.style.width = `${pct}%`;
            
            const chartData = (data.summary && data.summary.daily_data) ? data.summary.daily_data : [0,0,0,0,0,0,0];
            initCharts(chartData);
        }
    } catch (err) {
        console.error("Weekly Summary error:", err);
        initCharts([0,0,0,0,0,0,0]); // fallback empty
    }
}

function updateGeofenceUI() {
    if (!navigator.geolocation) return;

    navigator.geolocation.getCurrentPosition(async (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        
        const user = JSON.parse(localStorage.getItem('sat_student') || localStorage.getItem('user') || '{}');
        if(!user.student_id) return;

        const token = localStorage.getItem('sat_token');
        const res = await fetch('/api/attendance/auto-verify/check', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                student_id: user.student_id,
                latitude: lat,
                longitude: lng,
                face_verified: false // Real face verification required via manual scan
            })
        });
        const data = await res.json();
        
        // MANDATORY SYSTEM DEBUG LOGGING
        console.log("ROLE:", localStorage.getItem('userRole') || 'student');
        console.log("DISTANCE:", data.distance);
        console.log("BOUNDARY:", data.is_inside ? "INSIDE" : "OUTSIDE");

        renderGeofenceStatus(data.is_inside, data.distance);

        // Grace timer: backend does not return seconds remaining directly.
        // Compute from localStorage timestamp of when outside state started.
        if (!data.is_inside) {
            const outsideStart = parseInt(localStorage.getItem('outside_start_ts') || 0);
            const now = Date.now();
            if (!outsideStart) {
                localStorage.setItem('outside_start_ts', now);
            }
            const elapsed = Math.floor((now - (outsideStart || now)) / 1000);
            const remaining = Math.max(0, 300 - elapsed); // 5-min grace
            updateGraceTimerUI(remaining, false);
        } else {
            localStorage.removeItem('outside_start_ts');
            updateGraceTimerUI(0, true);
        }
    });
}

async function checkFaceRegistration(studentId) {
    const token = localStorage.getItem('sat_token');
    try {
        const res = await fetch(`/api/face/status/${studentId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        if (data.success && !data.enrolled) {
            // Show registration prompt
            const container = document.querySelector('.main-grid');
            if (container) {
                const prompt = document.createElement('div');
                prompt.className = 'dashboard-card';
                prompt.style.gridColumn = '1 / -1';
                prompt.style.background = 'linear-gradient(135deg, rgba(255, 152, 0, 0.1), rgba(255, 87, 34, 0.1))';
                prompt.style.border = '1px solid rgba(255, 152, 0, 0.3)';
                prompt.innerHTML = `
                    <div style="display:flex; align-items:center; justify-content:between; gap:20px;">
                        <div style="font-size: 30px; color: #ff9800;"><i class="fas fa-user-shield"></i></div>
                        <div style="flex:1;">
                            <h3 style="margin:0; color:#ff9800;">Face Biometrics Required</h3>
                            <p style="margin:5px 0 0; opacity:0.8;">You haven't registered your face data yet. Please complete enrollment to enable automated attendance.</p>
                        </div>
                        <a href="face_verification.html?mode=enroll" class="action-btn" style="background:#ff9800; text-decoration:none; display:inline-block; padding:10px 20px; border-radius:8px; color:white; font-weight:bold;">Register Now</a>
                    </div>
                `;
                container.prepend(prompt);
            }
        }
    } catch (err) {
        console.error("Face status check failed:", err);
    }
}

let graceTicker = null;
function updateGraceTimerUI(secondsRemaining, isInside) {
    const container = document.getElementById('grace-timer-container');
    const display = document.getElementById('grace-countdown');
    if (!container || !display) return;
    
    if (isInside || secondsRemaining <= 0) {
        container.style.display = 'none';
        clearInterval(graceTicker);
        graceTicker = null;
        return;
    }
    
    container.style.display = 'inline-flex';
    
    if (graceTicker) clearInterval(graceTicker);
    
    let current = parseInt(secondsRemaining);
    function refresh() {
        if (current <= 0) {
            display.textContent = "EXPIRED";
            clearInterval(graceTicker);
            return;
        }
        const mm = Math.floor(current / 60).toString().padStart(2, '0');
        const ss = (current % 60).toString().padStart(2, '0');
        display.textContent = `${mm}:${ss}`;
        current--;
    }
    refresh();
    graceTicker = setInterval(refresh, 1000);
}

function renderGeofenceStatus(isInside, distance = 0) {
    const card = document.getElementById('geofence-card');
    const text = document.getElementById('boundaryStatus');
    const subtext = document.getElementById('geofence-subtext');
    const visual = document.getElementById('geofence-visual');
    const icon = document.getElementById('geofence-icon');
    const badge = document.getElementById('boundary-badge');
    const distText = document.getElementById('boundary-distance');
    const glow = document.getElementById('boundary-glow');

    const safeDistance = (typeof distance === 'number' && isFinite(distance)) ? distance : 0;
    distText.textContent = `${safeDistance.toFixed(1)}m`;

    if (isInside) {
        card.style.borderColor = "rgba(0, 255, 204, 0.3)";
        glow.style.background = "radial-gradient(circle at center, var(--accent-cyan), transparent)";
        text.textContent = "INSIDE BOUNDARY";
        text.style.color = "var(--accent-cyan)";
        badge.textContent = "VERIFIED";
        badge.className = "badge green";
        subtext.textContent = "Secure connection active. You are within the 50m campus zone.";
        visual.style.borderColor = "var(--accent-cyan)";
        visual.querySelector('i').style.color = "var(--accent-cyan)";
        icon.style.color = "var(--accent-cyan)";
        icon.className = "fa-solid fa-shield-check";
    } else {
        card.style.borderColor = "rgba(255, 68, 68, 0.3)";
        glow.style.background = "radial-gradient(circle at center, var(--accent-red), transparent)";
        text.textContent = "OUTSIDE BOUNDARY";
        text.style.color = "var(--accent-red)";
        badge.textContent = "OUTSIDE";
        badge.className = "badge red";
        subtext.textContent = "Warning: Attendance cannot be marked. Please move within 50m of boundary.";
        visual.style.borderColor = "var(--accent-red)";
        visual.querySelector('i').style.color = "var(--accent-red)";
        icon.style.color = "var(--accent-red)";
        icon.className = "fa-solid fa-triangle-exclamation";
    }

    // STEP 6 & 7: CRITICAL LOGIC ENFORCEMENT & FORCE UI UPDATE
    const vStatus = document.getElementById('verificationStatus');
    if (vStatus) {
        vStatus.innerText = isInside ? "SUCCESSFUL" : "FAILED";
        vStatus.style.color = isInside ? "var(--accent-green)" : "var(--accent-red)";
    }
    if (text) {
        text.innerText = isInside ? "INSIDE BOUNDARY" : "OUTSIDE BOUNDARY";
    }
}

function initCharts(weeklyPoints) {
    const canvas = document.getElementById('attendanceChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    // Enhanced gradient creation for Glow Style
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(0, 255, 204, 0.35)');
    gradient.addColorStop(1, 'rgba(0, 255, 204, 0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Realtime Presence',
                data: weeklyPoints,
                borderColor: '#00ffcc',
                backgroundColor: gradient,
                borderWidth: 4,
                tension: 0.45,
                fill: true,
                pointBackgroundColor: '#00ffcc',
                pointBorderColor: 'rgba(255,255,255,0.5)',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 8,
                shadowBlur: 15,
                shadowColor: 'rgba(0, 255, 204, 0.6)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 1500,
                easing: 'easeOutQuart'
            },
            plugins: { 
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0d111b',
                    titleColor: '#00ffcc',
                    bodyColor: '#fff',
                    borderColor: 'rgba(0,255,204,0.3)',
                    borderWidth: 1,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y === 100 ? 'Present' : 'Absent / No Record';
                        }
                    }
                }
            },
            scales: {
                y: { 
                    display: false, 
                    min: 0, 
                    max: 120 
                },
                x: { 
                    grid: { display: false }, 
                    ticks: { 
                        color: 'rgba(255,255,255,0.4)',
                        font: { family: "'Inter', sans-serif", weight: '600' } 
                    } 
                }
            }
        }
    });
}

// Listen for auto-verification updates
window.addEventListener('autoVerificationComplete', (e) => {
    const data = e.detail;
    renderGeofenceStatus(data.is_inside, data.distance);
    
    const vStatus = document.getElementById('verificationStatus');
    if(vStatus) {
        vStatus.innerText = data.status.toUpperCase();
        vStatus.style.color = data.status === 'present' ? 'var(--accent-green)' : 'var(--accent-red)';
    }

    // RE-LOAD Percentage from backend after update
    const user = JSON.parse(localStorage.getItem('sat_student') || '{}');
    if (user.student_id) {
        loadAttendanceSummary(user.student_id);
    }
});
