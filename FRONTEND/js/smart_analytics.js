// ============================================================
// smart_analytics.js — Frontend logic for Command Center
// ============================================================

// Use global API_BASE if defined in auth.js, else fallback to empty
const SMART_API_BASE = (typeof API_BASE !== 'undefined') ? API_BASE : '';

function authHeaders() {
    const token = localStorage.getItem('sat_token') || localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

async function initSmartDashboard() {
    if (!document.getElementById('hub-present')) return;
    console.log("Initializing Smart Intelligence Hub...");
    await loadLiveStats();
    await loadTrustScores();
    await loadFraudAlerts();
    await loadGPSHeatmap();
    await loadLateArrivals();
    await loadForecast();
    await loadAchievements();
}

async function loadLiveStats() {
    try {
        const res = await fetch(`${SMART_API_BASE}/api/smart/summary`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            document.getElementById('hub-present').textContent = data.stats.total_present || 0;
            document.getElementById('hub-absent').textContent = data.stats.total_absent || 0;
            document.getElementById('hub-face').textContent = data.stats.face_verified || 0;
            document.getElementById('hub-inside').textContent = data.stats.inside_boundary || 0;
            renderOccupancy(data.occupancy);

            // Render GPS Analytics into the Fraud/GPS card header or top
            const gpsBody = document.getElementById('smart-fraud-alerts');
            if (data.gps_analytics) {
                const g = data.gps_analytics;
                let gpsHtml = `
                    <div style="background:rgba(0,153,255,0.1); border:1px solid rgba(0,153,255,0.2); border-radius:8px; padding:10px; margin-bottom:12px; font-size:11px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span>Boundary Edge Attempts:</span> <strong>${g.edge_attempts}</strong>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span>Outside Boundary Attempts:</span> <strong>${g.outside_attempts}</strong>
                        </div>
                        <div style="display:flex; justify-content:space-between;">
                            <span>GPS Consistency Score:</span> <strong>${g.avg_distance}m avg</strong>
                        </div>
                    </div>
                `;
                // Prepends to the alerts container
                const existing = gpsBody.querySelector('.gps-analytics-strip');
                if (existing) existing.remove();
                gpsBody.insertAdjacentHTML('afterbegin', `<div class="gps-analytics-strip">${gpsHtml}</div>`);
            }
        }
    } catch (err) {
        console.error("Live Stats Error:", err);
    }
}

async function loadTrustScores() {
    try {
        const res = await fetch(`${SMART_API_BASE}/api/smart/trust-scores`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            const tbody = document.getElementById('smart-trust-body');
            if (!data.scores || data.scores.length === 0) {
                tbody.innerHTML = '<tr><td colspan="2" style="text-align:center; opacity:0.5; padding:20px;">No records found</td></tr>';
                return;
            }
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
        const res = await fetch(`${SMART_API_BASE}/api/smart/fraud-alerts`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            const container = document.getElementById('smart-fraud-alerts');
            if (!data.alerts || data.alerts.length === 0) {
                container.innerHTML = '<p style="opacity:0.5; font-size:0.8rem; text-align:center; padding-top:20px;">No records found</p>';
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

async function loadGPSHeatmap() {
    try {
        const res = await fetch(`${SMART_API_BASE}/api/smart/gps-heatmap`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            const container = document.getElementById('smart-gps-heatmap');
            if (!data.heatmap || data.heatmap.length === 0) {
                container.innerHTML = '<p style="opacity:0.5; font-size:0.8rem; text-align:center; padding-top:20px;">No density patterns found.</p>';
                return;
            }
            container.innerHTML = data.heatmap.slice(0, 10).map(h => `
                <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:11px; padding:5px; border-bottom:1px solid rgba(255,255,255,0.05);">
                    <span><i class="fas fa-location-crosshairs" style="color:#00ffcc"></i> ${h.lat}, ${h.lng}</span>
                    <span style="color:#ff9f43; font-weight:700;">Intensity: ${h.intensity}</span>
                </div>
            `).join('');
        }
    } catch (err) { console.error('GPS heatmap error:', err); }
}

function renderOccupancy(data) {
    const container = document.getElementById('smart-occupancy-list');
    if (!data || data.length === 0) {
        container.innerHTML = '<p style="opacity:0.5; text-align:center; padding:20px;">No records found</p>';
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
        const res = await fetch(`${SMART_API_BASE}/api/smart/late-arrivals?period=daily`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            const container = document.getElementById('smart-late-arrivals');
            const lates = (data.arrivals || []).filter(a => a.category !== 'On Time');
            if (lates.length === 0) {
                container.innerHTML = '<span style="opacity:0.5;">No records found.</span>';
            } else {
                container.innerHTML = lates.slice(0, 3).map(a => 
                    `• ${a.name} (${a.category} - ${a.delay}m)`
                ).join('<br>');
            }
        }
    } catch (err) {}
}

async function loadForecast() {
    try {
        const res = await fetch(`${SMART_API_BASE}/api/smart/trust-scores`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success && data.scores && data.scores.length > 0) {
            const top = data.scores[0];
            const fRes = await fetch(`${SMART_API_BASE}/api/smart/forecast/${top.student_id}`, { headers: authHeaders() });
            const fData = await fRes.json();
            if (fData.success) {
                document.getElementById('smart-forecast-info').innerHTML = `
                    <div style="color:#00ffcc;">${top.name}</div>
                    <div style="font-size:11px; opacity:0.7;">
                        If Present: <strong>${fData.forecast_10_days_present}%</strong> (next 10d)<br>
                        If Absent: <strong>${fData.forecast_10_days_absent}%</strong> (next 10d)<br>
                        Exam Risk (3d Abs): <strong>${fData.prediction_3_days_absent}%</strong>
                    </div>
                `;
            } else {
                document.getElementById('smart-forecast-info').innerHTML = '<span style="opacity:0.5;">No forecast available.</span>';
            }
        } else {
            document.getElementById('smart-forecast-info').innerHTML = '<span style="opacity:0.5;">No records found.</span>';
        }
    } catch (err) {
        document.getElementById('smart-forecast-info').innerHTML = '<span style="opacity:0.5;">No records found.</span>';
    }
}

async function loadAchievements() {
    try {
        const res = await fetch(`${SMART_API_BASE}/api/smart/achievements`, { headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            const chamber = document.querySelector('.badge-chamber');
            // Clean up existing dynamic text if any
            const existingLabels = chamber.parentElement.querySelectorAll('.dynamic-achievement');
            existingLabels.forEach(el => el.remove());

            if (!data.achievements) {
                chamber.innerHTML = '<div style="opacity:0.5; font-size:12px; padding:20px; text-align:center;">No records found</div>';
                return;
            }

            const perfectNames = (data.achievements.perfect_score || []).map(s => s.name).slice(0,2).join(', ');
            const highNames = (data.achievements.high_attendancy || []).map(s => s.name).slice(0,2).join(', ');
            const streakNames = (data.achievements.streaks || []).map(s => s.name).slice(0,2).join(', ');
            
            if (!perfectNames && !highNames && !streakNames) {
                chamber.innerHTML = '<div style="opacity:0.5; font-size:12px; padding:20px; text-align:center;">No records found</div>';
                return;
            }

            if (perfectNames) {
                chamber.insertAdjacentHTML('afterend', `<div class="dynamic-achievement" style="font-size:10px; color:gold; margin-top:5px;">100% Club: ${perfectNames}+</div>`);
            }
            if (highNames) {
                chamber.insertAdjacentHTML('afterend', `<div class="dynamic-achievement" style="font-size:10px; color:#38ef7d; margin-top:5px;">95% Club: ${highNames}+</div>`);
            }
            if (streakNames) {
                chamber.insertAdjacentHTML('afterend', `<div class="dynamic-achievement" style="font-size:10px; color:#ff9f43; margin-top:5px;">30-Day Streaks: ${streakNames}+</div>`);
            }
        }
    } catch (err) {}
}
async function askAISmart() {
    const input = document.getElementById('ai-smart-query');
    const query = input.value.trim();
    if (!query) return;

    const output = document.getElementById('ai-chat-output');
    output.innerHTML = `<div style="opacity:0.7;"><i class="fas fa-microchip fa-spin"></i> Analyzing data...</div>`;
    input.value = '';

    try {
        const res = await fetch(`${SMART_API_BASE}/api/smart/ai-assistant?q=${encodeURIComponent(query)}`, { headers: authHeaders() });
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
