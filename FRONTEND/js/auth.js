// ============================================================
// auth.js — Authentication & Session Logic
// ============================================================

const API_BASE = '';

// ── Themed Modal & Toast System ─────────────────────────────────

window.showSuccessToast = function(message, duration = 3500) {
  _createAndShowToast(message, 'success', '#00ffcc', 'fa-check-circle');
};

window.showErrorToast = function(message, duration = 3500) {
  _createAndShowToast(message, 'error', '#ff4d4d', 'fa-times-circle');
};

window.showWarningToast = function(message, duration = 3500) {
  _createAndShowToast(message, 'warning', '#ff9f43', 'fa-exclamation-triangle');
};

window.showToast = function(message, type = 'info', duration = 3500) {
  if (type === 'error') showErrorToast(message, duration);
  else if (type === 'warning') showWarningToast(message, duration);
  else showSuccessToast(message, duration);
};

function _createAndShowToast(message, type, color, iconClass) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.style.cssText = `
    background: rgba(10, 15, 30, 0.95);
    border: 1px solid ${color};
    border-left: 4px solid ${color};
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    backdrop-filter: blur(8px);
    color: #fff;
    padding: 16px 24px;
    border-radius: 8px;
    margin-top: 10px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    transform: translateX(120%);
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.3s ease;
    opacity: 0;
  `;
  toast.innerHTML = `<i class="fas ${iconClass}" style="color:${color}; font-size:1.2rem;"></i><span>${message}</span>`;
  container.appendChild(toast);
  
  // Animate in
  requestAnimationFrame(() => {
    toast.style.transform = 'translateX(0)';
    toast.style.opacity = '1';
  });

  setTimeout(() => {
    toast.style.transform = 'translateX(120%)';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ── Login Handler ─────────────────────────────────────────────
async function handleLogin(event) {
  event.preventDefault();
  const identifier = document.getElementById('login-identifier').value.trim();
  const password = document.getElementById('login-password').value;
  const errEl = document.getElementById('login-error');
  const btn = document.getElementById('login-btn');
  const btnText = document.getElementById('login-btn-text');
  const spinner = document.getElementById('login-spinner');

  errEl.style.display = 'none';
  btn.disabled = true;
  btnText.textContent = 'Signing in…';
  spinner.style.display = 'inline-block';

  try {
    let fetchUrl = `${API_BASE}/api/auth/login`;
    const roleVal = document.getElementById('login-role').value;
    let bodyData = { identifier, password };

    if (roleVal === 'admin') {
      if (identifier === 'gowsicklitheswaran@gmail.com') {
        fetchUrl = `${API_BASE}/api/auth/creator/login`;
        bodyData = { email: identifier, password: password };
      } else {
        fetchUrl = `${API_BASE}/api/auth/admin/login`;
      }
    }

    const res = await fetch(fetchUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyData),
    });
    const data = await res.json();

    if (data.success) {
      let actualRole = data.role || (data.student && data.student.role) || (data.user && data.user.role) || 'student';
      if (identifier === 'gowsicklitheswaran@gmail.com') actualRole = 'creator';

      console.log("Logged role:", actualRole);

      const userObj = data.student || data.user || {};

      localStorage.setItem('sat_token', data.token);
      localStorage.setItem('sat_student', JSON.stringify(userObj));
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(userObj));
      localStorage.setItem('userEmail', userObj.email || identifier);
      localStorage.setItem('userRole', actualRole);
      localStorage.setItem('isLoggedIn', 'true');

      // Required explicitly in Session storage
      sessionStorage.setItem("role", actualRole);

      showToast(`Welcome back.`, 'success');

      // Clear locationVerified on fresh login to force check
      localStorage.removeItem('locationVerified');

      // Role-based redirection using absolute, cleaner URL endpoints
      if (actualRole === 'creator' || actualRole === 'admin') {
        console.log("Redirecting Admin/Creator to Location Setup:", "/location");
        window.location.href = '/location';
      } else {
        console.log("Redirecting Student to Dashboard:", "/dashboard");
        window.location.href = '/dashboard';
      }
    } else {
      errEl.textContent = data.message || 'Invalid credentials';
      errEl.style.display = '';
      btn.disabled = false;
      btnText.textContent = 'Sign In';
      spinner.style.display = 'none';
    }
  } catch (e) {
    console.error("Route error:", e);
    errEl.textContent = 'Server connection failed';
    errEl.style.display = '';
    btn.disabled = false;
    btnText.textContent = 'Sign In';
    spinner.style.display = 'none';
  }
}

