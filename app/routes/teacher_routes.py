from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models.database import Database
from datetime import datetime, date
from app.models.attendance_model import AttendanceModel
from app.models.marks_model import MarksModel

# Define the blueprint FIRST
teacher_bp = Blueprint("teacher", __name__)

def teacher_required():
    return "role" not in session or session["role"] != "teacher"

# ============================================
# TEACHER - DASHBOARD
# ============================================

@teacher_bp.route("/teacher/dashboard")
def dashboard():
    if teacher_required():
        return redirect(url_for("auth.login"))
    
    db = Database()
    teacher_id = session["user_id"]
    
    total_students = db.fetchone("""
        SELECT COUNT(DISTINCT e.student_id) as count
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE c.teacher_id = %s
    """, (teacher_id,))
    
    total_courses = db.fetchone("""
        SELECT COUNT(*) as count FROM courses WHERE teacher_id = %s
    """, (teacher_id,))
    
    total_resources = db.fetchone("""
        SELECT COUNT(*) as count FROM resources WHERE teacher_id = %s
    """, (teacher_id,))
    
    total_tasks = db.fetchone("""
        SELECT COUNT(*) as count FROM tasks WHERE teacher_id = %s
    """, (teacher_id,))
    
    students = db.fetch("""
        SELECT DISTINCT u.fullname, u.email
        FROM users u
        JOIN enrollments e ON u.id = e.student_id
        JOIN courses c ON e.course_id = c.id
        WHERE c.teacher_id = %s
        LIMIT 5
    """, (teacher_id,))
    
    db.close()
    
    return render_template(
        "teacher/dashboard.html",
        username=session["username"],
        role=session["role"],
        total_students=total_students["count"] if total_students else 0,
        total_courses=total_courses["count"] if total_courses else 0,
        assignments=total_resources["count"] if total_resources else 0,
        total_tasks=total_tasks["count"] if total_tasks else 0,
        students=students,
    )

# ============================================
# TEACHER - STUDENTS
# ============================================

@teacher_bp.route("/teacher/students")
def students():
    if teacher_required():
        return redirect(url_for("auth.login"))
    
    db = Database()
    teacher_id = session["user_id"]
    
    students = db.fetch("""
        SELECT DISTINCT u.id, u.fullname, u.email, u.username
        FROM users u
        JOIN enrollments e ON u.id = e.student_id
        JOIN courses c ON e.course_id = c.id
        WHERE c.teacher_id = %s
    """, (teacher_id,))
    
    db.close()
    
    return render_template(
        "teacher/students.html",
        username=session["username"],
        role=session["role"],
        students=students,
    )

# ============================================
# TEACHER - COURSES
# ============================================

@teacher_bp.route("/teacher/courses")
def courses():
    if teacher_required():
        return redirect(url_for("auth.login"))
    
    db = Database()
    courses = db.fetch("""
        SELECT c.*,
               COUNT(e.id) AS enrolled
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        WHERE c.teacher_id = %s
        GROUP BY c.id
        ORDER BY c.name
    """, (session["user_id"],))
    db.close()
    
    return render_template(
        "teacher/courses.html",
        username=session["username"],
        role=session["role"],
        courses=courses,
    )

@teacher_bp.route("/teacher/course/<int:course_id>")
def course_detail(course_id):
    if teacher_required():
        return redirect(url_for("auth.login"))
    
    db = Database()
    course = db.fetchone("SELECT * FROM courses WHERE id=%s AND teacher_id=%s", (course_id, session["user_id"]))
    
    if not course:
        flash("Course not found or you don't have permission.", "error")
        db.close()
        return redirect(url_for("teacher.courses"))
    
    weeks = db.fetch(
        "SELECT * FROM weeks WHERE course_id=%s ORDER BY week_number",
        (course_id,)
    )
    for week in weeks:
        week["lessons"] = db.fetch(
            "SELECT * FROM lessons WHERE week_id=%s ORDER BY lesson_number",
            (week["id"],)
        )
    
    total_lessons = sum(len(week["lessons"]) for week in weeks)
    
    materials = db.fetch("""
        SELECT sm.*, w.title as week_title
        FROM study_materials sm
        LEFT JOIN weeks w ON sm.week_id = w.id
        WHERE sm.course_id = %s
        ORDER BY sm.created_at DESC
    """, (course_id,))
    
    tasks = db.fetch("""
        SELECT t.*, w.title as week_title,
               COUNT(ts.id) as submission_count
        FROM tasks t
        LEFT JOIN weeks w ON t.week_id = w.id
        LEFT JOIN task_submissions ts ON t.id = ts.task_id
        WHERE t.course_id = %s
        GROUP BY t.id
        ORDER BY t.created_at DESC
    """, (course_id,))
    
    db.close()
    
    return render_template(
        "teacher/course_detail.html",
        username=session["username"],
        role=session["role"],
        course=course,
        weeks=weeks,
        total_lessons=total_lessons,
        materials=materials,
        tasks=tasks,
        now=datetime.now()
    )

