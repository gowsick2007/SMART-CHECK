// ============================================================
// admin.js — Admin Dashboard Logic (Full Implementation)
// Admin: View boundary, mark attendance, view logs
// Admin CANNOT: manage roles, disable users
// ============================================================

// const API_BASE = 'http://127.0.0.1:5000'; // Handled globally by auth.js

let _boundaryData = [];
let _attendanceData = [];

// ── Helpers ──────────────────────────────────────────────────

function getToken() {
    return localStorage.getItem('sat_token') || localStorage.getItem('token') || '';
}

function authHeaders() {
    return {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
    };
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

  // Restore user header
  try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const el = document.getElementById('admin-name');
      if (el && user.name) el.textContent = user.name;
      
      // Proactively request location for Admin boundary control if not already prompted
      if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
              (pos) => console.log("Admin location accessible:", pos.coords.latitude, pos.coords.longitude),
              (err) => console.warn("Admin location denied or unavailable:", err.message)
          );
      }
  } catch (_) {}

  loadSectionData("overview");
});

function loadSectionData(id) {
    console.log("Loading data for:", id);
    if (id === "overview") {
        if (typeof loadOverviewStats === 'function') loadOverviewStats();
        if (typeof loadBoundaryStatus === 'function') loadBoundaryStatus();
    } else if (id === "boundary-check") {
        if (typeof loadBoundaryStatus === 'function') loadBoundaryStatus();
    } else if (id === "attendance-logs") {
        if (typeof loadAttendanceLogs === 'function') loadAttendanceLogs();
    } else if (id === "auto-verification") {
        if (typeof loadAutoVerifyLogs === 'function') loadAutoVerifyLogs();
    }

    const el = document.getElementById('last-refresh');
    if (el) {
        el.innerHTML = 'Last refreshed: ' + new Date().toLocaleTimeString();
    }
}

// ── 1. Overview Stats ─────────────────────────────────────────

