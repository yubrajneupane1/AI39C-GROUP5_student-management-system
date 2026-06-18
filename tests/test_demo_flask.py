"""
    python -m pytest tests/test_demo_flask.py -v
"""

import unittest
from flask import Flask, Blueprint
from app.auth import login_required 

class TestFlaskBasics(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "secret_keyy"
        auth = Blueprint("auth", __name__)

        @auth.route("/login")
        def login():
            return "this is the login page"

        @auth.route("/home")
        @login_required                      
        def home():
            return "welcome home"

        self.app.register_blueprint(auth)
        self.client = self.app.test_client()


    def test_locked_page_redirects_a_guest(self):
        """A NOT-logged-in user /home redirect to /login."""
        response = self.client.get("/home")
        # Assert: 302 means "redirect" (go somewhere else)
        self.assertEqual(response.status_code, 302)
        # And it should be redirecting to the login page
        self.assertIn("/login", response.location)

    def test_locked_page_opens_for_logged_in_user(self):
        """A logged-in visitor SHOULD see /home."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
        response = self.client.get("/home")

        # Assert: 200 means "OK, here is the page"
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), "welcome home")


    def test_login_page_is_public(self):
        """Anyone can open the login page."""
        response = self.client.get("/login")

        self.assertEqual(response.status_code, 200)
        self.assertIn("this is the login page", response.data.decode())


if __name__ == "__main__":
    unittest.main()