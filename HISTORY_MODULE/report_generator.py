# ============================================================
# report_generator.py — Attendance Report Generator
# ============================================================

import csv
import io
from BACKEND.models.attendance_model import AttendanceModel
from ATTENDANCE_MODULE.timestamp_generator import format_date, format_time


class ReportGenerator:
    """
    Generates attendance reports in various formats (CSV, JSON summary).
    """

    @staticmethod
    def generate_csv(student_id: str, start_date: str = None, end_date: str = None) -> str:
        """
        Generate a CSV report of attendance records.

        Returns:
            CSV content as a string
        """
        if start_date and end_date:
            records = AttendanceModel.filter_by_date_range(student_id, start_date, end_date)
        else:
            records = AttendanceModel.get_by_student(student_id, limit=365)

        output = io.StringIO()
        fieldnames = ["date", "time", "status", "latitude", "longitude",
                      "location_valid", "face_match_status", "face_confidence", "remarks"]

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            record["date"] = format_date(str(record["date"]))
            record["time"] = format_time(str(record["time"]))
            writer.writerow(record)

        return output.getvalue()

    @staticmethod
    def generate_json_report(student_id: str) -> dict:
        """
        Generate a comprehensive JSON summary report.
        """
        from BACKEND.models.student_model import StudentModel
        from HISTORY_MODULE.attendance_logger import AttendanceLogger

        student = StudentModel.find_by_student_id(student_id)
        summary = AttendanceModel.get_summary(student_id)
        recent = AttendanceLogger.get_history(student_id, limit=10)

        return {
            "student": {
                "student_id": student["student_id"],
                "name": student["name"],
                "department": student["department"],
                "class_name": student["class_name"],
            },
            "summary": summary,
            "recent_records": recent,
            "attendance_percentage": (
                round(
                    (summary["present_count"] + summary["late_count"]) / max(summary["total"], 1) * 100, 2
                ) if summary else 0
            ),
        }
