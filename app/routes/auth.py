from flask import Blueprint
from flask import render_template
class AuthRoutes:

    def __init__(self):
        self.bp = Blueprint("auth", __name__)
    
    @self.bp.route("/login")
    def login():
        return render_template("login.html")

    def register(self):
        return self.bp