async function loadOverviewStats() {
    try {
        const res = await fetch(`${API_BASE}/api/admin/overview-stats`, { headers: authHeaders() });
        const data = await res.json();
        console.log("Data Loaded:", data);
        if (!data.success) return;
        const s = data.stats;
        setText('ov-total',   s.total_students);
        setText('ov-present', s.today_present);
        setText('ov-absent',  s.today_absent);
        setText('ov-inside',  s.inside_boundary);
        setText('ov-outside', s.outside_boundary);
    } catch (err) {
        console.error('Overview stats error:', err);
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = (val !== undefined && val !== null) ? val : 'N/A';
}

// ── 2. Boundary Status ────────────────────────────────────────

async function loadBoundaryStatus() {
    try {
        const dept = document.getElementById('boundary-dept-filter')?.value || '';
        const section = document.getElementById('boundary-section-filter')?.value || '';
        const sort = document.getElementById('boundary-sort-filter')?.value || 'A-Z';
        
        const params = new URLSearchParams();
        if (dept) params.append('department', dept);
        if (section) params.append('section', section);
        if (sort) params.append('sort', sort);
        
        const url = `${API_BASE}/api/admin/boundary-checks${params.toString() ? '?' + params.toString() : ''}`;
        const res = await fetch(url, { headers: authHeaders() });
        const data = await res.json();
        console.log("Data Loaded:", data);
        if (!data.success) { 
            showToast('Failed to load boundary data', 'error'); 
            document.getElementById('overview-boundary').innerHTML = `<tr><td colspan="5" class="empty-state"><i class="fas fa-exclamation-circle"></i> Failed to load data</td></tr>`;
            return; 
        }

        _boundaryData = data.students || [];
        renderBoundaryTable(_boundaryData);
        renderOverviewBoundary(_boundaryData.slice(0, 8));
    } catch (err) {
        console.error('Boundary status error:', err);
        const overviewBody = document.getElementById('overview-boundary');
        if (overviewBody) {
            overviewBody.innerHTML = `<tr><td colspan="5" class="empty-state"><i class="fas fa-wifi"></i> Failed to load data</td></tr>`;
        }
        showToast('Network error loading boundary data', 'error');
    }
}
window.loadBoundaryStatus = loadBoundaryStatus;

function renderBoundaryTable(students) {
    const tbody = document.getElementById('boundary-list');
    if (!tbody) return;

    if (!students || students.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="empty-state"><i class="fas fa-satellite-dish"></i> Current location not available. Students must complete location check first.</td></tr>`;
        return;
    }

    tbody.innerHTML = students.map(s => {
        const rawStatus = (s.gps_status || 'unknown').toLowerCase();
        const status = rawStatus === 'unavailable' ? 'unknown' : rawStatus;
        const isInside = status === 'inside';
        const isOutside = status === 'outside';
        const isUnavailable = rawStatus === 'unavailable';

        let badgeHtml;
        if (isInside)  badgeHtml = `<span class="badge-inside"><i class="fas fa-check-circle"></i> INSIDE BOUNDARY</span>`;
        else if (isOutside) badgeHtml = `<span class="badge-outside"><i class="fas fa-times-circle"></i> OUTSIDE BOUNDARY</span>`;
        else if (isUnavailable) badgeHtml = `<span class="badge-unknown" style="color:#ff6b6b; border-color:rgba(255,107,107,0.3);">UNAVAILABLE</span>`;
        else           badgeHtml = `<span class="badge-unknown">UNKNOWN</span>`;

        const actionBtn = `
            <div style="display:flex; gap:5px;">
                <button class="act-btn btn-check" id="check-btn-${s.student_id}" onclick="checkStudentGPS('${s.student_id}')" title="Fetch current status"><i class="fas fa-satellite-dish"></i> Check</button>
                ${isInside 
                    ? `<button class="act-btn btn-present" onclick="markAttendance('${s.student_id}', '${escStr(s.name)}', 'present')"><i class="fas fa-check"></i> Present</button>` 
                    : `<button class="act-btn btn-absent" onclick="markAttendance('${s.student_id}', '${escStr(s.name)}', 'absent')"><i class="fas fa-times"></i> Absent</button>`
                }
            </div>
        `;

        const dist = (s.distance !== undefined && s.distance !== null && !isUnavailable) ? `${parseFloat(s.distance).toFixed(1)} m` : 'N/A';
        const lastCheck = (isUnavailable || !s.last_check) ? 'Current location not available' : s.last_check;

        return `<tr data-name="${(s.name||'').toLowerCase()}" data-status="${status}" id="row-${s.student_id}">
            <td>
                <div style="font-weight:700;">${s.name || '—'}</div>
                <div style="font-size:11px;opacity:0.5;">${s.student_id}</div>
            </td>
            <td style="opacity:0.75;">${s.email || '—'}</td>
            <td style="opacity:0.75;">${s.department || '—'}</td>
            <td style="opacity:0.6;font-size:0.82rem;" class="last-check-cell">${lastCheck}</td>
            <td style="font-weight:600;" class="distance-cell">${dist}</td>
            <td class="status-cell">${badgeHtml}</td>
            <td>${actionBtn}</td>
        </tr>`;
    }).join('');
}

function renderOverviewBoundary(students) {
    const tbody = document.getElementById('overview-boundary');
    if (!tbody) return;
    if (!students || students.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="empty-state"><i class="fas fa-satellite-dish"></i> No boundary checks found</td></tr>`;
        return;
    }
    tbody.innerHTML = students.map(s => {
        const status = (s.gps_status || 'unknown').toLowerCase();
        const isInside = status === 'inside';
        const isOutside = status === 'outside';
        let badgeHtml;
        if (isInside)  badgeHtml = `<span class="badge-inside"><i class="fas fa-check-circle"></i> INSIDE</span>`;
        else if (isOutside) badgeHtml = `<span class="badge-outside"><i class="fas fa-times-circle"></i> OUTSIDE</span>`;
        else           badgeHtml = `<span class="badge-unknown">UNKNOWN</span>`;
        const dist = (s.distance !== undefined && s.distance !== null) ? `${parseFloat(s.distance).toFixed(1)} m` : 'N/A';
        const lastCheck = s.last_check ? new Date(s.last_check).toLocaleString() : 'N/A';
        return `<tr>
            <td><div style="font-weight:700;">${s.name||'—'}</div><div style="font-size:11px;opacity:0.5;">${s.student_id}</div></td>
            <td style="opacity:0.75;">${s.department||'—'}</td>
            <td style="font-weight:600;">${dist}</td>
            <td>${badgeHtml}</td>
            <td style="opacity:0.6;font-size:0.82rem;">${lastCheck}</td>
        </tr>`;
    }).join('');
}

function filterBoundaryTable() {
    const q      = (document.getElementById('boundary-search')?.value || '').toLowerCase();
    const status = (document.getElementById('boundary-status-filter')?.value || '').toLowerCase();
    document.querySelectorAll('#boundary-list tr[data-name]').forEach(row => {
        const nameMatch   = !q || row.dataset.name.includes(q);
        const statusMatch = !status || row.dataset.status === status;
        row.style.display = (nameMatch && statusMatch) ? '' : 'none';
    });
}
window.filterBoundaryTable = filterBoundaryTable;

// ── 3. Mark Attendance ────────────────────────────────────────

async function checkStudentGPS(studentId) {
    const btn = document.getElementById(`check-btn-${studentId}`);
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
    }
    
    try {
        // First refresh attempt
        await loadBoundaryStatus();
        
        // Wait 2 seconds and retry once more to catch any incoming live update
        await new Promise(r => setTimeout(r, 2000));
        await loadBoundaryStatus();
        
        showToast('Boundary status check complete.', 'success');
    } catch (err) {
        console.error(err);
        showToast('Failed to refresh student status.', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-satellite-dish"></i> Check';
        }
    }
}
window.checkStudentGPS = checkStudentGPS;