// ── Registration Handler ─────────────────────────────────────
async function handleRegister(event) {
  event.preventDefault();

  const errEl = document.getElementById('reg-error');
  const btn = document.getElementById('reg-btn');
  const btnText = document.getElementById('reg-btn-text');
  const spinner = document.getElementById('reg-spinner');

  if (errEl) {
    errEl.style.display = 'none';
    errEl.className = 'alert alert-error';
  }

  const name = document.getElementById('reg-name').value.trim();
  const student_id = document.getElementById('reg-student-id').value.trim();
  const email = document.getElementById('reg-email').value.trim().toLowerCase();
  const phone = document.getElementById('reg-phone').value.trim();
  const department = document.getElementById('reg-dept').value;
  const year = document.getElementById('reg-year').value;
  const class_section = document.getElementById('reg-class-section').value;
  const password = document.getElementById('reg-password').value;
  const confirmPass = document.getElementById('reg-confirm').value;

  if (!name || !student_id || !email || !password) {
    if (errEl) { errEl.textContent = 'All required fields must be filled.'; errEl.style.display = 'block'; }
    return;
  }

  if (password !== confirmPass) {
    if (errEl) { errEl.textContent = 'Passwords do not match.'; errEl.style.display = 'block'; }
    return;
  }

  btn.disabled = true;
  if (btnText) btnText.textContent = 'Creating Account...';
  if (spinner) spinner.style.display = 'inline-block';

  try {
    const resp = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, student_id, email, phone, department, year, class_section, password })
    });
    const data = await resp.json();

    if (data.success) {
      if (errEl) {
        errEl.textContent = 'Account created successfully.';
        errEl.className = 'alert alert-success';
        errEl.style.display = 'block';
      }
      if (btnText) btnText.textContent = 'SUCCESS!';
      if (spinner) spinner.style.display = 'none';

      setTimeout(() => {
        window.location.href = 'login.html';
      }, 2000);
    } else {
      if (errEl) {
        errEl.textContent = data.message || 'Registration failed.';
        errEl.style.display = 'block';
      }
      btn.disabled = false;
      if (btnText) btnText.textContent = 'CREATE ACCOUNT';
      if (spinner) spinner.style.display = 'none';
    }
  } catch (e) {
    console.error("Reg failed:", e);
    if (errEl) { errEl.textContent = 'Connection error.'; errEl.style.display = 'block'; }
    btn.disabled = false;
    if (btnText) btnText.textContent = 'CREATE ACCOUNT';
    if (spinner) spinner.style.display = 'none';
  }
}

window.addEventListener('pageshow', (event) => {
  const btn = document.getElementById('login-btn');
  const btnText = document.getElementById('login-btn-text');
  const spinner = document.getElementById('login-spinner');

  if (btn && btnText && spinner) {
    btn.disabled = false;
    btnText.textContent = 'Sign In';
    spinner.style.display = 'none';
  }
});

// ── Guard: redirect if not logged in ─────────────────────────
function requireAuth() {
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  const locationVerified = localStorage.getItem('locationVerified') === 'true';
  const path = window.location.pathname;

  // LOGIN PAGE RULE
  if (path.includes("login.html") || path === "/" || path === "/login") {
    // DO NOT AUTO REDIRECT FROM LOGIN PAGE - USER REQUIREMENT
    return true;
  }

  // DASHBOARD PAGE RULE (and other protected pages - supporting extensionless server routes)
  const isDashboard = path.includes("dashboard") || path.includes("location") || path.includes("face-scan") || path.includes("verification");
  if (isDashboard) {
    if (!isLoggedIn) {
      window.location.href = "login.html";
      return false;
    }

    // Protect Dashboard from access before location verification (Admin Only)
    const userRole = localStorage.getItem('userRole') || sessionStorage.getItem('role') || 'student';
    if ((userRole === 'admin' || userRole === 'creator') && (path.includes("/dashboard") || path === "/dashboard.html") && !locationVerified) {
      console.log("Guard redirect: Admin has not verified/set location yet.");
      window.location.href = "/location";
      return false;
    }

    return true;
  }

  return true;
}

