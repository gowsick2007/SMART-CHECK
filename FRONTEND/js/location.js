// ============================================================
// location.js — GPS Geolocation & Geo-fence Frontend Module
// ============================================================

let COLLEGE = null;

// Dynamically load college location configuration from backend-generated JSON
async function loadCollegeConfig() {
  try {
    let customLocStr = sessionStorage.getItem('custom_boundary_location');
    if (!customLocStr) {
      const lastLat = localStorage.getItem('last_selected_lat');
      const lastLng = localStorage.getItem('last_selected_lng');
      const lastAddress = localStorage.getItem('last_selected_address') || "Custom Campus";
      if (lastLat && lastLng) {
        const customLoc = { lat: parseFloat(lastLat), lon: parseFloat(lastLng), radius: 22.5, name: lastAddress };
        customLocStr = JSON.stringify(customLoc);
        sessionStorage.setItem('custom_boundary_location', customLocStr);
      }
    }

    if (customLocStr) {
      COLLEGE = JSON.parse(customLocStr);
      console.log("[GPS] Loaded CUSTOM college config:", COLLEGE);
    } else {
      const res = await fetch('../js/college_config.json');
      if (res.ok) {
        COLLEGE = await res.json();
        console.log("[GPS] Loaded dynamic college config:", COLLEGE);
      } else {
        console.error("[GPS] Failed to load dynamic college config");
      }
    }
  } catch (err) {
    console.error("[GPS] Error loading config:", err);
  }
}
// Initiate loading immediately
loadCollegeConfig();

// ── Google Maps Picker Logic ─────────────────────────────────
let map = null;
let mapMarker = null;
let tempSelectedLat = null;
let tempSelectedLon = null;

window.initMap = function() {
  // Callback for Google Maps
};

window.openLocationPicker = function() {
  document.getElementById('map-picker-modal').style.display = 'flex';
  
  setTimeout(() => {
    if (!map && typeof google !== 'undefined' && google.maps) {
      const defaultLoc = COLLEGE ? { lat: COLLEGE.lat, lng: COLLEGE.lon } : { lat: 10.9323, lng: 76.9770 };
      map = new google.maps.Map(document.getElementById('google-map-container'), {
        center: defaultLoc,
        zoom: 16,
        mapTypeId: 'roadmap',
        disableDefaultUI: true,
        zoomControl: true,
      });

      mapMarker = new google.maps.Marker({
        position: defaultLoc,
        map: map,
        draggable: true,
        animation: google.maps.Animation.DROP
      });

      map.addListener('click', (e) => {
        mapMarker.setPosition(e.latLng);
        tempSelectedLat = e.latLng.lat();
        tempSelectedLon = e.latLng.lng();
      });

      mapMarker.addListener('dragend', () => {
        const pos = mapMarker.getPosition();
        tempSelectedLat = pos.lat();
        tempSelectedLon = pos.lng();
      });
      
      const input = document.getElementById('map-search-input');
      if (input && google.maps.places) {
        const autocomplete = new google.maps.places.Autocomplete(input);
        autocomplete.bindTo('bounds', map);
        
        autocomplete.addListener('place_changed', () => {
          const place = autocomplete.getPlace();
          if (!place.geometry || !place.geometry.location) return;
          
          if (place.geometry.viewport) {
            map.fitBounds(place.geometry.viewport);
          } else {
            map.setCenter(place.geometry.location);
            map.setZoom(17);
          }
          
          mapMarker.setPosition(place.geometry.location);
          tempSelectedLat = place.geometry.location.lat();
          tempSelectedLon = place.geometry.location.lng();
          
          window.tempLocationName = place.name || place.formatted_address || "Custom Boundary";
        });
      }
      
      tempSelectedLat = defaultLoc.lat;
      tempSelectedLon = defaultLoc.lng;
    }
  }, 100);
};

window.closeLocationPicker = function() {
  document.getElementById('map-picker-modal').style.display = 'none';
};

