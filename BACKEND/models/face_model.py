# ============================================================
# face_model.py — Face Descriptor / Encoding Model
# ============================================================

import json
from DATABASE.connection.db_connection import execute_query, execute_insert


class FaceModel:
    TABLE = "face_data"

    @staticmethod
    def save_descriptor(student_id, descriptor: list, image_path: str = None, model: str = "face_recognition_v1"):
        """
        Save or update the face descriptor for a student.
        Descriptor is a list of floats (128-d vector).
        """
        descriptor_json = json.dumps(descriptor)
        existing = FaceModel.get_by_student_id(student_id)

        if existing:
            query = """
                UPDATE face_data
                SET face_descriptor = %s, image_path = %s, encoding_model = %s
                WHERE student_id = %s
            """
            execute_insert(query, (descriptor_json, image_path, model, student_id))
        else:
            query = """
                INSERT INTO face_data (student_id, face_descriptor, image_path, encoding_model)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """
            execute_insert(query, (student_id, descriptor_json, image_path, model))

    @staticmethod
    def get_by_student_id(student_id):
        """Fetch the face record for a student. Returns dict with parsed descriptor."""
        query = "SELECT * FROM face_data WHERE student_id = %s"
        row = execute_query(query, (student_id,), fetch="one")
        if row and "face_descriptor" in row:
            row["face_descriptor"] = json.loads(row["face_descriptor"])
        return row

    @staticmethod
    def get_all_descriptors():
        """
        Fetch all face descriptors (for batch matching).
        Returns list of {student_id, face_descriptor (list)}.
        """
        query = "SELECT student_id, face_descriptor FROM face_data"
        rows = execute_query(query, fetch="all")
        for row in rows:
            row["face_descriptor"] = json.loads(row["face_descriptor"])
        return rows

    @staticmethod
    def delete_by_student_id(student_id):
        """Remove a student's face data record."""
        query = "DELETE FROM face_data WHERE student_id = %s"
        execute_insert(query, (student_id,))

    @staticmethod
    def has_face_data(student_id):
        """Check if a student has enrolled their face."""
        row = execute_query("SELECT id FROM face_data WHERE student_id = %s", (student_id,), fetch="one")
        return row is not None
