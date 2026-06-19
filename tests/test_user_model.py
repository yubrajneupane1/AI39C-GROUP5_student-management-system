"""
    python -m pytest tests/test_user_model.py -v
"""

import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
from app.models.user_model import User


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"
    return app


class TestUserModel(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    def test_user_creation(self):
        """Creating a user should set attributes correctly."""
        user = User(name="Test User", email="test@example.com", 
                    username="testuser", password="password123", role="student")
        
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.role, "student")
        self.assertIsNotNone(user._password)

    def test_password_hashing(self):
        """Password should be hashed and verifiable."""
        user = User(password="secret123")
        self.assertNotEqual(user._password, "secret123")
        self.assertTrue(user.check_password("secret123"))
        self.assertFalse(user.check_password("wrongpass"))

    def test_from_db(self):
        """Creating a user from database data should work."""
        data = {
            "id": 1,
            "fullname": "Test User",
            "username": "testuser",
            "email": "test@example.com",
            "password": "hashed_password",
            "role": "student"
        }
        user = User.from_db(data)
        
        self.assertEqual(user.id, 1)
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.role, "student")

    def test_from_db_none(self):
        """from_db should return None when data is None."""
        user = User.from_db(None)
        self.assertIsNone(user)

    @patch('app.models.user_model.Database')
    def test_save_user(self, mock_db):
        """Saving a user should execute insert query."""
        user = User(name="Test", email="test@example.com", 
                    username="testuser", password="pass123")
        user.save()
        
        mock_db.return_value.execute.assert_called_once()

    @patch('app.models.user_model.Database')
    def test_email_exists(self, mock_db):
        """Checking if email exists should query the database."""
        mock_db.return_value.fetchone.return_value = {"id": 1}
        user = User(email="test@example.com")
        
        result = user.email_exists()
        self.assertTrue(result)

    @patch('app.models.user_model.Database')
    def test_username_exists(self, mock_db):
        """Checking if username exists should query the database."""
        mock_db.return_value.fetchone.return_value = {"id": 1}
        user = User(username="testuser")
        
        result = user.username_exists()
        self.assertTrue(result)

    @patch('app.models.user_model.Database')
    def test_login_success(self, mock_db):
        """Login should return user if found."""
        mock_db.return_value.fetchone.return_value = {
            "id": 1, "fullname": "Test", "username": "testuser",
            "email": "test@example.com", "password": "hashed", "role": "student"
        }
        
        user = User.login("testuser")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")

    @patch('app.models.user_model.Database')
    def test_login_not_found(self, mock_db):
        """Login should return None if user not found."""
        mock_db.return_value.fetchone.return_value = None
        
        user = User.login("notfound")
        self.assertIsNone(user)


if __name__ == "__main__":
    unittest.main()