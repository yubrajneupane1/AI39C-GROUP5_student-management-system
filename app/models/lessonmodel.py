from app.models.database import Database

class Lesson:
    def __init__(self):
        self.db = Database()

    def create(self, week_id, lesson_number, title, content=None):
        query = """
            INSERT INTO lessons
            (week_id, lesson_number, title, content)
            VALUES (%s, %s, %s, %s)
        """
        return self.db.execute(
            query,
            (week_id, lesson_number, title, content)
        )

    def get_by_week(self, week_id):
        query = """
            SELECT *
            FROM lessons
            WHERE week_id=%s
            ORDER BY lesson_number
        """
        return self.db.fetch(query, (week_id,))

    def get_by_id(self, lesson_id):
        query = """
            SELECT *
            FROM lessons
            WHERE id=%s
        """
        return self.db.fetchone(query, (lesson_id,))