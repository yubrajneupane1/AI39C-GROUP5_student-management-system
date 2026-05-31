from app.models.basemodel import BaseModel

class AttendanceModel(BaseModel):
    def get_all_attendance(self):
        query = """
            SELECT * FROM attendance
            ORDER BY attendance_date DESC
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def mark_attendance(self,student_id,attendance_date,status):
        query = """
            INSERT INTO attendance
            (student_id, attendance_date, status)
                VALUES(%s,%s,%s)
            """
        self.cursor.execute(
    query,
    (
        student_id,
        attendance_date,
        status
    )
    )

        self.conn.commit()    


