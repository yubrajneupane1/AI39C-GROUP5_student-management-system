from app.models.user_model import UserModel

class AuthController:

    def __init__(self):
        self.user_model = UserModel()
    def login(self, username):
        return self.user_model.get_user_by_username(username)