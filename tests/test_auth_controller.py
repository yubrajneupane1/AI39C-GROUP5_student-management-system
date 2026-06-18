"""
    python -m pytest tests/test_auth_controller.py -v
"""

import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages
from app.controller.auth import AuthController


# A reusable helper that builds a tiny Flask app for every test.
# define the route names the controller redirects to
# (auth.home, auth.login, auth.dashboard, auth.register) so that
# url_for() inside the controller can build URLs successfully.
def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"

    bp = Blueprint("auth", __name__)
    bp.route("/", endpoint="home")(lambda: "home")
    bp.route("/login", endpoint="login")(lambda: "login")
    bp.route("/dashboard", endpoint="dashboard")(lambda: "dashboard")
    bp.route("/register", endpoint="register")(lambda: "register")
    app.register_blueprint(bp)
    return app

class TestRegister(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()
        # Replace the real database model with a fake one.
        self.controller.user_model = MagicMock()

    @patch("app.controller.auth.render_template")
    def test_register_get_shows_form(self, mock_render):
        """Visiting register with GET should show the register form."""
        mock_render.return_value = "register_page"
        with self.app.test_request_context(method="GET"):
            result = self.controller.register()
            self.assertEqual(result, "register_page")
            mock_render.assert_called_once_with("register.html")

    @patch("app.controller.auth.render_template")
    def test_register_missing_fields_is_rejected(self, mock_render):
        """If any field is empty, registration is refused with a message."""
        mock_render.return_value = "register_page"
        with self.app.test_request_context(
            method="POST", data={"fullname": "", "email": "", "username": "", "password": "", "confirm_password": ""}
        ):
            self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("error", "All fields are required."), flashes)

    @patch("app.controller.auth.render_template")
    def test_register_password_mismatch_is_rejected(self, mock_render):
        """Passwords that don't match are rejected."""
        mock_render.return_value = "register_page"
        with self.app.test_request_context(
            method="POST",
            data={"fullname": "Bob", "email": "bob@example.com", "username": "bob123", 
                  "password": "secret123", "confirm_password": "different"}
        ):
            self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("error", "Passwords do not match."), flashes)

    @patch("app.controller.auth.render_template")
    def test_register_short_password_is_rejected(self, mock_render):
        """Passwords shorter than 8 characters are not allowed."""
        mock_render.return_value = "register_page"
        with self.app.test_request_context(
            method="POST",
            data={"fullname": "Bob", "email": "bob@example.com", "username": "bob123",
                  "password": "123", "confirm_password": "123"}
        ):
            self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("error", "Password must be at least 8 characters."), flashes)

    @patch("app.controller.auth.User")
    def test_register_duplicate_email_is_rejected(self, mock_user_class):
        """If the email already exists, registration is refused."""
        fake_user = MagicMock()
        fake_user.email_exists.return_value = True
        mock_user_class.return_value = fake_user

        with self.app.test_request_context(
            method="POST",
            data={"fullname": "Bob", "email": "taken@example.com", "username": "bob123",
                  "password": "secret123", "confirm_password": "secret123"}
        ):
            response = self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("error", "An account with this email already exists."), flashes)
            # We should be redirected back to the register page (302).
            self.assertEqual(response.status_code, 302)
            # And the user should NOT be saved.
            fake_user.save.assert_not_called()

    @patch("app.controller.auth.User")
    def test_register_duplicate_username_is_rejected(self, mock_user_class):
        """If the username already exists, registration is refused."""
        fake_user = MagicMock()
        fake_user.email_exists.return_value = False
        fake_user.username_exists.return_value = True
        mock_user_class.return_value = fake_user

        with self.app.test_request_context(
            method="POST",
            data={"fullname": "Bob", "email": "bob@example.com", "username": "taken",
                  "password": "secret123", "confirm_password": "secret123"}
        ):
            response = self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("error", "Username is already taken."), flashes)
            self.assertEqual(response.status_code, 302)
            fake_user.save.assert_not_called()

    @patch("app.controller.auth.User")
    def test_register_success_saves_user_and_redirects(self, mock_user_class):
        """A valid new user is saved and sent to the login page."""
        fake_user = MagicMock()
        fake_user.email_exists.return_value = False
        fake_user.username_exists.return_value = False
        mock_user_class.return_value = fake_user

        with self.app.test_request_context(
            method="POST",
            data={"fullname": "Alice", "email": "alice@example.com", "username": "alice123",
                  "password": "secret123", "confirm_password": "secret123"}
        ):
            response = self.controller.register()
            # The new user was saved to the database.
            fake_user.save.assert_called_once()
            # Then redirected (302) to the login page with a success note.
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login", response.location)
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Account created! You can now log in."), flashes)


