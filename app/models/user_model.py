from app.models.basemodel import BaseModel

class UserModel(BaseModel):

    def get_user_by_username(self, username):
        query = "SELECT * FROM users WHERE username=%s"
        self.cursor.execute(query, (username,))
        return self.cursor.fetchone()