window.saveSelectedLocation = function() {
  if (tempSelectedLat && tempSelectedLon) {
    const locName = window.tempLocationName || "Custom Boundary";
    const customLoc = { lat: tempSelectedLat, lon: tempSelectedLon, radius: 22.5, name: locName };
    sessionStorage.setItem('custom_boundary_location', JSON.stringify(customLoc));
    COLLEGE = customLoc;
    closeLocationPicker();
    const btn = document.querySelector('button[onclick="openLocationPicker()"]');
    if (btn) btn.textContent = 'Boundary Location Saved ✓';
    
    // Also re-verify if already watching
    if (currentPosition) {
      const result = isWithinGeofence(currentPosition.lat, currentPosition.lon);
      updateGpsUI({ lat: currentPosition.lat, lon: currentPosition.lon, accuracy: currentPosition.accuracy, ...result });
    }
  }
};


let currentPosition = null;
let locationWatchId = null;

// ── Haversine Distance ────────────────────────────────────────
function haversineDistance(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const toRad = d => d * Math.PI / 180;
  const dLat  = toRad(lat2 - lat1);
  const dLon  = toRad(lon2 - lon1);
  const a = Math.sin(dLat/2)**2 +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// ── Check if within geo-fence ─────────────────────────────────
function isWithinGeofence(lat, lon) {
  if (!COLLEGE) {
    // Fallback if config is not yet loaded or missing
    return { allowed: false, distance: 9999 };
  }
  const dist = haversineDistance(COLLEGE.lat, COLLEGE.lon, lat, lon);
  return { allowed: dist <= COLLEGE.radius, distance: Math.round(dist) };
}

// ── Start watching location ───────────────────────────────────
function startLocationWatch(onUpdate) {
  if (!navigator.geolocation) {
    updateGpsUI({ error: 'GPS not supported in this browser.' });
    return;
  }

  updateGpsUI({ loading: true });

  locationWatchId = navigator.geolocation.watchPosition(
    (pos) => {
      const { latitude, longitude, accuracy } = pos.coords;
      currentPosition = { lat: latitude, lon: longitude, accuracy };
      const result = isWithinGeofence(latitude, longitude);
      updateGpsUI({ lat: latitude, lon: longitude, accuracy, ...result });
      if (onUpdate) onUpdate(currentPosition, result);
    },
    (err) => {
      let msg = 'Location access denied.';
      if (err.code === 1) msg = 'Location permission denied. Please allow in browser settings.';
      else if (err.code === 2) msg = 'Location unavailable. Check GPS signal.';
      else if (err.code === 3) msg = 'Location request timed out.';
      updateGpsUI({ error: msg });
    },
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 5000 }
  );
}

function stopLocationWatch() {
  if (locationWatchId !== null) {
    navigator.geolocation.clearWatch(locationWatchId);
    locationWatchId = null;
  }
}

function getCurrentPosition() { return currentPosition; }

