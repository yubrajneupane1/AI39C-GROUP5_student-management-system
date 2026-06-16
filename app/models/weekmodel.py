from app.models.database import Database

class Week:
    def __init__(self):
        self.db = Database()

    def create(self, course_id, week_number, title):
        query = """
            INSERT INTO weeks
            (course_id, week_number, title)
            VALUES (%s, %s, %s)
        """
        return self.db.execute(
            query,
            (course_id, week_number, title)
        )

    def get_by_course(self, course_id):
        query = """
            SELECT *
            FROM weeks
            WHERE course_id = %s
            ORDER BY week_number
        """
        return self.db.fetch(
            query,
            (course_id,)
        )

    def get_by_id(self, week_id):
        query = """
            SELECT *
            FROM weeks
            WHERE id = %s
        """
        return self.db.fetchone(
            query,
            (week_id,)
        )