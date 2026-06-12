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
    if (!document.getElementById('hub-present')) return;
    await loadLiveStats();
    await loadTrustScores();
    await loadFraudAlerts();
    await loadLateArrivals();
    await loadForecast();
}

async function loadLiveStats() {
    try {
        const res = await fetch(`${API_BASE}/api/smart/summary`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            document.getElementById('hub-present').textContent = data.stats.total_present || 0;
            document.getElementById('hub-absent').textContent = data.stats.total_absent || 0;
            document.getElementById('hub-face').textContent = data.stats.face_verified || 0;
            document.getElementById('hub-inside').textContent = data.stats.inside_boundary || 0;
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
            const tbody = document.getElementById('smart-trust-body');
            tbody.innerHTML = data.scores.slice(0, 8).map(s => `
                <tr>
                    <td>
                        <div style="font-weight:700; color:#fff;">${s.name}</div>
                        <div style="font-size:10px; opacity:0.5;">${s.student_id}</div>
                    </td>
                    <td style="text-align:right;">
                        <span class="trust-pill ${s.trust_score >= 90 ? 'trust-high' : (s.trust_score >= 70 ? 'trust-med' : 'trust-low')}">
                            ${s.trust_score}%
                        </span>
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
            const container = document.getElementById('smart-fraud-alerts');
            if (data.alerts.length === 0) {
                container.innerHTML = '<p style="opacity:0.5; font-size:0.8rem; text-align:center; padding-top:20px;">No threats detected.</p>';
                return;
            }
            container.innerHTML = data.alerts.map(a => `
                <div class="fraud-alert-item">
                    <strong>${a.type}</strong>
                    <span>ID: ${a.student_id} - ${a.details}</span>
                </div>
            `).join('');
        }
    } catch (err) {
        console.error("Fraud Alerts Error:", err);
    }
}

function renderOccupancy(data) {
    const container = document.getElementById('smart-occupancy-list');
    if (!data || data.length === 0) {
        container.innerHTML = '<p style="opacity:0.5; text-align:center;">No data.</p>';
        return;
    }
    container.innerHTML = data.map(o => `
        <div class="occupancy-bar-wrap">
            <div class="occ-label">
                <span>${o.department} ${o.section}</span>
                <span>${o.present_count}/${o.total_students}</span>
            </div>
            <div class="occ-bar-bg">
                <div class="occ-bar-fill" style="width:${(o.present_count/o.total_students)*100}%"></div>
            </div>
        </div>
    `).join('');
}

async function loadLateArrivals() {
    try {
        const res = await fetch(`${API_BASE}/api/smart/late-arrivals?period=daily`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            const container = document.getElementById('smart-late-arrivals');
            const lates = data.arrivals.filter(a => a.category !== 'On Time');
            if (lates.length === 0) {
                container.innerHTML = 'All students arrived on time today.';
            } else {
                container.innerHTML = lates.slice(0, 3).map(a => 
                    `• ${a.name} (${a.category} - ${a.delay}m)`
                ).join('<br>');
            }
        }
    } catch (err) {}
}

async function loadForecast() {
    // Forecast is calculated on AI request or for a sample student for UI placeholder
    document.getElementById('smart-forecast-info').textContent = "78% Expected turnout tomorrow based on weekly velocity.";
} 

async function askAISmart() {
    const input = document.getElementById('ai-smart-query');
    const query = input.value.trim();
    if (!query) return;

    const output = document.getElementById('ai-chat-output');
    output.innerHTML = `<em>Querying IQ...</em><br>Q: ${query}`;
    input.value = '';

    try {
        const res = await fetch(`${API_BASE}/api/smart/ai-assistant?q=${encodeURIComponent(query)}`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            output.innerHTML = `<strong>Assistant:</strong><br>${data.answer}`;
        }
    } catch (err) {
        output.innerHTML = "Error connecting to AI Assistant.";
    }
}
window.askAISmart = askAISmart;

// Initialize on load
document.addEventListener('DOMContentLoaded', initSmartDashboard);
setInterval(loadLiveStats, 30000); // 5. Real-time updates every 30s
