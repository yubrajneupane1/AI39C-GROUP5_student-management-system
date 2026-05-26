from app.models.basemodel import BaseModel
from werkzeug.security import check_password_hash
class UserModel(BaseModel):

    def get_user_by_username(self, username):
        query = "SELECT * FROM users WHERE username=%s"
        self.cursor.execute(query, (username,))
        return self.cursor.fetchone()
 
    def check_password(self, plain_password):
       return check_password_hash(
        self._password,
        plain_password
    )