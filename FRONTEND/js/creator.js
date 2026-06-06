// ============================================================
// creator.js — Creator (Super Admin) Full Control Logic
// All buttons call real backend APIs. No dummy UI.
// ============================================================

console.log("JS Loaded");
// const API_BASE is already defined in auth.js and available globally
// var API_BASE = (typeof API_BASE !== 'undefined') ? API_BASE : 'http://127.0.0.1:5000';

// Cached data
let _allUsers = [];
let _creatorBoundaryData = [];
let _currentModalAction = null;

// ── Helpers ───────────────────────────────────────────────────

function getToken() {
    return localStorage.getItem('sat_token') || localStorage.getItem('token') || '';
}

function authHeaders(extra = {}) {
    return {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json',
        ...extra
    };
}



async function openModal(title, body, onConfirm) {
    if (await showConfirmModal(title, body)) {
        onConfirm();
    }
}
window.openModal = openModal;

function showLoading(el) {
    if (el) el.innerHTML = "Loading...";
}
function hideLoading(el) {
    if (el) el.innerHTML = "";
}

// ── Section navigation ────────────────────────────────────────

document.addEventListener("DOMContentLoaded", function () {
  // Side menu interaction
  document.querySelectorAll("[data-section]").forEach(btn => {
    btn.addEventListener("click", function () {
      const section = this.getAttribute("data-section");
      console.log("CLICKED:", section);

      document.querySelectorAll(".dashboard-section").forEach(sec => {
        sec.style.display = "none";
      });

      const target = document.getElementById(section);
      if (target) {
        target.style.display = "block";
        loadSectionData(section);
      } else {
        console.error("Section NOT FOUND:", section);
        console.log("Available IDs:", Array.from(document.querySelectorAll('.dashboard-section')).map(e=>e.id));
      }

      document.querySelectorAll(".sidebar-item").forEach(item => {
        item.classList.remove("active");
      });

      this.classList.add("active");
    });
  });

  // Refresh button interaction
  const refBtn = document.getElementById("refreshBtn");
  if (refBtn) {
      refBtn.addEventListener("click", function () {
          console.log("Refresh clicked");
          const activeSection = document.querySelector(".dashboard-section:not([style*='display: none'])");
          if (activeSection) {
              console.log("Refreshing section:", activeSection.id);
              loadSectionData(activeSection.id);
          }
      });
  }

  // Restore logic for header user name
  try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const el = document.getElementById('creator-name');
      if (el && user.name) el.textContent = user.name;
  } catch (_) {}

  // Initial load default
  loadSectionData("overview");
});

function loadSectionData(id) {
    console.log("Loading data for:", id);
    
    if (id === "overview") {
        if (typeof loadSystemStats === 'function') loadSystemStats();
        if (typeof loadRecentLogins === 'function') loadRecentLogins();
        if (typeof fetchFaceSetting === 'function') fetchFaceSetting();
        fetchFingerprintSetting();
    } else if (id === "user-management") {
        if (typeof loadAllUsers === 'function') loadAllUsers();
    } else if (id === "admin-control") {
        if (typeof loadAdminSection === 'function') loadAdminSection();
    } else if (id === "boundary-check") {
        if (typeof loadCreatorBoundary === 'function') loadCreatorBoundary();
    } else if (id === "attendance-logs") {
        if (typeof loadAttendance === 'function') loadAttendance();
    } else if (id === "activity-logs") {
        if (typeof loadRecentLogins === 'function') loadRecentLogins();
    }

    // Update last refreshed paragraph
    const el = document.getElementById('last-refresh');
    if (el) {
        el.innerHTML = 'Last refreshed: ' + new Date().toLocaleTimeString();
    }
}

// ── 1. System Stats ───────────────────────────────────────────

