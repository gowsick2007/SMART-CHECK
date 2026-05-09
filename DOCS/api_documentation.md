# ============================================================
# API Documentation — Smart Attendance System
# ============================================================

## Base URL
`http://127.0.0.1:5000`

---

## Auth Endpoints `/api/auth`

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/auth/register` | Register new student |
| POST | `/api/auth/login` | Login and get session token |
| POST | `/api/auth/logout` | Invalidate session |
| GET  | `/api/auth/validate` | Check if token is valid |

### POST /api/auth/register
```json
{
  "student_id": "CS2024001",
  "name": "John Doe",
  "email": "john@college.edu",
  "phone": "+91 9876543210",
  "password": "securepass123",
  "department": "Computer Science",
  "class_name": "III Year"
}
```

### POST /api/auth/login
```json
{ "identifier": "CS2024001", "password": "securepass123" }
```
Response:
```json
{ "success": true, "token": "uuid-session-token", "student": { ... } }
```

---

## Student Endpoints `/api/student`
> **All require** `Authorization: Bearer <token>` header

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/student/profile` | Get current student profile |
| GET | `/api/student/all` | List all students (filter by dept/class) |
| GET | `/api/student/<student_id>` | Get specific student |

---

## Attendance Endpoints `/api/attendance`
> **All require** `Authorization: Bearer <token>` header

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/attendance/mark` | Auto-mark attendance |
| GET  | `/api/attendance/history` | Get attendance history |
| GET  | `/api/attendance/summary` | Get stats (present/absent/late counts) |
| GET  | `/api/attendance/range` | Get records by date range |

### POST /api/attendance/mark
```json
{
  "latitude": 13.0827,
  "longitude": 80.2707,
  "face_descriptor": [0.123, -0.456, ...] // 128 floats
}
```

---

## Face Endpoints `/api/face`
> **All require** `Authorization: Bearer <token>` header

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/face/enroll` | Enroll face from base64 image |
| POST | `/api/face/verify` | Verify live face against stored |
| POST | `/api/face/identify` | Identify unknown student |

### POST /api/face/enroll
```json
{ "image_base64": "data:image/jpeg;base64,/9j/..." }
```

---

## Health Check
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/health` | Server health check |
