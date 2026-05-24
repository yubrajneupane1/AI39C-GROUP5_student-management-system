from app.models.database import Database
from werkzeug.security import generate_password_hash
class BaseModel:

    def __init__(self):
        self.conn = Database.get_connection()
        self.cursor = self.conn.cursor(dictionary=True)