async function loadSystemStats() {
    try {
        const res = await fetch(`${API_BASE}/api/creator/system-stats`, { headers: authHeaders() });
        const data = await res.json();
                console.log("API Response:", data);
        console.log("Data Loaded:", data);
        if (!data.success) return;
        const s = data.stats;

        setText('s-total',      s.total_users);
        setText('s-admins',     s.total_admins);
        setText('s-active',     s.active_users);
        setText('s-disabled',   s.disabled_users);
        setText('s-present',    s.today_present);
        setText('s-absent',     s.today_absent);
        setText('s-violations', s.boundary_violations);
        setText('att-present',  s.today_present);
        setText('att-absent',   s.today_absent);
    } catch (err) {
        console.error('Stats load error:', err);
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = (val !== undefined && val !== null) ? val : '—';
}

// ── 2. All Users ──────────────────────────────────────────────

async function loadAllUsers() {
    const container = document.getElementById('user-list');
    if (container) container.innerHTML = `<tr><td colspan="7" class="empty-state"><i class="fas fa-spinner fa-spin"></i> Loading users...</td></tr>`;
    
    try {
        const dept = document.getElementById('user-dept-filter')?.value || '';
        const section = document.getElementById('user-section-filter')?.value || '';
        const sort = document.getElementById('user-sort-filter')?.value || 'A-Z';
        
        const params = new URLSearchParams();
        if (dept) params.append('department', dept);
        if (section) params.append('section', section);
        if (sort) params.append('sort', sort);
        
        const url = `${API_BASE}/api/creator/users${params.toString() ? '?' + params.toString() : ''}`;
        const res = await fetch(url, { headers: authHeaders() });
        const data = await res.json();
                console.log("API Response:", data);
        console.log("Data Loaded:", data);
        if (!data.success) {
            if (container) container.innerHTML = `<tr><td colspan="7" class="empty-state"><i class="fas fa-exclamation-triangle"></i> Failed to load users</td></tr>`;
            return;
        }
        _allUsers = data.users;
        renderUserTable(_allUsers);
        populateGrantSelect(_allUsers);
    } catch (err) {
        console.error('Load users error:', err);
        if (container) container.innerHTML = `<tr><td colspan="7" class="empty-state"><i class="fas fa-wifi"></i> Network error loading users</td></tr>`;
    }
}

function renderUserTable(users) {
    const container = document.getElementById('user-list');
    if (!container) return;

    if (!users || users.length === 0) {
        container.innerHTML = `<tr><td colspan="6" class="empty-state"><i class="fas fa-users"></i> No users found</td></tr>`;
        return;
    }

    container.innerHTML = users.map(u => {
        const isCreator = u.role === 'creator';
        const isAdmin   = u.role === 'admin';
        const isActive  = u.is_active === 1 || u.is_active === true;
        const lastLogin = u.last_login ? new Date(u.last_login).toLocaleString() : 'Never';

        let roleClass = 'role-student';
        if (isAdmin)   roleClass = 'role-admin';
        if (isCreator) roleClass = 'role-creator';

        const statusHtml = isActive
            ? `<span class="status-dot dot-active"></span>Active`
            : `<span class="status-dot dot-disabled"></span>Disabled`;

        let actions;
        if (isCreator) {
            actions = `<span style="opacity:0.4; font-size:13px;">System Owner</span>`;
        } else {
            const roleBtn = isAdmin
                ? `<button class="act-btn btn-remove-admin" onclick="doRemoveAdmin('${u.student_id}','${escStr(u.name)}')">Remove Admin</button>`
                : `<button class="act-btn btn-make-admin"   onclick="doMakeAdmin('${u.student_id}','${escStr(u.name)}')">Make Admin</button>`;
            const statusBtn = isActive
                ? `<button class="act-btn btn-disable" onclick="doDisableUser('${u.student_id}','${escStr(u.name)}')">Disable</button>`
                : `<button class="act-btn btn-enable"  onclick="doEnableUser('${u.student_id}','${escStr(u.name)}')">Enable</button>`;
            const removeBtn = `<button class="act-btn btn-remove-user" onclick="doRemoveUser('${u.student_id}','${escStr(u.name)}')">Remove User</button>`;
            const detailBtn = `<button class="act-btn btn-details" onclick="viewDetails('${u.student_id}','${escStr(u.name)}','${u.email}','${u.role}','${isActive}','${lastLogin}')">Details</button>`;
            actions = `<div style="display:flex;flex-wrap:wrap;gap:4px;">${roleBtn}${statusBtn}${removeBtn}${detailBtn}</div>`;
        }

        return `
        <tr data-name="${u.name.toLowerCase()}" data-email="${u.email.toLowerCase()}" data-sid="${u.student_id.toLowerCase()}" data-role="${u.role}" data-status="${isActive ? 'active' : 'disabled'}">
            <td>
                <div style="font-weight:700;">${u.name}</div>
                <div style="font-size:11px;opacity:0.5;">${u.student_id}</div>
            </td>
            <td style="opacity:0.75;">${u.email}</td>
            <td style="opacity:0.75;">${u.department || '—'}</td>
            <td><span class="role-badge ${roleClass}">${u.role.toUpperCase()}</span></td>
            <td>${statusHtml}</td>
            <td>${actions}</td>
        </tr>`;
    }).join('');
}

function filterUserTable() {
    const q      = (document.getElementById('user-search')?.value || '').toLowerCase();
    const role   = (document.getElementById('user-role-filter')?.value || '').toLowerCase();
    const status = (document.getElementById('user-status-filter')?.value || '').toLowerCase();

    document.querySelectorAll('#user-list tr[data-name]').forEach(row => {
        const nameMatch  = !q || row.dataset.name.includes(q) || row.dataset.email.includes(q) || row.dataset.sid.includes(q);
        const roleMatch  = !role   || row.dataset.role === role;
        const statMatch  = !status || row.dataset.status === status;
        row.style.display = (nameMatch && roleMatch && statMatch) ? '' : 'none';
    });
}
window.filterUserTable = filterUserTable;

// ── 3. Admin Control section ──────────────────────────────────

async function loadAdminSection() {
    const container = document.getElementById('admins-list');
    if (container) container.innerHTML = `<tr><td colspan="5" class="empty-state"><i class="fas fa-spinner fa-spin"></i> Loading admins...</td></tr>`;

    try {
        const res = await fetch(`${API_BASE}/api/creator/admins`, { headers: authHeaders() });
        const data = await res.json();
                console.log("API Response:", data);
        console.log("Data Loaded:", data);
        
        if (!data.success) {
            if (container) container.innerHTML = `<tr><td colspan="5" class="empty-state"><i class="fas fa-exclamation-triangle"></i> Failed to load admins</td></tr>`;
            return;
        }

        const admins = data.users || [];
        renderAdminsList(admins);
        
        // Also ensure _allUsers is updated for the grant select
        const userRes = await fetch(`${API_BASE}/api/creator/users`, { headers: authHeaders() });
        const userData = await userRes.json();
        if (userData.success) {
            _allUsers = userData.users;
            populateGrantSelect(_allUsers);
        }
    } catch (err) {
        console.error('Admin load error:', err);
        if (container) container.innerHTML = `<tr><td colspan="5" class="empty-state"><i class="fas fa-wifi"></i> Network error</td></tr>`;
    }
}

function renderAdminsList(admins) {
    const container = document.getElementById('admins-list');
    if (!container) return;
    if (!admins.length) {
        container.innerHTML = `<tr><td colspan="5" class="empty-state"><i class="fas fa-user-shield"></i> No admins found</td></tr>`;
        return;
    }
    container.innerHTML = admins.map(u => {
        const isActive  = u.is_active === 1 || u.is_active === true;
        const statusHtml = isActive
            ? `<span class="status-dot dot-active"></span>Active`
            : `<span class="status-dot dot-disabled"></span>Disabled`;
        return `
        <tr>
            <td><div style="font-weight:700;">${u.name}</div><div style="font-size:11px;opacity:0.5;">${u.student_id}</div></td>
            <td style="opacity:0.75;">${u.email}</td>
            <td style="opacity:0.75;">${u.department || '—'}</td>
            <td>${statusHtml}</td>
            <td><button class="act-btn btn-remove-admin" onclick="doRemoveAdmin('${u.student_id}','${escStr(u.name)}')">Revoke Admin</button></td>
        </tr>`;
    }).join('');
}

function populateGrantSelect(users) {
    const sel = document.getElementById('grant-admin-select');
    if (!sel) return;
    const nonAdmins = users.filter(u => u.role !== 'admin' && u.role !== 'creator');
    sel.innerHTML = `<option value="">— Choose a user —</option>` +
        nonAdmins.map(u => `<option value="${u.student_id}">${u.name} (${u.student_id})</option>`).join('');
}

async function doGrantAdmin() {
    const name = document.getElementById('grant-admin-name')?.value.trim();
    const email = document.getElementById('grant-admin-email')?.value.trim();
    const pwd = document.getElementById('grant-admin-pwd')?.value.trim();
    const dept = document.getElementById('grant-admin-dept')?.value.trim();

    if (!name || !email) { 
        showToast('Full Name and Email are mandatory', 'error'); 
        return; 
    }

    openModal(
        'Grant Admin Access',
        `Authorize "${name}" as a system Administrator?`,
        async () => {
            try {
                const res = await fetch(`${API_BASE}/api/creator/grant-admin`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({ name, email, password: pwd, department: dept })
                });
                const data = await res.json();
                console.log("API Response:", data);
                if (data.success) {
                    showToast(data.message || 'Admin Access Granted!', 'success');
                    document.getElementById('grant-admin-name').value = '';
                    document.getElementById('grant-admin-email').value = '';
                    document.getElementById('grant-admin-pwd').value = '';
                    document.getElementById('grant-admin-dept').value = '';
                    loadAdminSection();
                    loadSystemStats();
                } else {
                    showToast(data.message || 'Failed', 'error');
                }
            } catch (err) {
                showToast('Network Error', 'error');
            }
        }
    );
}
window.doGrantAdmin = doGrantAdmin;

