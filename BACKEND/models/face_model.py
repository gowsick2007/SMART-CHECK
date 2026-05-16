# ============================================================
# face_model.py — Face Descriptor / Encoding Model (Students Table)
# ============================================================

import json
from DATABASE.connection.db_connection import execute_query, execute_insert


class FaceModel:
    TABLE = "students"

    @staticmethod
    def save_descriptor(student_id, descriptor: list, image_path: str = None, model: str = "face_recognition_v1"):
        """
        Save or update the face descriptor for a student in the students table.
        Descriptor is a list of floats (128-d vector).
        """
        descriptor_json = json.dumps(descriptor)
        query = """
            UPDATE students
            SET face_descriptor = %s, face_enrolled = TRUE
            WHERE student_id = %s
        """
        execute_insert(query, (descriptor_json, student_id))

    @staticmethod
    def get_by_student_id(student_id):
        """Fetch the face record for a student from students table."""
        query = "SELECT face_descriptor FROM students WHERE student_id = %s"
        row = execute_query(query, (student_id,), fetch="one")
        if row and row.get("face_descriptor"):
            try:
                row["face_descriptor"] = json.loads(row["face_descriptor"])
            except:
                pass
        return row

    @staticmethod
    def get_all_descriptors():
        """
        Fetch all face descriptors for students who have enrolled.
        """
        query = "SELECT student_id, face_descriptor FROM students WHERE face_enrolled = TRUE"
        rows = execute_query(query, fetch="all") or []
        for row in rows:
            if row.get("face_descriptor"):
                try:
                    row["face_descriptor"] = json.loads(row["face_descriptor"])
                except:
                    pass
        return rows

    @staticmethod
    def delete_by_student_id(student_id):
        """Remove a student's face data by resetting the columns."""
        query = "UPDATE students SET face_descriptor = NULL, face_enrolled = FALSE WHERE student_id = %s"
        execute_insert(query, (student_id,))

    @staticmethod
    def has_face_data(student_id):
        """Check if a student has enrolled their face using the boolean flag."""
        query = "SELECT face_enrolled FROM students WHERE student_id = %s"
        row = execute_query(query, (student_id,), fetch="one")
        return bool(row.get("face_enrolled")) if row else False
