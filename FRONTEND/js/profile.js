// ============================================================
// profile.js — Student Profile Management Logic
// ============================================================

async function loadProfile() {
    const token = localStorage.getItem('sat_token') || localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    try {
        const res = await fetch('https://smart-check-production.up.railway.app/api/student/profile', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        const data = await res.json();
        
        if (!data.success || !data.student) {
            console.error("Profile load failed:", data.message);
            return;
        }
        
        const student = data.student;

        // Update UI elements with exact IDs from profile.html
        const avatarEl = document.getElementById('profile-avatar');
        if (avatarEl) {
            avatarEl.textContent = (student.name || "S").charAt(0).toUpperCase();
        }

        const nameEl = document.getElementById('profile-name');
        if (nameEl) nameEl.textContent = student.name || "N/A";

        const emailEl = document.getElementById('profile-email');
        if (emailEl) emailEl.textContent = student.email || "N/A";

        const regEl = document.getElementById('profile-reg');
        if (regEl) regEl.textContent = student.student_id || "N/A";

        const deptEl = document.getElementById('profile-dept');
        if (deptEl) deptEl.textContent = student.department || "N/A";

        const yearEl = document.getElementById('profile-year');
        if (yearEl) {
            let yr = student.year || "";
            yearEl.textContent = yr.toString().includes("Year") ? yr : (yr ? yr + " Year" : "Not provided");
        }

        const classEl = document.getElementById('profile-class');
        if (classEl) classEl.textContent = student.class_name || "Not provided";

        const phoneEl = document.getElementById('profile-phone');
        if (phoneEl) phoneEl.textContent = student.phone || "Not provided";

        // Sync local storage
        localStorage.setItem('sat_student', JSON.stringify(student));

    } catch (e) {
        console.error("Profile network error:", e);
    }
}

// Call directly since script is at the end of body
loadProfile();
