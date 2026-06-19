"""
    python -m pytest tests/test_attendance.py -v
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from flask import Flask, Blueprint, session, get_flashed_messages
from app.models.attendance_model import AttendanceModel


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"
    return app


class TestAttendanceModel(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.model = AttendanceModel()
        self.model.db = MagicMock()

    def test_mark_attendance_success(self):
        """Marking attendance with valid data should succeed."""
        self.model.db.fetchone.return_value = None  # No existing attendance
        self.model.db.execute.return_value = None
        
        success, message = self.model.mark_attendance(
            student_id=1, course_id=1, status="present", marked_by=2
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Attendance marked successfully")
        self.model.db.execute.assert_called_once()

    def test_mark_attendance_duplicate_fails(self):
        """Marking attendance for the same day twice should fail."""
        self.model.db.fetchone.return_value = {"id": 1}  # Existing attendance
        
        success, message = self.model.mark_attendance(
            student_id=1, course_id=1, status="present", marked_by=2
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Attendance already marked for today")
        self.model.db.execute.assert_not_called()

    def test_update_attendance_success(self):
        """Updating attendance with valid data should succeed."""
        self.model.db.fetchone.return_value = {"id": 1, "date": date.today(), "status": "absent"}
        self.model.db.execute.return_value = None
        
        success, message = self.model.update_attendance(
            attendance_id=1, status="present", changed_by=2
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Attendance updated successfully")

    def test_update_attendance_future_date_fails(self):
        """Updating attendance for a future date should fail."""
        future_date = date.today() + timedelta(days=5)
        self.model.db.fetchone.return_value = {"id": 1, "date": future_date, "status": "absent"}
        
        success, message = self.model.update_attendance(
            attendance_id=1, status="present", changed_by=2
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Cannot update future attendance")

    def test_get_attendance_summary_returns_stats(self):
        """Getting attendance summary should return statistics."""
        self.model.db.fetchone.return_value = {
            "total_classes": 10,
            "present": 8,
            "absent": 2,
            "late": 0,
            "excused": 0,
            "percentage": 80.0
        }
        
        result = self.model.get_attendance_summary(student_id=1)
        
        self.assertEqual(result["total_classes"], 10)
        self.assertEqual(result["present"], 8)
        self.assertEqual(result["percentage"], 80.0)

    def test_get_attendance_summary_no_records(self):
        """Getting attendance summary with no records should return zeros."""
        self.model.db.fetchone.return_value = {
            "total_classes": 0,
            "present": 0,
            "absent": 0,
            "late": 0,
            "excused": 0,
            "percentage": None
        }
        
        result = self.model.get_attendance_summary(student_id=1)
        
        self.assertEqual(result["total_classes"], 0)
        self.assertEqual(result["percentage"], None)

    def test_get_course_attendance_summary(self):
        """Getting course attendance summary should return student data."""
        mock_students = [
            {"fullname": "Student A", "student_id": 1, "total_classes": 10, "present": 8, "percentage": 80.0},
            {"fullname": "Student B", "student_id": 2, "total_classes": 10, "present": 6, "percentage": 60.0}
        ]
        self.model.db.fetch.return_value = mock_students
        
        result = self.model.get_course_attendance_summary(course_id=1)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["fullname"], "Student A")
        self.assertEqual(result[0]["percentage"], 80.0)

    def test_close_connection(self):
        """Closing the model should close the database connection."""
        self.model.close()
        self.model.db.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()