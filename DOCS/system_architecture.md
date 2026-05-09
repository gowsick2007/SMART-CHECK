# System Architecture — Smart Attendance System

## Overview

```
┌─────────────────────────────────────────────────────┐
│                    BROWSER (Student)                │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  face-api.js │  │ Geolocation  │  │  HTML/CSS │  │
│  │  (Face Det.) │  │   API (GPS)  │  │    UI     │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┘  │
└─────────┼────────────────┼───────────────────────────┘
          │ 128-d vector   │ lat/lon
          └────────┬───────┘
                   │ HTTPS REST API
          ┌────────▼───────────────────────────────────┐
          │           FLASK BACKEND (Python)           │
          │  ┌──────────┐  ┌───────────┐  ┌────────┐  │
          │  │   Auth   │  │ Attendance │  │  Face  │  │
          │  │ Service  │  │  Service  │  │Service │  │
          │  └──────────┘  └───────────┘  └────────┘  │
          │  ┌────────────────────────────────────┐    │
          │  │         Geofence Service           │    │
          │  │    Haversine Distance Calculator   │    │
          │  └────────────────────────────────────┘    │
          └────────────────────┬───────────────────────┘
                               │
          ┌────────────────────▼───────────────────────┐
          │              MySQL Database                │
          │  students | attendance | face_data | sessions│
          └────────────────────────────────────────────┘
```

## Attendance Flow

1. Student opens dashboard → GPS watch starts
2. Camera activates → face-api.js loads models
3. System checks: GPS within 200m of college?
4. System checks: Face enrolled?
5. face-api.js detects face live → extracts 128-d descriptor
6. Student clicks "Mark Attendance"
7. API receives: lat, lon, face_descriptor
8. Backend validates GPS (Haversine distance)
9. Backend compares face descriptor vs stored (L2 distance < 0.5)
10. Both pass → attendance marked as present/late
11. Record saved with timestamp, GPS, face confidence

## Security

- Passwords: bcrypt hashed
- Sessions: UUID token in DB with expiry
- No JWT — stateful session (simpler, revocable)
- CORS restricted to frontend origin
- Face data: 128-d float vectors (not raw images in attendance flow)