async function markAttendance(studentId, name, status) {
    if (!(await showConfirmModal('Confirm Attendance Update', `Are you sure you want to mark ${name} as ${status.toUpperCase()}?`))) return;
    try {
        const res = await fetch(`${API_BASE}/api/admin/mark-attendance`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ student_id: studentId, status: status })
        });
        const data = await res.json();
        console.log("Data Loaded:", data);
        if (data.success) {
            showSuccessToast("Attendance marked successfully.");
            loadBoundaryStatus();
            loadOverviewStats();
        } else {
            showErrorToast(data.message || 'Failed to mark attendance');
        }
    } catch (err) {
        console.error('Mark attendance error:', err);
        showToast('Network error', 'error');
    }
}
window.markAttendance = markAttendance;

// ── 4. Attendance Logs ────────────────────────────────────────

async function loadAttendanceLogs() {
    try {
        const dept = document.getElementById('att-dept-filter')?.value || '';
        const section = document.getElementById('att-section-filter')?.value || '';
        const sort = document.getElementById('att-sort-filter')?.value || 'A-Z';
        
        const params = new URLSearchParams();
        if (dept) params.append('department', dept);
        if (section) params.append('section', section);
        if (sort) params.append('sort', sort);
        
        const url = `${API_BASE}/api/admin/attendance-logs${params.toString() ? '?' + params.toString() : ''}`;
        const res = await fetch(url, { headers: authHeaders() });
        const data = await res.json();
        console.log("Data Loaded:", data);
        const tbody = document.getElementById('attendance-list');
        if (!tbody) return;

        if (!data.success || !data.records || data.records.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="empty-state"><i class="fas fa-calendar"></i> No attendance records found</td></tr>`;
            return;
        }

        _attendanceData = data.records;
        renderAttTable(_attendanceData);
    } catch (err) {
        console.error('Attendance logs error:', err);
    }
}

function renderAttTable(records) {
    const tbody = document.getElementById('attendance-list');
    if (!tbody) return;
    tbody.innerHTML = records.map(r => {
        const statusClass = (r.status || '').toLowerCase() === 'present' ? 'att-present' : 'att-absent';
        const date = r.date ? new Date(r.date).toLocaleDateString() : (r.timestamp ? new Date(r.timestamp).toLocaleDateString() : 'N/A');
        const time = r.time || (r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : 'N/A');
        return `<tr data-name="${(r.name||r.student_id||'').toLowerCase()}" data-status="${(r.status||'').toLowerCase()}">
            <td style="font-weight:700;">${r.name || 'N/A'}</td>
            <td style="opacity:0.7;">${r.student_id}</td>
            <td style="opacity:0.65;font-size:0.85rem;">${date}</td>
            <td style="opacity:0.65;font-size:0.85rem;">${time}</td>
            <td><span class="${statusClass}">${(r.status||'N/A').toUpperCase()}</span></td>
            <td style="opacity:0.55;font-size:0.82rem;">${r.recorded_by_role || 'system'}</td>
        </tr>`;
    }).join('');
}

function filterAttTable() {
    const q      = (document.getElementById('att-search')?.value || '').toLowerCase();
    const status = (document.getElementById('att-status-filter')?.value || '').toLowerCase();
    document.querySelectorAll('#attendance-list tr[data-name]').forEach(row => {
        const nameMatch   = !q || row.dataset.name.includes(q);
        const statusMatch = !status || row.dataset.status === status;
        row.style.display = (nameMatch && statusMatch) ? '' : 'none';
    });
}
window.filterAttTable = filterAttTable;

// ── 5. Auto Verification Logs ─────────────────────────────────

async function loadAutoVerifyLogs() {
    try {
        const dept = document.getElementById('auto-dept-filter')?.value || '';
        const section = document.getElementById('auto-section-filter')?.value || '';
        const sort = document.getElementById('auto-sort-filter')?.value || 'A-Z';
        
        const params = new URLSearchParams();
        if (dept) params.append('department', dept);
        if (section) params.append('section', section);
        if (sort) params.append('sort', sort);
        
        const url = `${API_BASE}/api/admin/auto-verification${params.toString() ? '?' + params.toString() : ''}`;
        const res = await fetch(url, { headers: authHeaders() });
        const data = await res.json();
        console.log("Data Loaded:", data);
        const tbody = document.getElementById('autoverify-list');
        if (!tbody) return;

        if (!data.success || !data.logs || data.logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="empty-state"><i class="fas fa-robot"></i> No auto-verification records found</td></tr>`;
            return;
        }

        tbody.innerHTML = data.logs.map(log => {
            const gpsClass   = log.gps_status === 'inside' ? 'att-present' : 'att-absent';
            const faceClass  = log.face_status === 'success' ? 'att-present' : 'att-absent';
            const finalClass = log.final_status === 'present' ? 'att-present' : 'att-absent';
            const ts = log.timestamp ? new Date(log.timestamp).toLocaleString() : (log.check_time ? new Date(log.check_time).toLocaleString() : '—');
            
            let faceHtml = '';
            if(log.face_status === 'not_registered') faceHtml = 'NOT_REGISTERED';
            else if(log.face_status === 'failed') faceHtml = 'FAILED';
            else if(log.face_status === 'success') faceHtml = 'VERIFIED';
            else faceHtml = (log.face_status || '—').toUpperCase();

            return `<tr>
                <td style="font-weight:700;">${log.name || log.student_id || '—'}</td>
                <td><span class="${gpsClass}">${(log.gps_status || '—').toUpperCase()}</span></td>
                <td><span class="${faceClass}">${faceHtml}</span></td>
                <td><span class="${finalClass}">${(log.final_status || '—').toUpperCase()}</span></td>
                <td style="opacity:0.6;font-size:0.82rem;">${ts}</td>
            </tr>`;
        }).join('');
    } catch (err) {
        console.error('Auto verify logs error:', err);
    }
}

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

