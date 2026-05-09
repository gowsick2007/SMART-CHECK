-- ============================================================
-- attendance_table.sql — Attendance Records Schema
-- ============================================================

USE smart_attendance_db;

CREATE TABLE IF NOT EXISTS attendance (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    student_id          VARCHAR(20)  NOT NULL,
    date                DATE         NOT NULL,
    time                TIME         NOT NULL,
    status              ENUM('present', 'absent', 'late') NOT NULL DEFAULT 'absent',
    latitude            DECIMAL(10, 7),
    longitude           DECIMAL(10, 7),
    location_valid      TINYINT(1)   NOT NULL DEFAULT 0,  -- 1 = within geo-fence
    face_match_status   ENUM('success', 'failed', 'not_attempted') NOT NULL DEFAULT 'not_attempted',
    face_confidence     FLOAT,                             -- 0.0 to 1.0
    marked_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    remarks             VARCHAR(255),

    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    INDEX idx_student_date (student_id, date),
    INDEX idx_date (date),
    UNIQUE KEY unique_attendance (student_id, date)        -- one record per student per day
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS auto_verify_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id VARCHAR(20) NOT NULL,
  check_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  latitude DECIMAL(10,8),
  longitude DECIMAL(11,8),
  distance_meters DECIMAL(10,2),
  gps_status ENUM('inside','outside'),
  final_status ENUM('present','absent'),
  INDEX idx_student (student_id),
  INDEX idx_time (check_time)
);

