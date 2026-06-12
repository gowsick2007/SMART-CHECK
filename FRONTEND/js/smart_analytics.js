// ============================================================
// smart_analytics.js — Frontend logic for Command Center
// ============================================================

const API_BASE = '';

function authHeaders() {
    const token = localStorage.getItem('sat_token') || localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

async function initSmartDashboard() {
    // 5. Live Command Center
    await loadLiveStats();
    // 1. Trust Scores
    await loadTrustScores();
    // 3. Fraud Alerts
    await loadFraudAlerts();
    // 6. Occupancy Monitor
    await loadOccupancy();
    
    // Set Admin Name
    const user = JSON.parse(localStorage.getItem('sat_student') || '{}');
    document.getElementById('admin-name').textContent = user.name || 'Administrator';
}

async function loadLiveStats() {
    try {
        const res = await fetch(`${API_BASE}/api/smart/summary`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            document.getElementById('stat-present').textContent = data.stats.total_present || 0;
            document.getElementById('stat-absent').textContent = data.stats.total_absent || 0;
            document.getElementById('stat-face').textContent = data.stats.face_verified || 0;
            document.getElementById('stat-boundary').textContent = data.stats.inside_boundary || 0;
            renderOccupancy(data.occupancy);
        }
    } catch (err) {
        console.error("Live Stats Error:", err);
    }
}

async function loadTrustScores() {
    try {
        const res = await fetch(`${API_BASE}/api/smart/trust-scores`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            const tbody = document.getElementById('trust-table-body');
            tbody.innerHTML = data.scores.slice(0, 10).map(s => `
                <tr>
                    <td>
                        <div style="font-weight:700; color:#fff;">${s.name}</div>
                        <div style="font-size:11px; opacity:0.5;">${s.student_id}</div>
                    </td>
                    <td style="text-align:right;">
                        <span class="score-pill ${s.trust_score >= 90 ? 'high' : (s.trust_score >= 70 ? 'medium' : 'low')}">
                            ${s.trust_score}%
                        </span>
                        <div style="font-size:10px; margin-top:4px; opacity:0.6;">${s.category}</div>
                    </td>
                </tr>
            `).join('');
        }
    } catch (err) {
        console.error("Trust Scores Error:", err);
    }
}

async function loadFraudAlerts() {
    try {
        const res = await fetch(`${API_BASE}/api/smart/fraud-alerts`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            const container = document.getElementById('fraud-alerts-container');
            if (data.alerts.length === 0) {
                container.innerHTML = '<p style="opacity:0.5; font-size:0.9rem; text-align:center;">No suspicious activity detected.</p>';
                return;
            }
            container.innerHTML = data.alerts.map(a => `
                <div style="background:rgba(255, 77, 77, 0.05); border-left:3px solid var(--smart-red); padding:12px; border-radius:4px; margin-bottom:10px;">
                    <div style="font-weight:700; color:var(--smart-red); font-size:0.85rem;">${a.type}</div>
                    <div style="font-size:0.8rem; margin-top:2px;">ID: ${a.student_id}</div>
                    <div style="font-size:0.75rem; opacity:0.7; margin-top:4px;">${a.details}</div>
                </div>
            `).join('');
        }
    } catch (err) {
        console.error("Fraud Alerts Error:", err);
    }
}

function renderOccupancy(data) {
    const container = document.getElementById('occupancy-container');
    if (!data || data.length === 0) {
        container.innerHTML = '<p style="opacity:0.5; text-align:center;">No data.</p>';
        return;
    }
    container.innerHTML = data.map(o => `
        <div style="margin-bottom:12px;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:5px;">
                <span>${o.department} - ${o.section}</span>
                <span style="color:var(--smart-cyan)">${o.present_count}/${o.total_students}</span>
            </div>
            <div style="height:6px; background:rgba(255,255,255,0.05); border-radius:10px; overflow:hidden;">
                <div style="width:${(o.present_count/o.total_students)*100}%; height:100%; background:var(--smart-cyan); box-shadow:0 0 10px var(--smart-cyan);"></div>
            </div>
        </div>
    `).join('');
}

async function askAI() {
    const input = document.getElementById('ai-query-input');
    const query = input.value.trim();
    if (!query) return;

    const chat = document.getElementById('ai-chat-messages');
    chat.innerHTML += `<div class="msg user-msg">${query}</div>`;
    input.value = '';
    chat.scrollTop = chat.scrollHeight;

    try {
        const res = await fetch(`${API_BASE}/api/smart/ai-assistant?q=${encodeURIComponent(query)}`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            setTimeout(() => {
                chat.innerHTML += `<div class="msg ai-msg">${data.answer}</div>`;
                chat.scrollTop = chat.scrollHeight;
            }, 500);
        }
    } catch (err) {
        console.error("AI Error:", err);
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', initSmartDashboard);
setInterval(loadLiveStats, 30000); // 5. Real-time updates every 30s
