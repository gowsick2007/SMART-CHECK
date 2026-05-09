-- ============================================================
-- attendance_table.sql — Attendance Records Schema (PostgreSQL)
-- ============================================================

CREATE TABLE IF NOT EXISTS attendance (
    id                  SERIAL PRIMARY KEY,
    student_id          VARCHAR(20)  NOT NULL,
    date                DATE         NOT NULL,
    time                TIME         NOT NULL,
    status              VARCHAR(10)  NOT NULL DEFAULT 'absent'
                            CHECK (status IN ('present', 'absent', 'late')),
    latitude            NUMERIC(10, 7),
    longitude           NUMERIC(10, 7),
    location_valid      SMALLINT     NOT NULL DEFAULT 0,
    face_match_status   VARCHAR(15)  NOT NULL DEFAULT 'not_attempted'
                            CHECK (face_match_status IN ('success', 'failed', 'not_attempted')),
    face_confidence     FLOAT,
    marked_at           TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    remarks             VARCHAR(255),

    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    UNIQUE (student_id, date)
);

CREATE INDEX IF NOT EXISTS idx_student_date ON attendance (student_id, date);
CREATE INDEX IF NOT EXISTS idx_date         ON attendance (date);
