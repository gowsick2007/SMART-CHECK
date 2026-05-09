// ============================================================
// auth.js — Authentication & Session Logic
// ============================================================

const API_BASE = 'http://127.0.0.1:5000';

// ── Toast Notifications ──────────────────────────────────────
function showToast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Login Handler ─────────────────────────────────────────────
async function handleLogin(event) {
  event.preventDefault();
  const identifier = document.getElementById('login-identifier').value.trim();
  const password   = document.getElementById('login-password').value;
  const errEl      = document.getElementById('login-error');
  const btn        = document.getElementById('login-btn');
  const btnText    = document.getElementById('login-btn-text');
  const spinner    = document.getElementById('login-spinner');

  errEl.style.display = 'none';
  btn.disabled = true;
  btnText.textContent = 'Signing in…';
  spinner.style.display = 'inline-block';

  try {
    const res  = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier, password }),
    });
    const data = await res.json();

    if (data.success) {
      localStorage.setItem('sat_token',   data.token);
      localStorage.setItem('sat_student', JSON.stringify(data.student));
      showToast(`Welcome back, ${data.student.name}.`, 'success');
      
      const role = data.student.role || 'student';
      if (role === 'creator') {
        window.location.replace('/creator_dashboard');
      } else if (role === 'admin') {
        window.location.replace('/admin_dashboard');
      } else {
        window.location.replace('/student_dashboard');
      }
    } else {
      errEl.textContent    = data.message || 'Invalid credentials.';
      errEl.style.display  = '';
      btn.disabled         = false;
      btnText.textContent  = 'Sign In';
      spinner.style.display = 'none';
    }
  } catch (e) {
    errEl.textContent   = 'Connection error. Is the server running?';
    errEl.style.display = '';
    btn.disabled        = false;
    btnText.textContent = 'Sign In';
    spinner.style.display = 'none';
  }
}

// ── Register Handler ──────────────────────────────────────────
async function handleRegister(event) {
  event.preventDefault();
  const password = document.getElementById('reg-password').value;
  const confirm  = document.getElementById('reg-confirm').value;
  const errEl    = document.getElementById('reg-error');
  const btn      = document.getElementById('reg-btn');
  const btnText  = document.getElementById('reg-btn-text');
  const spinner  = document.getElementById('reg-spinner');

  errEl.style.display = 'none';

  if (password !== confirm) {
    errEl.textContent = 'Passwords do not match.';
    errEl.style.display = '';
    return;
  }

  const payload = {
    student_id:    document.getElementById('reg-student-id').value.trim(),
    name:          document.getElementById('reg-name').value.trim(),
    email:         document.getElementById('reg-email').value.trim(),
    phone:         document.getElementById('reg-phone')?.value.trim() || '',
    department:    document.getElementById('reg-dept').value,
    year:          document.getElementById('reg-year').value,          // e.g. "I Year"
    class_section: document.getElementById('reg-class-section').value, // e.g. "Section A"
    password,
  };

  btn.disabled  = true;
  btnText.textContent  = 'Creating account…';
  spinner.style.display = 'inline-block';

  try {
    const res  = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.success) {
      showToast('Account created. Please log in.', 'success');
      setTimeout(() => { window.location.href = '/'; }, 1000);
    } else {
      errEl.textContent    = data.message || 'Registration failed.';
      errEl.style.display  = '';
      btn.disabled         = false;
      btnText.textContent  = 'Create Account';
      spinner.style.display = 'none';
    }
  } catch (e) {
    errEl.textContent   = 'Connection error. Is the server running?';
    errEl.style.display = '';
    btn.disabled        = false;
    btnText.textContent = 'Create Account';
    spinner.style.display = 'none';
  }
}

// ── Logout Handler ────────────────────────────────────────────
async function handleLogout() {
  const token = localStorage.getItem('sat_token');
  if (token) {
    try {
      await fetch(`${API_BASE}/api/auth/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
    } catch (e) {}
  }
  localStorage.removeItem('sat_token');
  localStorage.removeItem('sat_student');
  window.location.href = '/';
}

// ── Get stored student ────────────────────────────────────────
function getStoredStudent() {
  try { return JSON.parse(localStorage.getItem('sat_student')); } catch(e) { return null; }
}

// ── Guard: redirect if not logged in ─────────────────────────
function requireAuth() {
  if (!localStorage.getItem('sat_token')) {
    window.location.href = '/';
    return false;
  }
  return true;
}

// Removed inline GPS check since it's now handled by the dashboard overlay
