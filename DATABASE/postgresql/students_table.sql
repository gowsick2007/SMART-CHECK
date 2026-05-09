-- ============================================================
-- students_table.sql — Students Table Schema (PostgreSQL)
-- ============================================================

CREATE TABLE IF NOT EXISTS students (
    id              SERIAL PRIMARY KEY,
    student_id      VARCHAR(20)  NOT NULL UNIQUE,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    phone           VARCHAR(15),
    password_hash   VARCHAR(255) NOT NULL,
    department      VARCHAR(100) NOT NULL,
    year            VARCHAR(20)  NOT NULL DEFAULT '',
    class_name      VARCHAR(50)  NOT NULL DEFAULT '',
    profile_image   VARCHAR(255),
    is_active       SMALLINT     NOT NULL DEFAULT 1,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_student_id   ON students (student_id);
CREATE INDEX IF NOT EXISTS idx_email        ON students (email);
CREATE INDEX IF NOT EXISTS idx_department   ON students (department);
