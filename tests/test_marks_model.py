"""
    python -m pytest tests/test_marks_model.py -v
"""

import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
from app.models.marks_model import MarksModel


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"
    return app


class TestMarksModel(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.model = MarksModel()
        self.model.db = MagicMock()

    def test_add_marks_success(self):
        """Adding marks with valid data should succeed."""
        self.model.db.fetchone.return_value = None  # No existing marks
        
        success, message = self.model.add_marks(
            student_id=1, course_id=1, title="Quiz 1", 
            score=85, total=100, exam_type="quiz"
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Marks added successfully")
        self.model.db.execute.assert_called_once()

    def test_add_marks_score_exceeds_total_fails(self):
        """Adding marks where score exceeds total should fail."""
        success, message = self.model.add_marks(
            student_id=1, course_id=1, title="Quiz 1",
            score=120, total=100, exam_type="quiz"
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Score cannot exceed total marks")
        self.model.db.execute.assert_not_called()

    def test_add_marks_duplicate_fails(self):
        """Adding marks for the same assessment twice should fail."""
        self.model.db.fetchone.return_value = {"id": 1}  # Existing marks
        
        success, message = self.model.add_marks(
            student_id=1, course_id=1, title="Quiz 1",
            score=85, total=100, exam_type="quiz"
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Marks already exist for this assessment")

    def test_update_marks_success(self):
        """Updating marks with valid data should succeed."""
        self.model.db.fetchone.return_value = {"id": 1, "score": 70, "total": 100}
        self.model.db.execute.return_value = None
        
        success, message = self.model.update_marks(
            mark_id=1, score=85, total=100, changed_by=2
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Marks updated successfully")

    def test_update_marks_not_found_fails(self):
        """Updating marks that don't exist should fail."""
        self.model.db.fetchone.return_value = None
        
        success, message = self.model.update_marks(
            mark_id=999, score=85, total=100, changed_by=2
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Marks not found")

    def test_update_marks_score_exceeds_total_fails(self):
        """Updating marks where score exceeds total should fail."""
        self.model.db.fetchone.return_value = {"id": 1, "score": 70, "total": 100}
        
        success, message = self.model.update_marks(
            mark_id=1, score=150, total=100, changed_by=2
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Score cannot exceed total marks")

    def test_calculate_course_results_success(self):
        """Calculating course results should return grade and percentage."""
        mock_marks = [
            {"score": 85, "total": 100, "weightage": 100},
            {"score": 90, "total": 100, "weightage": 100}
        ]
        self.model.db.fetch.return_value = mock_marks
        self.model.db.fetchone.return_value = {"grade": "A"}
        
        result = self.model.calculate_course_results(student_id=1, course_id=1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["grade"], "A")
        self.assertIsInstance(result["percentage"], float)

    def test_calculate_course_results_no_marks(self):
        """Calculating course results with no marks should return None."""
        self.model.db.fetch.return_value = []
        
        result = self.model.calculate_course_results(student_id=1, course_id=1)
        
        self.assertIsNone(result)

    def test_get_student_marks(self):
        """Getting student marks should return marks with grade and percentage."""
        mock_marks = [
            {"title": "Quiz 1", "score": 85, "total": 100, "course_name": "CS101", "percentage": 85.0, "grade": "A"}
        ]
        self.model.db.fetch.return_value = mock_marks
        
        result = self.model.get_student_marks(student_id=1)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Quiz 1")
        self.assertEqual(result[0]["percentage"], 85.0)

    def test_get_grade_scale(self):
        """Getting grade scale should return all grades."""
        mock_grades = [
            {"grade": "A+", "min_score": 90, "max_score": 100, "gpa": 4.0},
            {"grade": "A", "min_score": 85, "max_score": 89, "gpa": 3.7}
        ]
        self.model.db.fetch.return_value = mock_grades
        
        result = self.model.get_grade_scale()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["grade"], "A+")

    def test_close_connection(self):
        """Closing the model should close the database connection."""
        self.model.close()
        self.model.db.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()