# Database Design — Smart Attendance System

## Tables

### students
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK AUTO_INCREMENT | |
| student_id | VARCHAR(20) UNIQUE | e.g. CS2024001 |
| name | VARCHAR(100) | |
| email | VARCHAR(150) UNIQUE | |
| phone | VARCHAR(15) | |
| password_hash | VARCHAR(255) | bcrypt |
| department | VARCHAR(100) | |
| class_name | VARCHAR(50) | |
| profile_image | VARCHAR(255) | file path |
| is_active | TINYINT(1) | soft delete |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### attendance
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| student_id | VARCHAR(20) FK→students | |
| date | DATE | |
| time | TIME | |
| status | ENUM(present,absent,late) | |
| latitude | DECIMAL(10,7) | |
| longitude | DECIMAL(10,7) | |
| location_valid | TINYINT(1) | 1=within geofence |
| face_match_status | ENUM(success,failed,not_attempted) | |
| face_confidence | FLOAT | 0.0–1.0 |
| marked_at | DATETIME | |
| remarks | VARCHAR(255) | |

**Unique constraint**: (student_id, date) — one record per day

### face_data
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| student_id | VARCHAR(20) UNIQUE FK | |
| face_descriptor | LONGTEXT | JSON array of 128 floats |
| image_path | VARCHAR(255) | path to stored face image |
| encoding_model | VARCHAR(50) | model version tag |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### login_sessions
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| student_id | VARCHAR(20) FK | |
| session_token | VARCHAR(255) UNIQUE | UUID |
| ip_address | VARCHAR(45) | |
| user_agent | VARCHAR(500) | |
| login_at | DATETIME | |
| expires_at | DATETIME | 8hrs from login |
| is_active | TINYINT(1) | |
| logout_at | DATETIME | null until logout |
