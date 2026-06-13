from flask import Blueprint, render_template, session, redirect, url_for, request

class AuthRoutes:

    def __init__(self, controller):
        self.bp = Blueprint("auth", __name__)
        self.controller = controller
        self._register_routes()

    def _register_routes(self):

        @self.bp.route("/register", methods=["GET", "POST"])
        def register():
            return render_template("register.html")

        @self.bp.route("/login", methods=["GET", "POST"])
        def login():
            if request.method == "POST":
                user = self.controller.login(
                    request.form["username"],
                    request.form["password"]
                )
                if user:
                    session["user_id"] = user["id"]
                    session["role"] = user["role"]
                    return redirect(url_for("dashboard"))  # adjust to your route
            return render_template("login.html")

        @self.bp.route("/logout")
        def logout():
            session.clear()
            return redirect(url_for("auth.login"))

    def current_user(self):
        if not session.get("user_id"):
            return redirect("/login")
        return session.get("user_id")