// ── 4. Boundary Check (Creator) ───────────────────────────────

async function loadCreatorBoundary() {
    const tbody = document.getElementById('creator-boundary-list');
    if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="empty-state"><i class="fas fa-spinner fa-spin"></i> Loading GPS status...</td></tr>`;

    try {
        const dept = document.getElementById('cb-dept-filter')?.value || '';
        const section = document.getElementById('cb-section-filter')?.value || '';
        const sort = document.getElementById('cb-sort-filter')?.value || 'A-Z';
        
        const params = new URLSearchParams();
        if (dept) params.append('department', dept);
        if (section) params.append('section', section);
        if (sort) params.append('sort', sort);
        
        const url = `${API_BASE}/api/creator/boundary-status${params.toString() ? '?' + params.toString() : ''}`;
        const res = await fetch(url, { headers: authHeaders() });
        const data = await res.json();
                console.log("API Response:", data);
        console.log("Data Loaded:", data);
        if (!data.success) {
            if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="empty-state"><i class="fas fa-exclamation-triangle"></i> Failed to load boundary data</td></tr>`;
            return;
        }
        _creatorBoundaryData = data.students || [];
        renderCreatorBoundaryTable(_creatorBoundaryData);
    } catch (err) {
        console.error('Creator boundary error:', err);
        if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="empty-state"><i class="fas fa-wifi"></i> Network error</td></tr>`;
    }
}
window.loadCreatorBoundary = loadCreatorBoundary;

function renderCreatorBoundaryTable(students) {
    const tbody = document.getElementById('creator-boundary-list');
    if (!tbody) return;

    if (!students || students.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="empty-state"><i class="fas fa-satellite-dish"></i> No boundary records found.</td></tr>`;
        return;
    }

    tbody.innerHTML = students.map(s => {
        const status   = (s.gps_status || 'unknown').toLowerCase();
        const isInside  = status === 'inside';
        const isOutside = status === 'outside';

        let badgeHtml;
        if (isInside)       badgeHtml = `<span class="badge-inside"><i class="fas fa-check-circle"></i> INSIDE BOUNDARY</span>`;
        else if (isOutside) badgeHtml = `<span class="badge-outside"><i class="fas fa-times-circle"></i> OUTSIDE BOUNDARY</span>`;
        else                badgeHtml = `<span class="badge-unknown">UNKNOWN</span>`;

        const actionBtn = isInside
            ? `<div style="display:flex;gap:4px;">
                 <button class="act-btn btn-present" onclick="creatorMarkAttendance('${s.student_id}','${escStr(s.name)}','present',${s.distance})"><i class="fas fa-check"></i> Mark Present</button>
                 <button class="act-btn btn-absent"  onclick="creatorMarkAttendance('${s.student_id}','${escStr(s.name)}','absent',${s.distance})"><i class="fas fa-times"></i> Mark Absent</button>
               </div>`
            : isOutside
            ? `<button class="act-btn btn-absent"  onclick="creatorMarkAttendance('${s.student_id}','${escStr(s.name)}','absent',${s.distance})"><i class="fas fa-times"></i> Mark Absent</button>`
            : `<span style="opacity:0.4;font-size:13px;">No GPS data</span>`;

        const dist      = (s.distance !== undefined && s.distance !== null) ? `${parseFloat(s.distance).toFixed(1)} m` : '—';
        const lastCheck = s.last_check ? new Date(s.last_check).toLocaleString() : '—';

        return `<tr data-name="${(s.name||'').toLowerCase()}" data-status="${status}">
            <td>
                <div style="font-weight:700;">${s.name || '—'}</div>
                <div style="font-size:11px;opacity:0.5;">${s.student_id}</div>
            </td>
            <td style="opacity:0.75;">${s.email || '—'}</td>
            <td style="opacity:0.75;">${s.department || '—'}</td>
            <td style="opacity:0.6;font-size:0.82rem;">${lastCheck}</td>
            <td style="font-weight:600;">${dist}</td>
            <td>${badgeHtml}</td>
            <td>${actionBtn}</td>
        </tr>`;
    }).join('');
}

