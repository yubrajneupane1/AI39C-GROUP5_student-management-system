from app.models.basemodel import BaseModel

class MarksModel(BaseModel):
    def get_all_marks(self):
        query = """
            SELECT * FROM marks
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()