let _selectedManualStudentId = null;

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('manual-username');
    const box = document.getElementById('manual-suggestions');
    if (!input || !box) return;
    
    let timer = null;
    input.addEventListener('input', (e) => {
        clearTimeout(timer);
        _selectedManualStudentId = null; // reset on keypress
        const detailBox = document.getElementById('manual-status-details');
        if (detailBox) detailBox.style.display = 'none';

        const q = e.target.value.trim();
        if (!q || q.length < 2) {
            box.style.display = 'none';
            return;
        }
        timer = setTimeout(async () => {
            try {
                const res = await fetch(`${API_BASE}/api/admin/search-students?q=${encodeURIComponent(q)}`, { headers: authHeaders() });
                const data = await res.json();
                if (data.success && data.students && data.students.length > 0) {
                    box.innerHTML = data.students.map(s => `
                        <div class="manual-sugg-item" onclick='selectManualStudent(${JSON.stringify(s)})'>
                            <strong>${s.name}</strong>
                            <span>${s.student_id} • ${s.department} • Status: ${s.gps_status.toUpperCase()}</span>
                        </div>
                    `).join('');
                    box.style.display = 'block';
                } else {
                    box.innerHTML = '<div style="padding:12px; color:rgba(255,255,255,0.4); font-size:13px;">No student found</div>';
                    box.style.display = 'block';
                }
            } catch (err) { console.error(err); }
        }, 300);
    });

    // Clear drop on outer click
    document.addEventListener('click', (ev) => {
        if (!input.contains(ev.target) && !box.contains(ev.target)) box.style.display = 'none';
    });
});