function filterCreatorBoundary() {
    const q      = (document.getElementById('cb-search')?.value || '').toLowerCase();
    const status = (document.getElementById('cb-status-filter')?.value || '').toLowerCase();
    document.querySelectorAll('#creator-boundary-list tr[data-name]').forEach(row => {
        const nameMatch   = !q || row.dataset.name.includes(q);
        const statusMatch = !status || row.dataset.status === status;
        row.style.display = (nameMatch && statusMatch) ? '' : 'none';
    });
}
window.filterCreatorBoundary = filterCreatorBoundary;

async function creatorMarkAttendance(studentId, name, status, distance) {
    openModal(
        'Mark Attendance',
        `Are you sure you want to mark ${name} as ${status.toUpperCase()}?`,
        async () => {
            try {
                const res = await fetch(`${API_BASE}/api/admin/mark-attendance`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({ student_id: studentId, status: status, distance: distance })
                });
                const data = await res.json();
                console.log("API Response:", data);
                if (data.success) {
                    showToast(`✓ ${name} marked as ${status.toUpperCase()}`, 'success');
                    loadCreatorBoundary();
                    loadSystemStats();
                } else {
                    showToast(data.message || 'Failed', 'error');
                }
            } catch (err) {
                showToast('Network error', 'error');
            }
        }
    );
}
window.creatorMarkAttendance = creatorMarkAttendance;

