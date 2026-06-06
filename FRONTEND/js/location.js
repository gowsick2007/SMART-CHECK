// ============================================================
// location.js — Google Maps & Geo-fence Logic
// ============================================================

// GLOBAL VARIABLES
let selectedLat = null;
let selectedLng = null;
let selectedRadius = 100;

let map = null;
let marker = null;
let circle = null;

// Ensure map initializes only when DOM is ready
function initMap() {
    console.log("Google Maps Initializing...");
    const mapElement = document.getElementById('google-map-container') || document.getElementById('map');
    
    if (!mapElement) {
        console.error("Map container not found! Ensure #google-map-container exists.");
        return;
    }

    const defaultLoc = { lat: 10.9323, lng: 76.9770 };

    map = new google.maps.Map(mapElement, {
        center: defaultLoc,
        zoom: 16,
        mapTypeId: 'roadmap',
        disableDefaultUI: false,
        zoomControl: true,
    });

    marker = new google.maps.Marker({
        position: defaultLoc,
        map: map,
        draggable: true,
        animation: google.maps.Animation.DROP
    });

    circle = new google.maps.Circle({
        map: map,
        radius: selectedRadius,
        fillColor: '#00ffcc',
        fillOpacity: 0.2,
        strokeColor: '#00ffcc',
        strokeOpacity: 0.8,
        strokeWeight: 2
    });
    circle.bindTo('center', marker, 'position');

    // Clicking map MUST:
    map.addListener('click', (e) => {
        const latLng = e.latLng;
        marker.setPosition(latLng);
        
        // Save latitude/longitude
        selectedLat = latLng.lat();
        selectedLng = latLng.lng();

        // Update selected values globally
        console.log("Selected:", selectedLat, selectedLng);
        console.log("Marker placed");
        console.log("Boundary updated");
    });

    marker.addListener('dragend', () => {
        const pos = marker.getPosition();
        selectedLat = pos.lat();
        selectedLng = pos.lng();
        console.log("Selected:", selectedLat, selectedLng);
        console.log("Marker placed");
        console.log("Boundary updated");
    });

    // Handle Search/Autocomplete if element exists
    const input = document.getElementById('map-search-input') || document.getElementById('pac-input');
    if (input && google.maps.places) {
        const autocomplete = new google.maps.places.Autocomplete(input);
        autocomplete.bindTo('bounds', map);
        autocomplete.addListener('place_changed', () => {
            const place = autocomplete.getPlace();
            if (!place.geometry || !place.geometry.location) return;
            
            if (place.geometry.viewport) map.fitBounds(place.geometry.viewport);
            else map.setCenter(place.geometry.location);
            
            marker.setPosition(place.geometry.location);
            selectedLat = place.geometry.location.lat();
            selectedLng = place.geometry.location.lng();
            console.log("Selected:", selectedLat, selectedLng);
            console.log("Marker placed");
            console.log("Boundary updated");
        });
    }

    console.log("Google Maps Initialized Successfully");
}

// Global exposure
window.initMap = initMap;

async function saveBoundaryLocation() {
    // Confirm/save button MUST: verify values exist
    if (selectedLat === null || selectedLng === null) {
        await showWarningToast("Please select a location on the map");
        return;
    }

    const payload = {
        latitude: selectedLat,
        longitude: selectedLng,
        address: "Campus Boundary"
    };

    const token = localStorage.getItem('sat_token');
    try {
        const res = await fetch('/api/location/save-boundary', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        
        if (data.success) {
            localStorage.setItem('locationVerified', 'true');
            localStorage.setItem('boundaryLat', selectedLat);
            localStorage.setItem('boundaryLng', selectedLng);
            
            // Continue to dashboard properly via absolute route
            window.location.href = '/dashboard';
        } else {
            await showErrorToast(data.message || "Failed to save location");
        }
    } catch (err) {
        console.error("Save Error:", err);
        await showErrorToast("Server connection failed");
    }
}

// Global exposure for buttons
window.saveBoundaryLocation = saveBoundaryLocation;
window.saveSelectedLocation = saveBoundaryLocation; // Alias for different button calls
window.confirmLocation = saveBoundaryLocation;     // Alias for different button calls

// For dashboard logic if needed
// ============================================================
// STEP 5: BOUNDARY FIX (MAIN BUG) — EXACT CODE IMPLEMENTATION
// ============================================================
function getDistance(lat1, lon1, lat2, lon2) {
    const R = 6371e3;
    const φ1 = lat1 * Math.PI/180;
    const φ2 = lat2 * Math.PI/180;
    const Δφ = (lat2-lat1) * Math.PI/180;
    const Δλ = (lon2-lon1) * Math.PI/180;

    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}
window.haversineDistance = getDistance; // Alias to ensure existing dependencies inherit the new logic
window.getDistance = getDistance;
