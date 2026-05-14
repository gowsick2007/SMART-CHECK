// ============================================================
// settings.js — User Preferences & System Settings
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
});

function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('user_settings') || '{}');
    
    // Set defaults
    if (settings.darkMode === undefined) settings.darkMode = true;
    if (settings.notifications === undefined) settings.notifications = true;
    if (settings.animations === undefined) settings.animations = true;

    // Apply to UI
    document.getElementById('toggle-dark-mode').checked = settings.darkMode;
    document.getElementById('toggle-notifications').checked = settings.notifications;
    document.getElementById('toggle-animations').checked = settings.animations;
    
    applyTheme(settings.darkMode);
}

function saveSetting(key, value) {
    const settings = JSON.parse(localStorage.getItem('user_settings') || '{}');
    settings[key] = value;
    localStorage.setItem('user_settings', JSON.stringify(settings));
    
    if (key === 'darkMode') applyTheme(value);
    
    window.showToast(`Setting updated: ${key}`, 'success');
}

function applyTheme(isDark) {
    if (isDark) {
        document.body.classList.add('dark-mode');
        document.body.classList.remove('light-mode');
    } else {
        document.body.classList.add('light-mode');
        document.body.classList.remove('dark-mode');
    }
}

function resetAll() {
    if (confirm("Are you sure you want to reset all settings to default?")) {
        localStorage.removeItem('user_settings');
        location.reload();
    }
}
