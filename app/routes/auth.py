from flask import Blueprint

class AuthRoutes:

    def __init__(self):
        self.bp = Blueprint("auth", __name__)

    def register(self):
        return self.bp