# ============================================
# TEACHER - RESOURCES (Complete)
# ============================================

@teacher_bp.route("/teacher/resources", methods=["GET", "POST"])
def resources():
    if teacher_required():
        return redirect(url_for("auth.login"))
    
    db = Database()
    teacher_id = session["user_id"]
    
    # Get teacher's courses for dropdown
    courses = db.fetch("SELECT id, name FROM courses WHERE teacher_id = %s", (teacher_id,))
    
    if request.method == "POST":
        course_id = request.form.get("course_id")
        title = request.form.get("title")
        description = request.form.get("description")
        link = request.form.get("link")
        
        if not all([course_id, title]):
            flash("Course and Title are required.", "error")
            db.close()
            return redirect(url_for("teacher.resources"))
        
        db.execute("""
            INSERT INTO resources (course_id, teacher_id, title, description, link)
            VALUES (%s, %s, %s, %s, %s)
        """, (course_id, teacher_id, title, description, link))
        
        # Send notification to students in this course
        students = db.fetch("SELECT student_id FROM enrollments WHERE course_id=%s", (course_id,))
        for student in students:
            db.execute("""
                INSERT INTO notifications (user_id, type, title, message, link)
                VALUES (%s, 'system', 'New Resource Added', 
                       CONCAT('A new resource has been added to your course: ', %s),
                       '/student/resources')
            """, (student['student_id'], title))
        
        flash("Resource added successfully.", "success")
        db.close()
        return redirect(url_for("teacher.resources"))
    
    # Get all resources for this teacher
    all_resources = db.fetch("""
        SELECT r.*, c.name as course_name
        FROM resources r
        JOIN courses c ON r.course_id = c.id
        WHERE r.teacher_id = %s
        ORDER BY r.created_at DESC
    """, (teacher_id,))
    
    db.close()
    
    return render_template(
        "teacher/resources.html",
        username=session["username"],
        role=session["role"],
        courses=courses,
        resources=all_resources,
    )

@teacher_bp.route("/teacher/resources/delete/<int:resource_id>", methods=["POST"])
def delete_resource(resource_id):
    if teacher_required():
        return redirect(url_for("auth.login"))
    
    db = Database()
    db.execute(
        "DELETE FROM resources WHERE id=%s AND teacher_id=%s",
        (resource_id, session["user_id"])
    )
    db.close()
    flash("Resource deleted.", "success")
    return redirect(url_for("teacher.resources"))
# ============================================
# TEACHER - MARKS
# ============================================

@teacher_bp.route("/teacher/marks")
def teacher_marks():
    if teacher_required():
        return redirect(url_for("auth.login"))
    
    db = Database()
    teacher_id = session["user_id"]
    
    courses = db.fetch("""
        SELECT c.*, COUNT(DISTINCT e.id) as enrolled
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        WHERE c.teacher_id = %s
        GROUP BY c.id
    """, (teacher_id,))
    
    db.close()
    
    return render_template(
        "teacher/marks.html",
        username=session["username"],
        role=session["role"],
        courses=courses
    )

