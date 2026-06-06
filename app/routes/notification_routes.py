from flask import Blueprint

notification_bp = Blueprint(
    "notification",
    __name__,
    url_prefix="/notifications"
)

@notification_bp.route("/")
def notifications():
    return render_template(
        "notifications.html"
    )

@notification_bp.route("/preferences")
def preferences():
    return render_template(
        "notification_preferences.html"
    )
@notification_bp.route("/mark-read/<int:id>")
def mark_read(id):
    pass
notification_model.mark_as_read(id)

from flask import flash

from app.models.database import Database
from datetime import datetime

class MarksModel:
    def __init__(self):
        self.db = Database()

    def add_marks(self, student_id, course_id, title, score, total, 
                  exam_type='assignment', weightage=100):
        """Add marks with validation"""
        if score > total:
            return False, "Score cannot exceed total marks"
        
        # Check for duplicate marks entry
        existing = self.db.fetchone(
            "SELECT id FROM marks WHERE student_id=%s AND course_id=%s AND title=%s",
            (student_id, course_id, title)
        )
        
        if existing:
            return False, "Marks already exist for this assessment"
        
        self.db.execute("""
            INSERT INTO marks (student_id, course_id, title, score, total, 
                             exam_type, weightage, date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURDATE())
        """, (student_id, course_id, title, score, total, exam_type, weightage))
        
        return True, "Marks added successfully"

    def update_marks(self, mark_id, score, total, changed_by, reason=None):
        """Update marks with history tracking"""
        existing = self.db.fetchone("SELECT * FROM marks WHERE id=%s", (mark_id,))
        
        if not existing:
            return False, "Marks not found"
        
        if score > total:
            return False, "Score cannot exceed total marks"
        
        self.db.execute("""
            UPDATE marks SET score=%s, total=%s, updated_at=NOW()
            WHERE id=%s
        """, (score, total, mark_id))
        
        # Log history
        self.db.execute("""
            INSERT INTO marks_history (mark_id, old_score, new_score, changed_by, reason)
            VALUES (%s, %s, %s, %s, %s)
        """, (mark_id, existing['score'], score, changed_by, reason))
        
        return True, "Marks updated successfully"

    def get_student_marks(self, student_id, course_id=None):
        """Get student marks with course details"""
        query = """
            SELECT m.*, c.name as course_name,
                   ROUND((m.score / m.total) * 100, 2) as percentage,
                   (SELECT g.grade FROM grade_scale g 
                    WHERE ROUND((m.score / m.total) * 100, 2) BETWEEN g.min_score AND g.max_score
                    LIMIT 1) as grade
            FROM marks m
            JOIN courses c ON m.course_id = c.id
            WHERE m.student_id = %s
        """
        params = [student_id]
        
        if course_id:
            query += " AND m.course_id = %s"
            params.append(course_id)
        
        query += " ORDER BY m.date DESC"
        
        return self.db.fetch(query, tuple(params))

    def calculate_course_results(self, student_id, course_id):
        """Calculate overall results for a student in a course"""
        marks = self.db.fetch("""
            SELECT score, total, weightage
            FROM marks
            WHERE student_id=%s AND course_id=%s
        """, (student_id, course_id))
        
        if not marks:
            return None
        
        total_weighted_score = 0
        
        for m in marks:
            percentage = (m['score'] / m['total']) * 100
            weighted_score = percentage * (m['weightage'] / 100)
            total_weighted_score += weighted_score
        
        avg_percentage = total_weighted_score / len(marks) if marks else 0
        
        grade = self.db.fetchone("""
            SELECT grade FROM grade_scale
            WHERE %s BETWEEN min_score AND max_score
            LIMIT 1
        """, (avg_percentage,))
        
        return {
            'percentage': round(avg_percentage, 2),
            'grade': grade['grade'] if grade else 'F'
        }

    def get_course_result_summary(self, course_id):
        """Get result summary for all students in a course"""
        students = self.db.fetch("""
            SELECT DISTINCT u.id, u.fullname
            FROM users u
            JOIN enrollments e ON u.id = e.student_id
            WHERE e.course_id = %s AND u.role = 'student'
        """, (course_id,))
        
        results = []
        for student in students:
            result = self.calculate_course_results(student['id'], course_id)
            if result:
                results.append({
                    'student_id': student['id'],
                    'name': student['fullname'],
                    'percentage': result['percentage'],
                    'grade': result['grade']
                })
        
        return results

    def get_grade_scale(self):
        """Get all grade scale configurations"""
        return self.db.fetch("SELECT * FROM grade_scale ORDER BY min_score DESC")

    def generate_report_card(self, student_id):
        """Generate report card for a student"""
        student = self.db.fetchone("""
            SELECT u.fullname, u.email, u.username
            FROM users u
            WHERE u.id = %s
        """, (student_id,))
        
        if not student:
            return None
        
        courses = self.db.fetch("""
            SELECT c.id, c.name, c.code, c.credits,
                   (SELECT ROUND(AVG((m.score / m.total) * 100), 2) 
                    FROM marks m 
                    WHERE m.course_id = c.id AND m.student_id = %s) as avg_percentage,
                   (SELECT g.grade FROM grade_scale g 
                    WHERE (SELECT ROUND(AVG((m.score / m.total) * 100), 2) 
                           FROM marks m 
                           WHERE m.course_id = c.id AND m.student_id = %s) 
                    BETWEEN g.min_score AND g.max_score LIMIT 1) as grade
            FROM courses c
            JOIN enrollments e ON c.id = e.course_id
            WHERE e.student_id = %s AND e.status = 'active'
        """, (student_id, student_id, student_id))
        
        total_points = 0
        total_credits = 0
        
        for course in courses:
            if course['grade']:
                grade_info = self.db.fetchone(
                    "SELECT gpa FROM grade_scale WHERE grade=%s LIMIT 1",
                    (course['grade'],)
                )
                if grade_info:
                    total_points += grade_info['gpa'] * (course['credits'] or 3)
                    total_credits += (course['credits'] or 3)
        
        gpa = total_points / total_credits if total_credits > 0 else 0
        
        attendance = self.db.fetchone("""
            SELECT 
                COUNT(*) as total_classes,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
                ROUND(AVG(CASE WHEN status = 'present' THEN 1 ELSE 0 END) * 100, 2) as percentage
            FROM attendance
            WHERE student_id = %s
        """, (student_id,))
        
        return {
            'student': student,
            'courses': courses,
            'gpa': round(gpa, 2),
            'total_credits': total_credits,
            'attendance': attendance,
            'generated_at': datetime.now()
        }

    def close(self):
        self.db.close()