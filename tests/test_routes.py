"""
    python -m pytest tests/test_routes.py -v
"""

import unittest
from flask import Flask
from app import create_app


class TestRoutes(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.client = cls.app.test_client()
    
    def test_login_page(self):
        """Test login page loads."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_register_page(self):
        """Test register page loads."""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data)

    def test_home_redirect(self):
        """Test home redirects to login when not authenticated."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)

    def test_admin_students_route(self):
        """Test admin students route requires login."""
        response = self.client.get('/admin/students', follow_redirects=True)
        self.assertIn(b'Login', response.data)

    def test_admin_courses_route(self):
        """Test admin courses route requires login."""
        response = self.client.get('/admin/courses', follow_redirects=True)
        self.assertIn(b'Login', response.data)

    def test_teacher_attendance_route(self):
        """Test teacher attendance route requires login."""
        response = self.client.get('/teacher/attendance', follow_redirects=True)
        self.assertIn(b'Login', response.data)

    def test_student_marks_route(self):
        """Test student marks route requires login."""
        response = self.client.get('/student/marks', follow_redirects=True)
        self.assertIn(b'Login', response.data)

    def test_notifications_route(self):
        """Test notifications route requires login."""
        response = self.client.get('/notifications', follow_redirects=True)
        self.assertIn(b'Login', response.data)

    def test_profile_route(self):
        """Test profile route requires login."""
        response = self.client.get('/profile', follow_redirects=True)
        self.assertIn(b'Login', response.data)


if __name__ == "__main__":
    unittest.main()