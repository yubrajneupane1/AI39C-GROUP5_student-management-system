from app.models.database import Database
from werkzeug.security import generate_password_hash
class BaseModel:

    def __init__(self):
        self.conn = Database.get_connection()
        self.cursor = self.conn.cursor(dictionary=True)
    def create_user(self, username, password, role):

        hashed_password = generate_password_hash(password)

        query = """
        INSERT INTO users
        (username,password,role)
        VALUES(%s,%s,%s)
    """

        self.cursor.execute(
        query,
        (username, hashed_password, role)
    )

        self.conn.commit()