from app.models.user_model import UserModel
from werkzeug.security import check_password_hash
from flask import session

class AuthController:

    def __init__(self):
        self.user_model = UserModel()
    def login(self, username):
        return self.user_model.get_user_by_username(username)
    def validate_login(self, username, password):
        user = self.user_model.get_user_by_username(username)
    
 

        if not user:
            return False

        return check_password_hash(
        user["password"],
        password
    )

    session["user_id"] = user.id
    session["role"] = user.role

    def register_user(
        self,
        username,
        password,
        role
    ):
       return self.user_model.create_user(
        username,
        password,
        role
    )