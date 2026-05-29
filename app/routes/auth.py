from flask import Blueprint
from flask import render_template
from flask import session
class AuthRoutes:

    def __init__(self):
        self.bp = Blueprint("auth", __name__)


    def register(self):
        return self.bp
    @self.bp.route("/register", methods=["GET", "POST"])
    def register():
        return render_template("register.html")
        
    @self.bp.route("/login")
    def login():
        return render_template("login.html")
    
    session["user_id"] = user["id"]
    session["role"] = user["role"]

    self.bp.route("/logout")(
    self.controller.logout
)
    def logout(self):
      session.clear()