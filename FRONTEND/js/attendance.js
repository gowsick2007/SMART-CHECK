// ============================================================
// attendance.js — Dashboard Orchestration & Attendance Marking
// ============================================================

const API = 'http://127.0.0.1:5000';
let currentStudent = null;
let gpsResult      = null;

// ── Init Dashboard ────────────────────────────────────────────
(async function initDashboard() {
  if (!requireAuth()) return;

  // Start clock
  updateClock();
  setInterval(updateClock, 1000);

  // Load student profile
  await loadStudentProfile();

  // Load stats
  await loadAttendanceSummary();

  // Check if attendance already marked today
  await checkTodayAttendance();

  // Make sure face scanner is hidden on load
  document.getElementById('face-verification-section').style.display = 'none';

  // Wait for user to click Enable Location Access
  // The GPS Overlay is visible by default
})();

// ── Request GPS Access (Called by overlay button) ─────────────
async function requestGpsAccess() {
  const btn = document.getElementById('enable-gps-btn');
  const errEl = document.getElementById('gps-perm-error');
  
  if (btn) { btn.disabled = true; btn.textContent = 'Requesting...'; }
  if (errEl) errEl.style.display = 'none';

  if (!navigator.geolocation) {
    if (errEl) { errEl.textContent = 'Geolocation is not supported by your browser.'; errEl.style.display = 'block'; }
    return;
  }

  try {
    const pos = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 });
    });
    
    // Permission granted! Hide overlay, show dashboard content
    const overlay = document.getElementById('gps-permission-overlay');
    const content = document.getElementById('dashboard-content');
    if (overlay) overlay.style.display = 'none';
    if (content) content.style.display = 'block';

    // Start continuous GPS watch
    startLocationWatch((pos, result) => {
      gpsResult = result;
      // Note: Face enrollment check not needed on dashboard for marking flow
    });
  } catch (err) {
    if (btn) { btn.disabled = false; btn.textContent = 'Enable Location Access'; }
    if (errEl) errEl.style.display = 'block';
  }
}

// ── Clock ─────────────────────────────────────────────────────
function updateClock() {
  const now  = new Date();
  const timeEl = document.getElementById('clock');
  const dateEl = document.getElementById('date-display');
  if (timeEl) {
    timeEl.textContent = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
  }
  if (dateEl) {
    dateEl.textContent = now.toLocaleDateString('en-IN', { weekday:'long', day:'2-digit', month:'long', year:'numeric' });
  }
}

