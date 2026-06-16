from app.models.database import Database


class Course:

    def __init__(self):
        self.db = Database()

    # ─────────────────────────────────────────────
    # GET ALL (with teacher name + enrollment count)
    # ─────────────────────────────────────────────

    def get_all(self):
        return self.db.fetch("""
            SELECT c.*, u.fullname AS teacher_name,
                   COUNT(e.id) AS enrolled
            FROM courses c
            LEFT JOIN users u ON c.teacher_id = u.id
            LEFT JOIN enrollments e ON c.id = e.course_id
            GROUP BY c.id
            ORDER BY c.name
        """)

    # ─────────────────────────────────────────────
    # GET BY ID (with weeks + lessons)
    # ─────────────────────────────────────────────

    def get_by_id(self, course_id):
        return self.db.fetchone(
            "SELECT * FROM courses WHERE id=%s",
            (course_id,)
        )

    def get_by_id_with_weeks(self, course_id):
        course = self.get_by_id(course_id)
        if not course:
            return None, []

        weeks = self.db.fetch(
            "SELECT * FROM weeks WHERE course_id=%s ORDER BY week_number",
            (course_id,)
        )

        for week in weeks:
            week["lessons"] = self.db.fetch(
                "SELECT * FROM lessons WHERE week_id=%s ORDER BY lesson_number",
                (week["id"],)
            )

        return course, weeks

    # ─────────────────────────────────────────────
    # GET BY TEACHER
    # ─────────────────────────────────────────────

    def get_by_teacher(self, teacher_id):
        return self.db.fetch(
            "SELECT * FROM courses WHERE teacher_id=%s ORDER BY name",
            (teacher_id,)
        )

    # ─────────────────────────────────────────────
    # CREATE
    # ─────────────────────────────────────────────

    def create(self, name, description, teacher_id, capacity):
        self.db.execute(
            "INSERT INTO courses (name, description, teacher_id, capacity) VALUES (%s,%s,%s,%s)",
            (name, description, teacher_id, capacity)
        )

    # ─────────────────────────────────────────────
    # UPDATE
    # ─────────────────────────────────────────────

    def update(self, course_id, name, description, teacher_id, capacity):
        self.db.execute(
            "UPDATE courses SET name=%s, description=%s, teacher_id=%s, capacity=%s WHERE id=%s",
            (name, description, teacher_id, capacity, course_id)
        )

    # ─────────────────────────────────────────────
    # DELETE
    # ─────────────────────────────────────────────

    def delete(self, course_id):
        self.db.execute("DELETE FROM courses WHERE id=%s", (course_id,))

    def close(self):
        self.db.close()
