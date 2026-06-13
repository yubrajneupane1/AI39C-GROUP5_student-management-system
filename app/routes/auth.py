from flask import Blueprint
from app.controller.auth import AuthController


class AuthRoutes:

    def __init__(self):

        self.bp = Blueprint("auth", __name__)

        self.controller = AuthController()

    def register(self):

        self.bp.route("/", methods=["GET", "POST"])(
            self.controller.login
        )

        self.bp.route("/login", methods=["GET", "POST"])(
            self.controller.login
        )

        self.bp.route("/register", methods=["GET", "POST"])(
            self.controller.register
        )

        self.bp.route("/home", methods=["GET", "POST"])(
            self.controller.home
        )

        self.bp.route("/logout")(
            self.controller.logout
        )

        return self.bp