// ── 5. Activity Logs ──────────────────────────────────────────

function loadRecentLogins() {
    fetch(`${API_BASE}/api/creator/activity-logs`, { headers: authHeaders() })
    .then(res => res.json())
    .then(data => {
        console.log("Data Loaded:", data);
        renderRecentLogins(data);
    })
    .catch(err => {
        console.error("Failed to load login data", err);
    });
}

function renderRecentLogins(data) {
    const overviewBody = document.getElementById('overview-activity');
    const detailBody   = document.getElementById('activity-log');
    
    if (!data.success || !data.logs || !data.logs.length) {
        const emptyMsg = `<tr><td colspan="4" class="empty-state">No data</td></tr>`;
        if (overviewBody) overviewBody.innerHTML = emptyMsg;
        if (detailBody)   detailBody.innerHTML   = emptyMsg;
        return;
    }

    const rowsHtml = data.logs.map(log => {
        const isActive = log.is_active === 1 || log.is_active === true;
        const statusHtml = isActive ? `<span class="status-dot dot-active"></span>Active` : `<span class="status-dot dot-disabled"></span>Disabled`;
        
        let roleClass = 'role-student';
        if (log.role === 'admin') roleClass = 'role-admin';
        if (log.role === 'creator') roleClass = 'role-creator';
        
        const time = log.last_login ? new Date(log.last_login).toLocaleString() : '—';
        
        return `<tr>
            <td style="font-weight:700;">${log.name}</td>
            <td><span class="role-badge ${roleClass}">${log.role.toUpperCase()}</span></td>
            <td>${statusHtml}</td>
            <td style="opacity:0.6;font-size:0.82rem;">${time}</td>
        </tr>`;
    }).join('');
    
    if (overviewBody) overviewBody.innerHTML = rowsHtml;
    if (detailBody)   detailBody.innerHTML   = rowsHtml;
}

