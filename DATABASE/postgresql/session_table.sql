-- ============================================================
-- session_table.sql — Login Session Tracking (PostgreSQL)
-- ============================================================

CREATE TABLE IF NOT EXISTS login_sessions (
    id              SERIAL PRIMARY KEY,
    student_id      VARCHAR(20)  NOT NULL,
    session_token   VARCHAR(255) NOT NULL UNIQUE,
    ip_address      VARCHAR(45),
    user_agent      VARCHAR(500),
    login_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMP    NOT NULL,
    is_active       SMALLINT     NOT NULL DEFAULT 1,
    logout_at       TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_session_token    ON login_sessions (session_token);
CREATE INDEX IF NOT EXISTS idx_student_sessions ON login_sessions (student_id);