// ── Load profile ──────────────────────────────────────────────
async function loadStudentProfile() {
  const token = localStorage.getItem('sat_token');
  try {
    const res  = await fetch(`${API}/api/student/profile`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    if (!data.success) { handleLogout(); return; }

    currentStudent = data.student;
    const s = currentStudent;

    // Set avatar initial
    const initial = s.name[0].toUpperCase();
    const avatarEl = document.getElementById('student-avatar');
    const navAvatarEl = document.getElementById('nav-avatar');
    if (avatarEl)    avatarEl.textContent    = initial;
    if (navAvatarEl) navAvatarEl.textContent = initial;

    if (document.getElementById('student-name'))
      document.getElementById('student-name').textContent = s.name;
    if (document.getElementById('student-meta'))
      document.getElementById('student-meta').textContent = `${s.student_id} • ${s.department} • ${s.class_name}`;

    // Update face-enrolled check
    const checkFaceEl = document.getElementById('check-face-enrolled');
    if (checkFaceEl) {
      if (s.face_enrolled) {
        checkFaceEl.textContent = 'Enrolled';
        checkFaceEl.className   = 'check-status check-ok';
      } else {
        checkFaceEl.textContent = 'Not enrolled';
        checkFaceEl.className   = 'check-status check-fail';
      }
    }
  } catch(e) { console.error('Profile load failed', e); }
}

// ── Check face enrollment ─────────────────────────────────────
async function checkFaceEnrolled() {
  if (!currentStudent) return;
  const checkFaceEl = document.getElementById('check-face-enrolled');
  if (currentStudent.face_enrolled) {
    if (checkFaceEl) { checkFaceEl.textContent = 'Enrolled'; checkFaceEl.className = 'check-status check-ok'; }
  } else {
    if (checkFaceEl) { checkFaceEl.textContent = 'Not enrolled'; checkFaceEl.className = 'check-status check-fail'; }
  }
}

// ── Load attendance summary stats ─────────────────────────────
async function loadAttendanceSummary() {
  const token = localStorage.getItem('sat_token');
  try {
    const res  = await fetch(`${API}/api/attendance/summary`, { headers: { 'Authorization': `Bearer ${token}` } });
    const data = await res.json();
    if (data.success && data.summary) {
      const s = data.summary;
      document.getElementById('stat-total')  && (document.getElementById('stat-total').textContent  = s.total || 0);
      document.getElementById('stat-present')&& (document.getElementById('stat-present').textContent = s.present_count || 0);
      document.getElementById('stat-late')   && (document.getElementById('stat-late').textContent    = s.late_count || 0);
      document.getElementById('stat-absent') && (document.getElementById('stat-absent').textContent  = s.absent_count || 0);

      const pct = s.total ? Math.round((s.present_count + s.late_count) / s.total * 100) : 0;
      const pctEl = document.getElementById('attend-pct');
      const barEl = document.getElementById('attend-bar');
      if (pctEl) pctEl.textContent = pct + '%';
      if (barEl) { setTimeout(() => barEl.style.width = pct + '%', 200); }
    }
  } catch(e) { console.error('Summary load failed', e); }
}

// ── Check if already marked today ────────────────────────────
async function checkTodayAttendance() {
  const token = localStorage.getItem('sat_token');
  try {
    const res  = await fetch(`${API}/api/attendance/history?limit=1`, { headers: { 'Authorization': `Bearer ${token}` } });
    const data = await res.json();
    if (!data.success || !data.records.length) return;

    const today  = new Date().toISOString().split('T')[0];
    const latest = data.records[0];
    if (latest.date && latest.date.toString().startsWith(today)) {
      const badgeEl = document.getElementById('today-badge');
      const markBtn = document.getElementById('mark-btn');
      const statusClass = latest.status === 'present' ? 'badge-present' : latest.status === 'late' ? 'badge-late' : 'badge-absent';
      if (badgeEl) badgeEl.innerHTML = `<span class="badge ${statusClass}">Today: ${latest.status.toUpperCase()}</span>`;
      if (markBtn) {
        markBtn.disabled = true;
        document.getElementById('mark-btn-text').textContent = 'Already Marked Today';
      }
    }
  } catch(e) {}
}

// ── Load students (filter dropdown) ───────────────────────────
async function loadStudents() {
  const dept  = document.getElementById('dept-filter')?.value || '';
  const cls   = document.getElementById('class-filter')?.value || '';
  const token = localStorage.getItem('sat_token');
  const params = new URLSearchParams();
  if (dept) params.set('department', dept);
  if (cls)  params.set('class_name', cls);

  try {
    const res  = await fetch(`${API}/api/student/all?${params}`, { headers: { 'Authorization': `Bearer ${token}` } });
    const data = await res.json();
    if (data.success) {
      console.log(`Loaded ${data.count} students`);
    }
  } catch(e) {}
}

// ── Mark Attendance ───────────────────────────────────────────
async function markAttendance() {
  const token    = localStorage.getItem('sat_token');
  const markBtn  = document.getElementById('mark-btn') || document.getElementById('action-btn');
  const btnText  = document.getElementById('mark-btn-text') || markBtn;
  const spinner  = document.getElementById('mark-spinner');
  const resultEl = document.getElementById('mark-result');

  if (!isFaceDetected()) {
    showToast('No face detected. Please look at the camera.', 'error');
    return;
  }

  const descriptor = getLastDescriptor();
  if (!descriptor || descriptor.length !== 128) {
    showToast('Face descriptor not ready. Please wait…', 'error');
    return;
  }

  const pos = getCurrentPosition();
  if (!pos) {
    showToast('GPS location not available. Please ensure location is enabled and verified on the Dashboard.', 'error');
    return;
  }

  if (markBtn) markBtn.disabled = true;
  if (btnText) btnText.textContent = 'Processing…';
  if (spinner) spinner.style.display = 'inline-block';
  if (resultEl) resultEl.style.display = 'none';

  try {
    const res  = await fetch(`${API}/api/attendance/mark`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({
        latitude:        pos.lat,
        longitude:       pos.lon,
        face_descriptor: descriptor,
        college_lat:     COLLEGE ? COLLEGE.lat : undefined,
        college_lon:     COLLEGE ? COLLEGE.lon : undefined
      }),
    });
    const data = await res.json();

    if (resultEl) resultEl.style.display = 'block';
    if (data.success) {
      if (resultEl) { resultEl.className = 'alert alert-success'; resultEl.textContent = data.message; }
      showToast(data.message, 'success', 5000);
      if (btnText) btnText.textContent = 'Attendance Marked!';
      await loadAttendanceSummary();
      await checkTodayAttendance();
    } else if (data.already_marked) {
      if (resultEl) { resultEl.className = 'alert alert-info'; resultEl.textContent = data.message; }
      showToast(data.message, 'info');
      if (btnText) btnText.textContent = 'Already Marked';
    } else {
      if (resultEl) { resultEl.className = 'alert alert-error'; resultEl.textContent = data.message; }
      showToast(data.message, 'error', 5000);
      if (markBtn) markBtn.disabled = false;
      if (btnText) btnText.textContent = 'Mark Attendance';
    }
  } catch (e) {
    if (resultEl) { resultEl.style.display = 'block'; resultEl.className = 'alert alert-error'; resultEl.textContent = 'Connection error. Please check server.'; }
    if (markBtn) markBtn.disabled = false;
    if (btnText) btnText.textContent = 'Mark Attendance';
  } finally {
    if (spinner) spinner.style.display = 'none';
  }
}

// ── Flow Handlers ─────────────────────────────────────────────
function proceedToFaceScan() {
  window.location.href = '/face-scan';
}

function backToGps() {
  window.location.href = '/dashboard';
}

function runAutoCheck() {
  navigator.geolocation.getCurrentPosition(function(pos) {
    const lat = pos.coords.latitude;
    const lng = pos.coords.longitude;
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const storedStudent = JSON.parse(localStorage.getItem('sat_student') || '{}');
    const studentId = user.student_id || storedStudent.student_id;
    if (!studentId) return;

    fetch('/api/attendance/auto-verify/check', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + localStorage.getItem('sat_token') 
      },
      body: JSON.stringify({
        student_id: studentId,
        latitude: lat,
        longitude: lng,
        face_verified: true
      })
    })
    .then(r => r.json())
    .then(data => {
      console.log('[AutoCheck]', data.status, new Date().toLocaleTimeString());
    })
    .catch(e => console.error('[AutoCheck Error]', e));
  }, function(err) {
    console.warn('[AutoCheck] Location denied:', err.message);
  });
}

// Start auto check immediately and every 30 minutes
runAutoCheck();
setInterval(runAutoCheck, 1800000);