// ── Update GPS UI elements ────────────────────────────────────
function updateGpsUI({ loading, error, allowed, distance, lat, lon, accuracy }) {
  const indicator   = document.getElementById('gps-indicator');
  const gpsText     = document.getElementById('gps-text');
  const checkGps    = document.getElementById('check-gps');

  // New boundary visual elements
  const visual      = document.getElementById('gps-boundary-visual');
  const statusText  = document.getElementById('gps-status-text');
  const subText     = document.getElementById('gps-subtext');
  const distBadge   = document.getElementById('gps-distance-badge');

  if (loading) {
    if (indicator)   indicator.className = 'gps-indicator loading';
    if (gpsText)     gpsText.textContent = 'Requesting GPS location…';
    if (checkGps)    { checkGps.textContent = 'Checking…'; checkGps.className = 'check-status check-wait'; }
    if (visual)      { visual.className = 'gps-boundary-visual large'; }
    if (statusText)  { statusText.textContent = 'REQUESTING LOCATION'; statusText.className = 'gps-status-text'; }
    if (subText)     subText.textContent = 'Waiting for GPS signal…';
    if (distBadge)   distBadge.style.display = 'none';
    return;
  }

  if (error) {
    if (indicator)   indicator.className = 'gps-indicator outside';
    if (gpsText)     gpsText.textContent = error;
    if (checkGps)    { checkGps.textContent = 'Error'; checkGps.className = 'check-status check-fail'; }
    if (visual)      visual.className = 'gps-boundary-visual large outside';
    if (statusText)  { statusText.textContent = 'GPS UNAVAILABLE'; statusText.className = 'gps-status-text outside'; }
    if (subText)     subText.textContent = error;
    if (distBadge)   distBadge.style.display = 'none';
    return;
  }

  const distStr = distance >= 1000 ? `${(distance/1000).toFixed(2)} km` : `${distance} m`;

  const topStatus = document.getElementById('top-left-location-status');
  const topStatusText = document.getElementById('top-left-location-text');

  if (allowed) {
    if (indicator)   indicator.className = 'gps-indicator inside';
    if (gpsText)     gpsText.textContent = `Location Verified — ${distStr}`;
    if (checkGps)    { checkGps.textContent = 'Inside'; checkGps.className = 'check-status check-ok'; }
    if (visual)      visual.className = 'gps-boundary-visual large inside';
    if (statusText)  { statusText.textContent = 'INSIDE BOUNDARY'; statusText.className = 'gps-status-text inside'; }
    if (subText)     subText.textContent = 'Location verified successfully';
    if (distBadge)   { distBadge.style.display = 'inline-block'; distBadge.textContent = `${distStr} from campus center`; }
    if (document.getElementById('continue-face-btn')) document.getElementById('continue-face-btn').style.display = 'block';
    if (topStatus) {
      topStatus.style.display = 'flex';
      topStatusText.textContent = COLLEGE && COLLEGE.name ? COLLEGE.name : `Lat: ${lat.toFixed(4)}, Lon: ${lon.toFixed(4)}`;
    }
  } else {
    if (indicator)   indicator.className = 'gps-indicator outside';
    if (gpsText)     gpsText.textContent = `${distStr} away — must be within ${COLLEGE.radius}m`;
    if (checkGps)    { checkGps.textContent = 'Outside'; checkGps.className = 'check-status check-fail'; }
    if (visual)      visual.className = 'gps-boundary-visual large outside';
    if (statusText)  { statusText.textContent = 'OUTSIDE BOUNDARY'; statusText.className = 'gps-status-text outside'; }
    if (subText)     subText.textContent = `Move to within ${COLLEGE.radius}m of campus`;
    if (distBadge)   { distBadge.style.display = 'inline-block'; distBadge.textContent = `${distStr} away from boundary`; }
    if (document.getElementById('continue-face-btn')) document.getElementById('continue-face-btn').style.display = 'none';
    if (topStatus) {
      topStatus.style.display = 'flex';
      topStatusText.textContent = 'Outside Location';
      topStatus.querySelector('.glowing-green-dot').style.backgroundColor = 'var(--accent-red)';
      topStatus.querySelector('.glowing-green-dot').style.boxShadow = '0 0 8px var(--accent-red)';
      topStatus.style.color = 'var(--accent-red)';
      topStatus.style.borderColor = 'rgba(239, 68, 68, 0.3)';
    }
  }
}

// ── One-shot position fetch ───────────────────────────────────
function fetchCurrentPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) { reject(new Error('GPS not supported')); return; }
    navigator.geolocation.getCurrentPosition(
      pos => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: pos.coords.accuracy }),
      err => reject(err),
      { enableHighAccuracy: true, timeout: 15000 }
    );
  });
}

// ── GPS Permission Flow Override ──────────────────────────────
// This cleanly overrides any existing onclick logic set by attendance.js
// and ensures the flow strictly follows the new requirements.
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('enable-gps-btn');
  if (btn) {
    // Remove the inline onclick attribute
    btn.removeAttribute('onclick');
    // Attach our robust permission handler
    btn.addEventListener('click', () => handleGpsPermissionFlow(false));
  }

  // Auto-start if session permission is granted
  if (sessionStorage.getItem('gps_permission_granted') === 'true') {
    handleGpsPermissionFlow(true);
  }
});

