from app.models.basemodel import BaseModel
from datetime import datetime

class MarksModel(BaseModel):
    def get_all_marks(self):
        query = """
            SELECT * FROM marks
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def add_marks(self,student_id,subject,marks): 
        query = """
            INSERT INTO marks
            (student_id,subject,marks)
            VALUES(%s,%s,%s)
            """