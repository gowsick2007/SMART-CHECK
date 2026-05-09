-- ============================================================
-- students_table.sql — Students Table Schema
-- PATCH: Added separate `year` and `class_section` columns.
--        `class_name` kept as alias column for compatibility.
-- ============================================================

CREATE DATABASE IF NOT EXISTS smart_attendance_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE smart_attendance_db;

CREATE TABLE IF NOT EXISTS students (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_id      VARCHAR(20)  NOT NULL UNIQUE,   -- e.g., "2024001"
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    phone           VARCHAR(15),
    password_hash   VARCHAR(255) NOT NULL,
    department      VARCHAR(100) NOT NULL,
    year            VARCHAR(20)  NOT NULL DEFAULT '',  -- e.g., "I Year", "II Year"
    class_name      VARCHAR(50)  NOT NULL DEFAULT '',  -- e.g., "Section A", "Section B"
    profile_image   VARCHAR(255),
    is_active       TINYINT(1)   NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_student_id (student_id),
    INDEX idx_email (email),
    INDEX idx_department (department)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── If the table already exists, run these ALTER commands instead ──
-- ALTER TABLE students ADD COLUMN IF NOT EXISTS year VARCHAR(20) NOT NULL DEFAULT '' AFTER department;
