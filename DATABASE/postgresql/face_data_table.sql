-- ============================================================
-- face_data_table.sql — Face Descriptor Storage (PostgreSQL)
-- ============================================================

CREATE TABLE IF NOT EXISTS face_data (
    id              SERIAL PRIMARY KEY,
    student_id      VARCHAR(20)  NOT NULL UNIQUE,
    face_descriptor TEXT         NOT NULL,
    image_path      VARCHAR(255),
    encoding_model  VARCHAR(50)  NOT NULL DEFAULT 'face_recognition_v1',
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_student_face ON face_data (student_id);