// ── 6. Attendance ─────────────────────────────────────────────

async function loadAttendance() {
    const container = document.getElementById('attendance-list');
    if (container) container.innerHTML = `<tr><td colspan="4" class="empty-state"><i class="fas fa-spinner fa-spin"></i> Loading attendance logs...</td></tr>`;

    try {
        const dept = document.getElementById('att-dept-filter')?.value || '';
        const section = document.getElementById('att-section-filter')?.value || '';
        const sort = document.getElementById('att-sort-filter')?.value || 'A-Z';
        
        const params = new URLSearchParams();
        if (dept) params.append('department', dept);
        if (section) params.append('section', section);
        if (sort) params.append('sort', sort);
        
        const url = `${API_BASE}/api/creator/attendance-logs${params.toString() ? '?' + params.toString() : ''}`;
        const res = await fetch(url, { headers: authHeaders() });
        const data = await res.json();
                console.log("API Response:", data);
        console.log("Data Loaded:", data);
        if (!container) return;

        if (!data.success || !data.records || !data.records.length) {
            container.innerHTML = `<tr><td colspan="4" class="empty-state"><i class="fas fa-calendar"></i> No attendance records found</td></tr>`;
            return;
        }

        renderAttendanceTable(data.records);
    } catch (err) {
        console.error('Attendance error:', err);
        if (container) container.innerHTML = `<tr><td colspan="4" class="empty-state"><i class="fas fa-wifi"></i> Network error</td></tr>`;
    }
}

function renderAttendanceTable(records) {
    const container = document.getElementById('attendance-list');
    if (!container) return;
    container.innerHTML = records.map(r => {
        const statusClass = (r.status || '').toLowerCase() === 'present' ? 'att-present' : 'att-absent';
        const time = r.timestamp ? new Date(r.timestamp).toLocaleString() : '—';
        return `
        <tr>
            <td style="font-weight:700;">${r.name || '—'}</td>
            <td style="font-size:11px;opacity:0.6;">${r.student_id || '—'}</td>
            <td style="opacity:0.8;">${time}</td>
            <td><span class="${statusClass}">${(r.status || '—').toUpperCase()}</span></td>
        </tr>`;
    }).join('');
}

async function confirmResetAttendance() {
    openModal(
        'Reset Attendance',
        'This will delete ALL attendance records for today. This cannot be undone. Continue?',
        async () => {
            try {
                const res = await fetch(`${API_BASE}/api/creator/reset-today-attendance`, {
                    method: 'POST',
                    headers: authHeaders()
                });
                const data = await res.json();
                console.log("API Response:", data);
                if (data.success) {
                    showToast('Attendance reset successfully', 'success');
                    loadSystemStats();
                    loadAttendance();
                } else {
                    showToast(data.message || 'Reset failed', 'error');
                }
            } catch (err) {
                showToast('Network error', 'error');
            }
        }
    );
}
window.confirmResetAttendance = confirmResetAttendance;

// ── Actions: Make / Remove Admin ──────────────────────────────

