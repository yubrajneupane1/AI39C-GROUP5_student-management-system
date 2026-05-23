from app.models.user_model import UserModel
from werkzeug.security import check_password_hash

class AuthController:

    def __init__(self):
        self.user_model = UserModel()
    def login(self, username):
        return self.user_model.get_user_by_username(username)