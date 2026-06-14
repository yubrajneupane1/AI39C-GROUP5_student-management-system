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
    def get_student_marks(self, student_id):
        return self.db.fetch(
        """
        SELECT *
        FROM marks
        WHERE student_id=%s
        ORDER BY date DESC
        """,
        (student_id,)
    )
    
    def calculate_grade(marks):
        if marks >= 80:
            return "A"
        elif marks >= 60:
            return "B"
        return "C"
    
    def get_class_average(self, subject):
        pass
    
    
    
    
# Final validation improvements
    