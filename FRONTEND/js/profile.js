// ============================================================
// profile.js — Student Profile Management Logic
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    loadProfile();
});

async function loadProfile() {
    const token = localStorage.getItem('sat_token') || localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    try {
        const res = await fetch('/api/student/profile', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        const data = await res.json();
        
        if (!data.success || !data.student) {
            console.error("Failed to load live profile");
            return;
        }
        
        const student = data.student;

        // Helper to map empty to placeholder
        const fmt = (val) => (val && val.toString().trim() !== "") ? val : "Not provided";

        // Update Avatar
        const initial = (student.name || "S").charAt(0).toUpperCase();
        const avatar = document.getElementById('profile-avatar');
        if (avatar) avatar.textContent = initial;

        // Update General Info
        document.getElementById('profile-name').textContent = fmt(student.name);
        document.getElementById('profile-email').textContent = fmt(student.email);
        document.getElementById('profile-reg').textContent = fmt(student.student_id);
        document.getElementById('profile-dept').textContent = fmt(student.department);
        
        // Detailed stats mapping
        const yearEl = document.getElementById('profile-year');
        if (yearEl) {
            yearEl.textContent = student.year ? (student.year.includes("Year") ? student.year : student.year + ' Year') : "Not provided";
        }
        
        const classEl = document.getElementById('profile-class');
        if (classEl) classEl.textContent = fmt(student.class_name);
        
        const phoneEl = document.getElementById('profile-phone');
        if (phoneEl) phoneEl.textContent = fmt(student.phone);

        // Refresh global cached state just in case it drifted
        localStorage.setItem('sat_student', JSON.stringify(student));

    } catch (e) {
        console.error("Profile network error", e);
    }
}
