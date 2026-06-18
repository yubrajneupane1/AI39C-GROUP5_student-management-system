"""
    python -m pytest tests/test_integration.py -v
"""

import unittest
from flask import Flask, session
from app import create_app
from app.models.database import Database
import json


class TestIntegration(unittest.TestCase):

    TEST_USERNAME = "testuser"
    TEST_EMAIL = "test@example.com"

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.client = cls.app.test_client()
        cls._cleanup_test_user()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_test_user()

    @classmethod
    def _cleanup_test_user(cls):
        """Remove any leftover test-registration data so test_register_flow
        is repeatable across multiple pytest runs."""
        db = Database()
        db.execute(
            "DELETE FROM users WHERE username = %s OR email = %s",
            (cls.TEST_USERNAME, cls.TEST_EMAIL),
        )
        db.close()

    def test_login_flow_admin(self):
        """Test complete login flow for admin."""
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin Dashboard', response.data)

    def test_login_flow_teacher(self):
        """Test complete login flow for teacher."""
        response = self.client.post('/login', data={
            'username': 'teacher',
            'password': 'teacher123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Teacher Dashboard', response.data)

    def test_login_flow_student(self):
        """Test complete login flow for student."""
        response = self.client.post('/login', data={
            'username': 'student',
            'password': 'student123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Student Dashboard', response.data)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post('/login', data={
            'username': 'wrong',
            'password': 'wrong'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_logout_flow(self):
        """Test logout flow."""
        # Login first
        self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        # Then logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_register_flow(self):
        """Test registration flow."""
        # Ensure a clean slate even if a previous test in this run left data behind
        self._cleanup_test_user()

        response = self.client.post('/register', data={
            'fullname': 'Test User',
            'email': self.TEST_EMAIL,
            'username': self.TEST_USERNAME,
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'role': 'student'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Account created!', response.data)

        # Clean up immediately so later runs aren't affected
        self._cleanup_test_user()

    def test_admin_dashboard_access(self):
        """Test admin dashboard access."""
        self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin Dashboard', response.data)

    def test_teacher_dashboard_access(self):
        """Test teacher dashboard access."""
        self.client.post('/login', data={
            'username': 'teacher',
            'password': 'teacher123'
        })

        response = self.client.get('/teacher/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Teacher Dashboard', response.data)

    def test_student_dashboard_access(self):
        """Test student dashboard access."""
        self.client.post('/login', data={
            'username': 'student',
            'password': 'student123'
        })

        response = self.client.get('/student/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Student Dashboard', response.data)

    def test_protected_route_redirect(self):
        """Test protected route redirects unauthenticated users."""
        response = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Login', response.data)


if __name__ == "__main__":
    unittest.main()