window.selectManualStudent = async function(s) {
    const input = document.getElementById('manual-username');
    const box = document.getElementById('manual-suggestions');
    const det = document.getElementById('manual-status-details');
    
    input.value = s.name;
    box.style.display = 'none';
    _selectedManualStudentId = s.student_id;
    
    det.innerHTML = `
        <div class="detail-row"><span class="detail-label">Name</span><span class="detail-val">${s.name}</span></div>
        <div class="detail-row"><span class="detail-label">Student ID</span><span class="detail-val">${s.student_id}</span></div>
        <div class="detail-row"><span class="detail-label">Email</span><span class="detail-val" style="font-size:11px;">${s.email}</span></div>
        <div class="detail-row"><span class="detail-label">Dept / Section</span><span class="detail-val">${s.department} / ${s.section || '—'}</span></div>
        <div id="manual-live-boundary" class="detail-row" style="border-bottom:none;">
            <span class="detail-label">Boundary</span>
            <span class="detail-val"><i class="fas fa-spinner fa-spin"></i> Fetching live status...</span>
        </div>
    `;
    det.style.display = 'block';

    try {
        const res = await fetch(`${API_BASE}/api/admin/boundary-check?student_id=${s.student_id}`, { headers: authHeaders() });
        const data = await res.json();
        const liveBoundaryEl = document.getElementById('manual-live-boundary');
        if (liveBoundaryEl) {
            if (data.success) {
                const status = (data.status || 'unknown').toLowerCase();
                const isStale = data.is_stale === true;
                let color = '#ffd166'; // unknown/stale
                let statusText = 'Unavailable';

                if (isStale) {
                    statusText = 'Current location not available';
                    color = '#ff6b6b';
                } else if (status === 'inside') {
                    statusText = 'INSIDE';
                    color = '#00ffcc';
                } else if (status === 'outside') {
                    statusText = 'OUTSIDE';
                    color = '#ff6b6b';
                }

                liveBoundaryEl.innerHTML = `
                    <span class="detail-label">Boundary</span>
                    <span class="detail-val" style="color:${color}; text-transform:uppercase;">${statusText}</span>
                `;
            } else {
                liveBoundaryEl.innerHTML = `
                    <span class="detail-label">Boundary</span>
                    <span class="detail-val" style="color:#ff6b6b; text-transform:uppercase;">Unavailable</span>
                `;
            }
        }
    } catch (err) {
        console.error("Live boundary check failed:", err);
    }
};