// ── Logout Handler ────────────────────────────────────────────
async function handleLogout() {
  const token = localStorage.getItem('sat_token') || localStorage.getItem('token');
  if (token) {
    try {
      await fetch(`${API_BASE}/api/auth/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
    } catch (e) { }
  }

  // Clear session safely - maintain boundary state if needed, but per request clear session
  localStorage.removeItem('sat_token');
  localStorage.removeItem('sat_student');
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('isLoggedIn');
  localStorage.removeItem('locationVerified');
  sessionStorage.clear();

  window.location.href = 'login.html';
}

function getStoredStudent() {
  try { return JSON.parse(localStorage.getItem('sat_student')); } catch (e) { return null; }
}

// Initial check on script load
requireAuth();

// ── Sidebar Dynamic Rendering ──────────────────────────────────
async function renderSidebarFeatures() {
  const navMenu = document.querySelector('.nav-menu');
  if (!navMenu) return;

  // Avoid duplicate rendering
  if (document.getElementById('nav-fingerprint') || document.getElementById('nav-face-scan')) {
    return;
  }

  try {
    const [faceRes, fpRes] = await Promise.all([
      fetch(`${API_BASE}/api/system/face-config`),
      fetch(`${API_BASE}/api/system/fingerprint-config`)
    ]);
    const faceData = await faceRes.json();
    const fpData = await fpRes.json();

    const pathname = window.location.pathname;
    const currentPage = pathname.substring(pathname.lastIndexOf('/') + 1) || 'dashboard.html';

    const dashboardLink = navMenu.querySelector('a[href="dashboard.html"]');

    // Render Fingerprint if enabled
    if (fpData && fpData.success && fpData.enabled) {
      const fpLink = document.createElement('a');
      fpLink.href = 'fingerprint.html';
      fpLink.id = 'nav-fingerprint';
      fpLink.className = `nav-link ${currentPage === 'fingerprint.html' ? 'active' : ''}`;
      fpLink.innerHTML = '<i class="fa-solid fa-fingerprint"></i><span>Fingerprint</span>';
      if (dashboardLink) dashboardLink.after(fpLink);
      else navMenu.prepend(fpLink);
    }

    // Render Face if enabled
    if (faceData && faceData.success && faceData.enabled) {
      const faceLink = document.createElement('a');
      faceLink.href = 'face_verification.html';
      faceLink.id = 'nav-face-scan';
      faceLink.className = `nav-link ${currentPage === 'face_verification.html' ? 'active' : ''}`;
      faceLink.innerHTML = '<i class="fa-solid fa-face-viewfinder"></i><span>Face Verification</span>';

      const fpLink = document.getElementById('nav-fingerprint');
      if (fpLink) fpLink.after(faceLink);
      else if (dashboardLink) dashboardLink.after(faceLink);
      else navMenu.prepend(faceLink);
    }
  } catch (e) {
    console.error("Sidebar dynamic render failed:", e);
  }
}

document.addEventListener('DOMContentLoaded', renderSidebarFeatures);

// ── Custom Modals ─────────────────────────────────────────────
window.showConfirmModal = function(title, msg) {
  return new Promise(resolve => {
    let m = document.getElementById('global-confirm-modal');
    if(!m) {
      document.body.insertAdjacentHTML('beforeend', `
        <div id="global-confirm-modal" style="position:fixed; inset:0; background:rgba(0,0,0,0.65); backdrop-filter:blur(10px); z-index:10000; display:none; align-items:center; justify-content:center; opacity:0; transition:opacity 0.2s;">
          <div id="global-confirm-card" style="background:linear-gradient(145deg, rgba(20,25,40,0.9), rgba(10,15,30,0.95)); border:1px solid rgba(0,255,204,0.2); border-radius:16px; padding:32px; min-width:340px; max-width:90vw; text-align:center; box-shadow:0 15px 40px rgba(0,0,0,0.5), 0 0 20px rgba(0,255,204,0.1); transform:scale(0.9); transition:transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);">
            <div style="font-size:2.5rem; color:#00ffcc; margin-bottom:15px;"><i class="fas fa-question-circle"></i></div>
            <h3 id="global-confirm-title" style="margin:0 0 12px; color:#fff; font-family:'Outfit', sans-serif; font-size:1.4rem; font-weight:700; letter-spacing:0.5px;">Confirm Action</h3>
            <p id="global-confirm-msg" style="color:rgba(255,255,255,0.7); margin-bottom:28px; line-height:1.6; font-size:1rem;"></p>
            <div style="display:flex; gap:12px; justify-content:center;">
              <button id="global-confirm-cancel" style="flex:1; padding:12px 24px; background:transparent; border:1px solid rgba(255,255,255,0.2); color:#fff; border-radius:8px; cursor:pointer; font-weight:600; transition:all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.05)'" onmouseout="this.style.background='transparent'">Cancel</button>
              <button id="global-confirm-ok" style="flex:1; padding:12px 24px; background:linear-gradient(45deg, #00ffcc, #0099ff); border:none; color:#000; border-radius:8px; cursor:pointer; font-weight:700; box-shadow:0 4px 15px rgba(0,255,204,0.3); transition:transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">Confirm</button>
            </div>
          </div>
        </div>
      `);
      m = document.getElementById('global-confirm-modal');
    }
    document.getElementById('global-confirm-title').textContent = title || "Confirm Action";
    document.getElementById('global-confirm-msg').textContent = msg;
    
    m.style.display = 'flex';
    // Animate in
    requestAnimationFrame(() => {
        m.style.opacity = '1';
        document.getElementById('global-confirm-card').style.transform = 'scale(1)';
    });

    const close = (result) => {
        m.style.opacity = '0';
        document.getElementById('global-confirm-card').style.transform = 'scale(0.9)';
        setTimeout(() => {
            m.style.display = 'none';
            resolve(result);
        }, 200);
    };

    document.getElementById('global-confirm-cancel').onclick = () => close(false);
    document.getElementById('global-confirm-ok').onclick = () => close(true);
  });
};