@teacher_bp.route("/teacher/marks/course/<int:course_id>", methods=["GET", "POST"])
def teacher_manage_marks(course_id):
    if teacher_required():
        return redirect(url_for("auth.login"))
    
    db = Database()
    course = db.fetchone(
        "SELECT * FROM courses WHERE id=%s AND teacher_id=%s",
        (course_id, session["user_id"])
    )
    
    if not course:
        flash("Course not found or you don't have permission.", "error")
        db.close()
        return redirect(url_for("teacher.teacher_marks"))
    
    if request.method == "POST":
        marks_model = MarksModel()
        title = request.form.get("title")
        total = float(request.form.get("total", 100))
        exam_type = request.form.get("exam_type", "assignment")
        weightage = float(request.form.get("weightage", 100))
        
        students = db.fetch(
            "SELECT u.id FROM users u JOIN enrollments e ON u.id=e.student_id WHERE e.course_id=%s",
            (course_id,)
        )
        
        marked_count = 0
        for student in students:
            score = request.form.get(f"score_{student['id']}")
            if score:
                success, message = marks_model.add_marks(
                    student['id'], course_id, title, float(score), total, exam_type, weightage
                )
                if success:
                    marked_count += 1
                    # Send notification to student
                    db.execute("""
                        INSERT INTO notifications (user_id, type, title, message, link)
                        VALUES (%s, 'grade', 'New Grade Added', 
                               CONCAT('You received a new grade for ', %s, ' in ', %s),
                               '/student/marks')
                    """, (student['id'], title, course['name']))
        
        marks_model.close()
        flash(f"Marks added for {marked_count} students.", "success")
        db.close()
        return redirect(url_for("teacher.teacher_manage_marks", course_id=course_id))
    
    students = db.fetch("""
        SELECT u.id, u.fullname, u.email,
               (SELECT ROUND(AVG(score / total * 100), 1) 
                FROM marks m 
                WHERE m.student_id = u.id AND m.course_id = %s) as avg_percentage,
               (SELECT COUNT(*) FROM marks m 
                WHERE m.student_id = u.id AND m.course_id = %s) as marks_count
        FROM users u
        JOIN enrollments e ON u.id = e.student_id
        WHERE e.course_id=%s AND u.role='student'
        ORDER BY u.fullname
    """, (course_id, course_id, course_id))
    
    existing_marks = db.fetch("""
        SELECT m.*, u.fullname as student_name
        FROM marks m
        JOIN users u ON m.student_id = u.id
        WHERE m.course_id = %s
        ORDER BY m.created_at DESC
    """, (course_id,))
    
    db.close()
    
    return render_template(
        "teacher/manage_marks.html",
        username=session["username"],
        role=session["role"],
        course=course,
        students=students,
        existing_marks=existing_marks
    )

# ============================================
# TEACHER - ATTENDANCE (Using attendance blueprint)
# ============================================

# REMOVE THIS REDIRECT - It's causing the loop
# @teacher_bp.route("/teacher/attendance")
# def teacher_attendance_redirect():
#     if teacher_required():
#         return redirect(url_for("auth.login"))
#     return redirect(url_for("attendance.teacher_attendance"))

# Instead, use the attendance blueprint directly
# The attendance routes are already registered under the "attendance" blueprint
# So we don't need a redirect here


# ============================================
# TEACHER - REPORTS
# ============================================

@teacher_bp.route("/teacher/reports")
def teacher_reports():
    if teacher_required():
        return redirect(url_for("auth.login"))
    
    db = Database()
    teacher_id = session["user_id"]
    
    course_performance = db.fetch("""
        SELECT 
            c.id,
            c.name,
            COUNT(DISTINCT e.student_id) as total_students,
            ROUND(AVG(m.score / m.total * 100), 1) as avg_marks,
            ROUND(AVG(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) * 100, 2) as avg_attendance,
            COUNT(DISTINCT t.id) as total_tasks,
            COUNT(DISTINCT ts.id) as total_submissions,
            ROUND(COUNT(DISTINCT ts.id) / NULLIF(COUNT(DISTINCT t.id) * COUNT(DISTINCT e.student_id), 0) * 100, 2) as completion_rate
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        LEFT JOIN marks m ON c.id = m.course_id
        LEFT JOIN attendance a ON c.id = a.course_id
        LEFT JOIN tasks t ON c.id = t.course_id
        LEFT JOIN task_submissions ts ON t.id = ts.task_id
        WHERE c.teacher_id = %s
        GROUP BY c.id, c.name
        ORDER BY completion_rate DESC
    """, (teacher_id,))
    
    stats = db.fetchone("""
        SELECT 
            COUNT(DISTINCT e.student_id) as total_students,
            COUNT(DISTINCT c.id) as total_courses,
            ROUND(AVG(m.score / m.total * 100), 1) as overall_avg_marks,
            ROUND(AVG(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) * 100, 2) as overall_attendance
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        LEFT JOIN marks m ON c.id = m.course_id
        LEFT JOIN attendance a ON c.id = a.course_id
        WHERE c.teacher_id = %s
    """, (teacher_id,))
    
    db.close()
    
    return render_template(
        "teacher/reports.html",
        username=session["username"],
        role=session["role"],
        course_performance=course_performance,
        stats=stats
    )