from app.models.database import Database

class BaseModel:

    def __init__(self):
        self.conn = Database.get_connection()
        self.cursor = self.conn.cursor(dictionary=True)