async function doMakeAdmin(studentId, name) {
    openModal(
        'Make Admin',
        `Promote "${name}" (${studentId}) to Admin?`,
        async () => {
            try {
                const res = await fetch(`${API_BASE}/api/creator/make-admin`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({ student_id: studentId })
                });
                const data = await res.json();
                console.log("API Response:", data);
                if (data.success) {
                    showToast(data.message, 'success');
                    await loadAllUsers();
                    loadSystemStats();
                    loadAdminSection();
                } else {
                    showToast(data.message || 'Error', 'error');
                }
            } catch (err) {
                showToast('Network error', 'error');
            }
        }
    );
}
window.doMakeAdmin = doMakeAdmin;

async function doRemoveAdmin(studentId, name) {
    openModal(
        'Revoke Admin',
        `Remove admin access from "${name}" (${studentId})?`,
        async () => {
            try {
                const res = await fetch(`${API_BASE}/api/creator/revoke-admin`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({ student_id: studentId })
                });
                const data = await res.json();
                console.log("API Response:", data);
                if (data.success) {
                    showToast(data.message, 'success');
                    await loadAllUsers();
                    loadSystemStats();
                    loadAdminSection();
                } else {
                    showToast(data.message || 'Error', 'error');
                }
            } catch (err) {
                showToast('Network error', 'error');
            }
        }
    );
}
window.doRemoveAdmin = doRemoveAdmin;

async function doDisableUser(studentId, name) {
    openModal(
        'Disable User',
        `Revoke system access for "${name}" (${studentId})? They will not be able to log in.`,
        async () => {
            try {
                const res = await fetch(`${API_BASE}/api/creator/disable-user`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({ student_id: studentId })
                });
                const data = await res.json();
                console.log("API Response:", data);
                if (data.success) {
                    showToast(data.message, 'success');
                    await loadAllUsers();
                    loadSystemStats();
                } else {
                    showToast(data.message || 'Error', 'error');
                }
            } catch (err) {
                showToast('Network error', 'error');
            }
        }
    );
}
window.doDisableUser = doDisableUser;

async function doEnableUser(studentId, name) {
    openModal(
        'Enable User',
        `Restore system access for "${name}" (${studentId})?`,
        async () => {
            try {
                const res = await fetch(`${API_BASE}/api/creator/enable-user`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({ student_id: studentId })
                });
                const data = await res.json();
                console.log("API Response:", data);
                if (data.success) {
                    showToast(data.message, 'success');
                    await loadAllUsers();
                    loadSystemStats();
                } else {
                    showToast(data.message || 'Error', 'error');
                }
            } catch (err) {
                showToast('Network error', 'error');
            }
        }
    );
}
window.doEnableUser = doEnableUser;

async function doRemoveUser(studentId, name) {
    openModal(
        'Remove User Account',
        `PERMANENTLY delete user "${name}" (${studentId}) from system? This action cannot be undone.`,
        async () => {
            try {
                const res = await fetch(`${API_BASE}/api/creator/remove-user`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({ student_id: studentId })
                });
                const data = await res.json();
                console.log("API Response:", data);
                if (data.success) {
                    showToast(`User ${name} was successfully removed.`, 'success');
                    await loadAllUsers();
                    loadSystemStats();
                } else {
                    showToast(data.message || 'Operation failed', 'error');
                }
            } catch (err) {
                showToast('Network connection error', 'error');
            }
        }
    );
}
window.doRemoveUser = doRemoveUser;

function viewDetails(sid, name, email, role, isActive, lastLogin) {
    openModal(
        `User Details — ${name}`,
        `ID: ${sid}\nEmail: ${email}\nRole: ${role.toUpperCase()}\nStatus: ${isActive === 'true' ? 'Active' : 'Disabled'}\nLast Login: ${lastLogin}`,
        () => {}
    );
    document.getElementById('modal-confirm').style.display = 'none';
    const origClose = window.closeModal;
    window.closeModal = () => {
        document.getElementById('modal-confirm').style.display = '';
        window.closeModal = origClose;
        origClose();
    };
}
window.viewDetails = viewDetails;

