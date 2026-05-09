-- ============================================================
-- session_table.sql — Login Session Tracking
-- ============================================================

USE smart_attendance_db;

CREATE TABLE IF NOT EXISTS login_sessions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_id      VARCHAR(20)  NOT NULL,
    session_token   VARCHAR(255) NOT NULL UNIQUE,
    ip_address      VARCHAR(45),
    user_agent      VARCHAR(500),
    login_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at      DATETIME     NOT NULL,
    is_active       TINYINT(1)   NOT NULL DEFAULT 1,
    logout_at       DATETIME,

    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    INDEX idx_session_token (session_token),
    INDEX idx_student_sessions (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