# =====================================================================
#  LOGIN
# =====================================================================
class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()
        self.controller.user_model = MagicMock()

    @patch("app.controller.auth.render_template")
    def test_login_get_shows_form(self, mock_render):
        """Visiting login with GET should show the login form."""
        mock_render.return_value = "login_page"
        with self.app.test_request_context(method="GET"):
            result = self.controller.login()
            self.assertEqual(result, "login_page")
            mock_render.assert_called_once_with("login.html")

    @patch("app.controller.auth.render_template")
    def test_login_missing_fields_is_rejected(self, mock_render):
        """Empty username/password shows an error and stays on login."""
        mock_render.return_value = "login_page"
        with self.app.test_request_context(
            method="POST", data={"username": "", "password": ""}
        ):
            self.controller.login()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("error", "Username and password are required."), flashes)

    @patch("app.controller.auth.render_template")
    @patch("app.controller.auth.User.login")
    def test_login_wrong_password_is_rejected(self, mock_login, mock_render):
        """A correct username but wrong password is refused."""
        mock_render.return_value = "login_page"
        # The database "finds" a user...
        fake_user = MagicMock()
        fake_user.check_password.return_value = False
        mock_login.return_value = fake_user

        with self.app.test_request_context(
            method="POST",
            data={"username": "bob123", "password": "wrongpass"},
        ):
            self.controller.login()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("error", "Invalid username or password."), flashes)
            # No session was created.
            self.assertNotIn("user_id", session)

    @patch("app.controller.auth.User.login")
    def test_login_success_sets_session_and_redirects_admin(self, mock_login):
        """A correct admin login stores the user in the session and redirects to admin dashboard."""
        fake_user = MagicMock()
        fake_user.id = 1
        fake_user.username = "admin"
        fake_user.role = "admin"
        fake_user.check_password.return_value = True
        mock_login.return_value = fake_user

        with self.app.test_request_context(
            method="POST",
            data={"username": "admin", "password": "admin123"},
        ):
            response = self.controller.login()
            # Session is filled in with the logged-in user's details.
            self.assertEqual(session["user_id"], 1)
            self.assertEqual(session["username"], "admin")
            self.assertEqual(session["role"], "admin")
            # Redirected (302) to admin dashboard
            self.assertEqual(response.status_code, 302)
            self.assertIn("/admin/dashboard", response.location)

    @patch("app.controller.auth.User.login")
    def test_login_success_redirects_teacher(self, mock_login):
        """A correct teacher login redirects to teacher dashboard."""
        fake_user = MagicMock()
        fake_user.id = 2
        fake_user.username = "teacher"
        fake_user.role = "teacher"
        fake_user.check_password.return_value = True
        mock_login.return_value = fake_user

        with self.app.test_request_context(
            method="POST",
            data={"username": "teacher", "password": "teacher123"},
        ):
            response = self.controller.login()
            self.assertEqual(session["role"], "teacher")
            self.assertEqual(response.status_code, 302)
            self.assertIn("/teacher/dashboard", response.location)

    @patch("app.controller.auth.User.login")
    def test_login_success_redirects_student(self, mock_login):
        """A correct student login redirects to student dashboard."""
        fake_user = MagicMock()
        fake_user.id = 3
        fake_user.username = "student"
        fake_user.role = "student"
        fake_user.check_password.return_value = True
        mock_login.return_value = fake_user

        with self.app.test_request_context(
            method="POST",
            data={"username": "student", "password": "student123"},
        ):
            response = self.controller.login()
            self.assertEqual(session["role"], "student")
            self.assertEqual(response.status_code, 302)
            self.assertIn("/student/dashboard", response.location)


# =====================================================================
#  LOGOUT
# =====================================================================
class TestLogout(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()
        self.controller.user_model = MagicMock()

    def test_logout_clears_session_and_redirects(self):
        """Logging out wipes the session and returns to the login page."""
        with self.app.test_request_context():
            # Pretend someone is logged in.
            session["user_id"] = 99
            session["username"] = "Alice"
            session["role"] = "student"

            response = self.controller.logout()

            # Every session value is gone.
            self.assertNotIn("user_id", session)
            self.assertNotIn("username", session)
            self.assertNotIn("role", session)
            # Redirected (302) back to login with a goodbye message.
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login", response.location)
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "You have been logged out."), flashes)


if __name__ == "__main__":
    unittest.main()