async function submitManualAttendance(status) {
    const input = document.getElementById('manual-username');
    const rawUsername = input ? input.value.trim() : '';
    // Prioritize the stored explicit student_id if selection was made.
    const finalIdentifier = _selectedManualStudentId || rawUsername;
    
    if (!finalIdentifier) {
        showToast('Please enter a student name or ID', 'error');
        return;
    }

    if (!(await showConfirmModal('Confirm Attendance Update', `Are you sure you want to mark ${rawUsername || _selectedManualStudentId} as ${status.toUpperCase()}?`))) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/admin/manual-attendance`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ username: finalIdentifier, status: status })
        });
        const data = await res.json();
        console.log("Data Loaded:", data);
        if (data.success) {
            showSuccessToast("Attendance marked successfully.");
            if (input) input.value = ''; 
            _selectedManualStudentId = null;
            const det = document.getElementById('manual-status-details');
            if (det) det.style.display = 'none';
            loadOverviewStats();
        } else {
            showErrorToast(data.message || 'Failed to mark attendance');
        }
    } catch (err) {
        console.error("Manual Attendance Error:", err);
        showToast('Network Error', 'error');
    }
}
window.submitManualAttendance = submitManualAttendance;

// ── Export Details ─────────────────────────────────────────────

async function exportAdminDetails() {
    if (typeof _attendanceData === 'undefined' || !_attendanceData || _attendanceData.length === 0) {
        showToast("Fetching data for export...", "info");
        await loadAttendanceLogs();
    }
    
    if (!_attendanceData || _attendanceData.length === 0) {
        showWarningToast("No attendance data available to export.");
        return;
    }

    const q = (document.getElementById('att-search')?.value || '').toLowerCase();
    const statusFilter = (document.getElementById('att-status-filter')?.value || '').toLowerCase();

    // Use ALL data from the backend report
    const filtered = _attendanceData.filter(r => {
        const nameMatch = !q || (r.name || '').toLowerCase().includes(q) || (r.student_id || '').toLowerCase().includes(q);
        const statusMatch = !statusFilter || (r.status || '').toLowerCase() === statusFilter;
        return nameMatch && statusMatch;
    });

    if (filtered.length === 0) {
        showWarningToast("No records match current filters.");
        return;
    }

    let csvContent = "Student Name,Student ID,Department,Section,Email,Attendance Percentage,Date,Time,Boundary Status,Face Match Status,Distance,Attendance Status,Recorded By\n";

    filtered.forEach(r => {
        const boundaryStatus = (r.location_valid === true) ? "Inside" : (r.location_valid === false ? "Outside" : "N/A");
        
        let faceMatchStatus = "N/A";
        if (r.face_match_status === 'success' || r.face_match_status === 'Matched') faceMatchStatus = "Matched";
        else if (r.face_match_status === 'failed' || r.face_match_status === 'Not Matched') faceMatchStatus = "Not Matched";

        let distanceText = "N/A";
        if (r.remarks) {
            const match = String(r.remarks).match(/([0-9.]+) ?m/);
            if (match) distanceText = match[1] + " m";
            else if (String(r.remarks).includes("Attendance manually updated")) distanceText = "N/A";
        }

        const row = [
            `"${(r.name || 'N/A').replace(/"/g, '""')}"`,
            `"${(r.student_id || 'N/A').replace(/"/g, '""')}"`,
            `"${(r.department || 'N/A').replace(/"/g, '""')}"`,
            `"${(r.class_name || r.section || 'N/A').replace(/"/g, '""')}"`,
            `"${(r.email || 'N/A').replace(/"/g, '""')}"`,
            `"${r.attendance_percentage || '0'}%"`,
            `"${r.date || 'N/A'}"`,
            `"${(r.time && r.time !== '—') ? r.time : 'N/A'}"`,
            `"${boundaryStatus}"`,
            `"${faceMatchStatus}"`,
            `"${distanceText}"`,
            `"${(r.status || 'ABSENT').toUpperCase()}"`,
            `"${(r.recorded_by_role || 'system').toUpperCase()}"`
        ];
        csvContent += row.join(",") + "\n";
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=ascii;' });
    const link = document.createElement("a");
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute("download", `Admin_Export_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}
window.exportAdminDetails = exportAdminDetails;
