-- ============================================================
-- face_data_table.sql — Face Descriptor / Encoding Storage
-- ============================================================

USE smart_attendance_db;

CREATE TABLE IF NOT EXISTS face_data (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_id      VARCHAR(20)  NOT NULL UNIQUE,
    face_descriptor LONGTEXT     NOT NULL,  -- JSON array of 128-d face encodings
    image_path      VARCHAR(255),           -- path to stored face reference image
    encoding_model  VARCHAR(50)  NOT NULL DEFAULT 'face_recognition_v1',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    INDEX idx_student_face (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
