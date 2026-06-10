// ============================================================
// history.js — Attendance & Verification History Logic
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
});

async function loadHistory() {
    const user = JSON.parse(localStorage.getItem('sat_student') || '{}');
    const token = localStorage.getItem('sat_token');
    if (!user.student_id) return;

    window.studentHistoryRecords = [];

    try {
        const res = await fetch(`/api/attendance/history?student_id=${user.student_id}&_t=${Date.now()}`, {
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        });
        const data = await res.json();
        
        if (data.success) {
            window.studentHistoryRecords = data.records;
            renderHistory(data.records);
        } else {
            document.getElementById('history-table-body').innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--text-muted);">Failed to fetch history.</td></tr>';
        }
    } catch (err) {
        console.error("History load error:", err);
        document.getElementById('history-table-body').innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--text-muted);">Error connecting to server.</td></tr>';
    }
}

function renderHistory(records) {
    const tbody = document.getElementById('history-table-body');
    if (!records || records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--text-muted);">No attendance history found.</td></tr>';
        return;
    }

    tbody.innerHTML = records.map(rec => {
        const displayDate = rec.date || '—';
        const displayTime = rec.time || '—';
        
        const type = rec.type || 'Auto Verified';
        let typeHtml = `<span>${type}</span>`;
        
        // Support fallback or new mapped field
        const isInside = rec.boundary === 'inside' || rec.location_valid === true || rec.location_valid === 1;
        const faceMatched = rec.face_match === 'success' || rec.face_match === 'match' || rec.face_match_status === 'success' || rec.face_match_status === 'match';
        
        let distanceVal = rec.distance || '—';
        // Removed override to allow specific 'Manual attendance + ...' strings from backend
        const statusVal = (rec.status || 'absent').toLowerCase();
        const isPresent = statusVal === 'present';

        return `
        <tr>
            <td>
                <div style="font-weight: 700;">${displayDate}</div>
                <div style="font-size: 11px; color: var(--text-muted);">${displayTime}</div>
            </td>
            <td style="color: var(--text-secondary); font-size: 13px;">${typeHtml}</td>
            <td>
                <span style="color: ${isInside ? 'var(--accent-green)' : 'var(--accent-red)'}; font-weight: 600;">
                    ${isInside ? 'INSIDE' : 'OUTSIDE'}
                </span>
            </td>
            <td>
                <div class="status-cell">
                    ${rec.face_match_status === 'success' ? `
                        <i class="fa-solid fa-circle-check" style="color: var(--accent-green)"></i>
                        <span style="color: var(--accent-green)">Matched</span>
                    ` : `
                        <span style="color: var(--text-muted); font-size: 16px; font-weight: bold;">—</span>
                    `}
                </div>
            </td>
            <td style="font-family: monospace; color: var(--text-muted); font-size: 12px;">${distanceVal}</td>
            <td>
                <span class="badge ${isPresent ? 'badge-present' : 'badge-absent'}" style="text-transform: uppercase; font-weight: 700; padding: 4px 8px; border-radius: 6px; background: ${isPresent ? 'rgba(0,255,136,0.2)' : 'rgba(255,68,68,0.2)'}; color: ${isPresent ? '#00ff88' : '#ff4444'}">
                    ${rec.status}
                </span>
            </td>
        </tr>
    `; }).join('');
}

async function exportHistoryCSV() {
    if (!window.studentHistoryRecords || window.studentHistoryRecords.length === 0) {
        await showWarningToast("No records to export.");
        return;
    }
    
    // Fetch summary to get attendance percentage
    const user = JSON.parse(localStorage.getItem('sat_student') || '{}');
    const token = localStorage.getItem('sat_token');
    let attPct = '0';
    
    try {
        const res = await fetch(`/api/attendance/summary?student_id=${user.student_id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        if (data.success && data.summary) {
            attPct = data.summary.percentage || '0';
        }
    } catch (err) {
        console.error("Failed to fetch percentage for export:", err);
    }
    
    const uName = `"${user.name || ''}"`;
    const uSid = `"${user.student_id || ''}"`;
    const uDept = `"${user.department || ''}"`;
    const uSec = `"${user.class_name || ''}"`;
    const uEmail = `"${user.email || ''}"`;

    let csv = "Student Name,Student ID,Department,Section,Email,Attendance Percentage,Date,Time,Boundary Status,Face Match Status,Distance,Attendance Status\n";
    window.studentHistoryRecords.forEach(rec => {
        const date = `"${rec.date || '—'}"`;
        const time = `"${rec.time || '—'}"`;
        const isInside = (rec.boundary === 'inside' || rec.location_valid === true || rec.location_valid === 1 || String(rec.remarks).includes('INSIDE')) ? 'Inside' : 'Outside';
        const faceMatched = (rec.face_match === 'success' || rec.face_match === 'match' || rec.face_match_status === 'success' || rec.face_match_status === 'match' || String(rec.remarks).includes('MATCHED')) ? 'Matched' : '—';
        
        let distance = '—';
        if (rec.remarks) {
            const match = String(rec.remarks).match(/([0-9.]+)m/);
            if (match) distance = `${match[1]} m`;
        } else if (rec.distance) {
            distance = `${parseFloat(rec.distance).toFixed(1)} m`;
        }

        const status = (rec.status || 'absent').toUpperCase();
        
        csv += `${uName},${uSid},${uDept},${uSec},${uEmail},"${attPct}%",${date},${time},"${isInside}","${faceMatched}","${distance}","${status}"\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('href', url);
    a.setAttribute('download', 'My_Attendance_History.csv');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}