// ── Utility ───────────────────────────────────────────────────

function escStr(s) {
    return (s || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function handleLogout() {
    localStorage.removeItem('sat_token');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}
window.handleLogout = handleLogout;

// --- Global Setting Management ---
let _faceEnabled = true;
async function fetchFaceSetting() {
    const btn = document.getElementById('btn-toggle-face');
    if (!btn) return;
    try {
        const res = await fetch(`${API_BASE}/api/system/face-config`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            _faceEnabled = data.enabled;
            updateFaceBtnUI();
        }
    } catch (err) { console.error(err); }
}

function updateFaceBtnUI() {
    const btn = document.getElementById('btn-toggle-face');
    if (!btn) return;
    if (_faceEnabled) {
        btn.textContent = "ENABLED (ON)";
        btn.style.background = "rgba(56,239,125,0.15)";
        btn.style.borderColor = "var(--accent-green)";
        btn.style.color = "var(--accent-green)";
    } else {
        btn.textContent = "DISABLED (OFF)";
        btn.style.background = "rgba(255,77,77,0.15)";
        btn.style.borderColor = "var(--accent-red)";
        btn.style.color = "var(--accent-red)";
    }
}

async function toggleFaceSetting() {
    const btn = document.getElementById('btn-toggle-face');
    if (btn) btn.textContent = "UPDATING...";
    const targetState = !_faceEnabled;
    try {
        const res = await fetch(`${API_BASE}/api/system/face-config`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ enabled: targetState })
        });
        const data = await res.json();
        if (data.success) {
            _faceEnabled = data.enabled;
            updateFaceBtnUI();
            showToast(`Face verification is now ${data.enabled ? 'ON' : 'OFF'}`);
        } else {
            showToast("Operation failed", "error");
            updateFaceBtnUI();
        }
    } catch (e) {
        showToast("Network Error", "error");
        updateFaceBtnUI();
    }
}
window.toggleFaceSetting = toggleFaceSetting;
window.fetchFaceSetting = fetchFaceSetting;

// ── Fingerprint Global Toggle ─────────────────────────────
let fingerprintEnabled = false;

async function fetchFingerprintSetting() {
    const btn = document.getElementById('btn-toggle-fingerprint');
    if (!btn) return;

    try {
        const res = await fetch(`${API_BASE}/api/system/fingerprint-config`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            fingerprintEnabled = data.enabled;
            updateFingerprintBtnUI();
        }
    } catch (e) {
        console.error("Failed to fetch fingerprint config:", e);
    }
}

async function toggleFingerprintSetting() {
    const btn = document.getElementById('btn-toggle-fingerprint');
    if (!btn) return;

    const newState = !fingerprintEnabled;
    btn.disabled = true;
    btn.textContent = "WAIT...";

    try {
        const res = await fetch(`${API_BASE}/api/system/fingerprint-config`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ enabled: newState })
        });
        const data = await res.json();
        if (data.success) {
            fingerprintEnabled = newState;
            showToast(`Fingerprint verification ${newState ? 'ENABLED' : 'DISABLED'}`, 'success');
        } else {
            showToast("Failed to update setting", "error");
        }
    } catch (e) {
        showToast("Server error", "error");
    } finally {
        btn.disabled = false;
        updateFingerprintBtnUI();
    }
}

function updateFingerprintBtnUI() {
    const btn = document.getElementById('btn-toggle-fingerprint');
    if (!btn) return;

    if (fingerprintEnabled) {
        btn.textContent = "ENABLED (ON)";
        btn.style.background = "rgba(56,239,125,0.15)";
        btn.style.borderColor = "var(--accent-green)";
        btn.style.color = "var(--accent-green)";
    } else {
        btn.textContent = "DISABLED (OFF)";
        btn.style.background = "rgba(255,77,77,0.15)";
        btn.style.borderColor = "var(--accent-red)";
        btn.style.color = "var(--accent-red)";
    }
}

window.toggleFingerprintSetting = toggleFingerprintSetting;
window.fetchFingerprintSetting = fetchFingerprintSetting;