async function handleGpsPermissionFlow(isAuto = false) {
  const btn = document.getElementById('enable-gps-btn');
  const errEl = document.getElementById('gps-perm-error');
  
  if (!isAuto && btn) { btn.disabled = true; btn.textContent = 'Requesting Location...'; }
  if (errEl) errEl.style.display = 'none';

  if (!navigator.geolocation) {
    if (errEl) { errEl.textContent = 'Geolocation is not supported by your browser.'; errEl.style.display = 'block'; }
    if (btn) { btn.disabled = false; btn.textContent = 'Enable Location Access'; }
    return;
  }

  // Ensure config is loaded before we process the coordinates
  if (!COLLEGE) await loadCollegeConfig();

  try {
    // 1. Automatically trigger browser popup using the API directly
    const pos = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, { 
        enableHighAccuracy: true, timeout: 20000, maximumAge: 0 
      });
    });
    
    // Save session permission state
    sessionStorage.setItem('gps_permission_granted', 'true');

    // 2. Fetch current latitude and longitude
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    
    // 3. Compare with college coordinates dynamically loaded
    const result = isWithinGeofence(lat, lon);
    
    // 4. If Allowed GPS, open dashboard (either inside or outside boundary UI)
    const overlay = document.getElementById('gps-permission-overlay');
    const content = document.getElementById('dashboard-content');
    if (overlay) overlay.style.display = 'none';
    if (content) content.style.display = 'block';

    // 5. Trigger UI updates based on inside/outside radius
    updateGpsUI({ lat, lon, accuracy: pos.coords.accuracy, ...result });

    // 6. Start continuous tracking for dynamic movement
    startLocationWatch((pos, res) => {
      window.gpsResult = res; // Make available globally
    });

  } catch (err) {
    // USER DENIES GPS -> block dashboard, show warning screen
    if (btn) { btn.disabled = false; btn.textContent = 'Enable Location Access'; }
    if (errEl) {
      errEl.textContent = 'Location access was denied. Please allow it in your browser settings and retry.';
      errEl.style.display = 'block';
    }
  }
}

function updateLocationManually() {
  const btn = document.getElementById('updateLocationBtn');
  if(btn) btn.innerText = '🔄 Updating...';
  navigator.geolocation.getCurrentPosition(function(position) {
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;
    localStorage.setItem('userLat', lat);
    localStorage.setItem('userLng', lng);
    // re-run existing boundary check
    if(typeof checkBoundary === 'function') checkBoundary(lat, lng);
    
    // Call the actual update functions if available
    if(typeof isWithinGeofence === 'function' && typeof updateGpsUI === 'function') {
      const res = isWithinGeofence(lat, lng);
      updateGpsUI({ lat, lon: lng, accuracy: position.coords.accuracy, ...res });
    }
    
    showToast('✅ Location Updated Successfully');
    if(btn) btn.innerText = '🔄 Update Location';
  }, function(error) {
    showToast('❌ Location access denied');
    if(btn) btn.innerText = '🔄 Update Location';
  });
}
function showToast(msg) {
  // Check if toast container exists from auth.js to avoid duplicates or overriding
  if (document.getElementById('toast-container')) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast success';
    toast.textContent = msg.replace(/^[✅❌]\s*/, ''); // Remove emoji for existing toast styling if wanted, or keep it
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
    return;
  }
  
  const toast = document.createElement('div');
  toast.innerText = msg;
  toast.style.cssText = 'position:fixed;bottom:30px;right:30px;background:#00ffcc;color:#000;padding:12px 24px;border-radius:8px;font-weight:bold;z-index:9999;animation:fadeOut 3s forwards;';
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ── Global Window Aliases for Button Event Handlers ─────────
window.updateLocation = updateLocationManually;
window.updateLocationManually = updateLocationManually;
window.chooseBoundaryLocation = function() {
  window.location.href = 'map_select.html';
};
window.confirmLocation = function() {
  if (typeof confirmLocation === 'function') {
    confirmLocation();
  }
};

