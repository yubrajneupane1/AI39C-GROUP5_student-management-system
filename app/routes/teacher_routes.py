from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models.database import Database
from app.auth import login_required, teacher_required
from datetime import datetime, date
from app.models.attendance_model import AttendanceModel
from app.models.marks_model import MarksModel
import os
from werkzeug.utils import secure_filename

teacher_bp = Blueprint("teacher", __name__)

UPLOAD_FOLDER = os.path.join("app", "static", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx", "txt", "png", "jpg", "jpeg", "zip"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================
# TEACHER - DASHBOARD
# ============================================

@teacher_bp.route("/teacher/dashboard")
@login_required
@teacher_required
def dashboard():
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
@login_required
@teacher_required
def students():
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
@login_required
@teacher_required
def courses():
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
@login_required
@teacher_required
def course_detail(course_id):
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
# TEACHER - ADD WEEK
# ============================================

@teacher_bp.route("/teacher/course/<int:course_id>/week/add", methods=["POST"])
@login_required
@teacher_required
def add_week(course_id):
    week_number = request.form["week_number"]
    title = request.form["title"]
    
    db = Database()
    course = db.fetchone("SELECT id FROM courses WHERE id=%s AND teacher_id=%s", (course_id, session["user_id"]))
    if not course:
        flash("Course not found or you don't have permission.", "error")
        db.close()
        return redirect(url_for("teacher.courses"))
    
    db.execute(
        "INSERT INTO weeks (course_id, week_number, title) VALUES (%s,%s,%s)",
        (course_id, week_number, title)
    )
    db.close()
    
    flash("Week added successfully.", "success")
    return redirect(url_for("teacher.course_detail", course_id=course_id))

# ============================================
# TEACHER - ADD LESSON
# ============================================

@teacher_bp.route("/teacher/week/<int:week_id>/lesson/add", methods=["POST"])
@login_required
@teacher_required
def add_lesson(week_id):
    lesson_number = request.form["lesson_number"]
    title = request.form["title"]
    content = request.form.get("content", "")
    
    db = Database()
    week = db.fetchone("SELECT * FROM weeks WHERE id=%s", (week_id,))
    if not week:
        flash("Week not found.", "error")
        db.close()
        return redirect(url_for("teacher.courses"))
    
    course = db.fetchone("SELECT id FROM courses WHERE id=%s AND teacher_id=%s", (week["course_id"], session["user_id"]))
    if not course:
        flash("You don't have permission.", "error")
        db.close()
        return redirect(url_for("teacher.courses"))
    
    db.execute(
        "INSERT INTO lessons (week_id, lesson_number, title, content) VALUES (%s,%s,%s,%s)",
        (week_id, lesson_number, title, content)
    )
    db.close()
    
    flash("Lesson added successfully.", "success")
    return redirect(url_for("teacher.course_detail", course_id=week["course_id"]))

# ============================================
# TEACHER - ADD MATERIAL
# ============================================

@teacher_bp.route("/teacher/course/<int:course_id>/material/add", methods=["POST"])
@login_required
@teacher_required
def add_material(course_id):
    teacher_id = session["user_id"]
    title = request.form.get("title")
    description = request.form.get("description", "")
    material_type = request.form.get("material_type", "file")
    week_id = request.form.get("week_id") or None
    file_url = None
    
    db = Database()
    course = db.fetchone("SELECT id FROM courses WHERE id=%s AND teacher_id=%s", (course_id, session["user_id"]))
    if not course:
        flash("Course not found or you don't have permission.", "error")
        db.close()
        return redirect(url_for("teacher.courses"))
    
    if "file" in request.files and request.files["file"].filename != "":
        file = request.files["file"]
        if allowed_file(file.filename):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(file.filename)
            filename = f"{int(datetime.now().timestamp())}_{filename}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            file_url = f"/static/uploads/{filename}"
        else:
            flash("File type not allowed.")
            db.close()
            return redirect(url_for("teacher.course_detail", course_id=course_id))
    else:
        file_url = request.form.get("link_url") or None
    
    db.execute("""
        INSERT INTO study_materials
            (course_id, week_id, teacher_id, material_type, title, description, file_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (course_id, week_id, teacher_id, material_type, title, description, file_url))
    db.close()
    
    flash("Study material added successfully.", "success")
    return redirect(url_for("teacher.course_detail", course_id=course_id))

# ============================================
# TEACHER - DELETE MATERIAL
# ============================================

@teacher_bp.route("/teacher/material/delete/<int:material_id>", methods=["POST"])
@login_required
@teacher_required
def delete_material(material_id):
    db = Database()
    mat = db.fetchone(
        "SELECT * FROM study_materials WHERE id=%s AND teacher_id=%s",
        (material_id, session["user_id"])
    )
    if mat:
        if mat["file_url"] and mat["file_url"].startswith("/static/uploads/"):
            disk_path = os.path.join("app", mat["file_url"].lstrip("/"))
            if os.path.exists(disk_path):
                os.remove(disk_path)
        db.execute("DELETE FROM study_materials WHERE id=%s", (material_id,))
        flash("Material deleted.", "success")
        course_id = mat["course_id"]
    else:
        flash("Not found.", "error")
        course_id = request.referrer
    db.close()
    return redirect(url_for("teacher.course_detail", course_id=course_id))

# ============================================
# TEACHER - ADD TASK
# ============================================

@teacher_bp.route("/teacher/course/<int:course_id>/task/add", methods=["POST"])
@login_required
@teacher_required
def add_task(course_id):
    teacher_id = session["user_id"]
    title = request.form.get("title")
    description = request.form.get("description", "")
    week_id = request.form.get("week_id") or None
    time_limit = request.form.get("time_limit_minutes") or None
    due_date_str = request.form.get("due_date") or None
    submission_type = request.form.get("submission_type", "text")
    
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            due_date = None
    
    db = Database()
    course = db.fetchone("SELECT id FROM courses WHERE id=%s AND teacher_id=%s", (course_id, session["user_id"]))
    if not course:
        flash("Course not found or you don't have permission.", "error")
        db.close()
        return redirect(url_for("teacher.courses"))
    
    db.execute("""
        INSERT INTO tasks
            (course_id, week_id, teacher_id, title, description,
             time_limit_minutes, due_date, submission_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (course_id, week_id, teacher_id, title, description,
          time_limit, due_date, submission_type))
    db.close()
    
    flash("Task created successfully.", "success")
    return redirect(url_for("teacher.course_detail", course_id=course_id))

# ============================================
# TEACHER - DELETE TASK
# ============================================

@teacher_bp.route("/teacher/task/delete/<int:task_id>", methods=["POST"])
@login_required
@teacher_required
def delete_task(task_id):
    db = Database()
    task = db.fetchone(
        "SELECT * FROM tasks WHERE id=%s AND teacher_id=%s",
        (task_id, session["user_id"])
    )
    if task:
        db.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
        flash("Task deleted.", "success")
        course_id = task["course_id"]
    else:
        flash("Task not found.", "error")
        course_id = 0
    db.close()
    return redirect(url_for("teacher.course_detail", course_id=course_id))

# ============================================
# TEACHER - TASK SUBMISSIONS
# ============================================

@teacher_bp.route("/teacher/task/<int:task_id>/submissions")
@login_required
@teacher_required
def task_submissions(task_id):
    db = Database()
    task = db.fetchone("SELECT * FROM tasks WHERE id=%s", (task_id,))
    
    if not task:
        flash("Task not found.", "error")
        db.close()
        return redirect(url_for("teacher.courses"))
    
    if task["teacher_id"] != session["user_id"]:
        flash("You don't have permission.", "error")
        db.close()
        return redirect(url_for("teacher.courses"))
    
    submissions = db.fetch("""
        SELECT ts.*, u.fullname as student_name, u.username as student_username
        FROM task_submissions ts
        JOIN users u ON ts.student_id = u.id
        WHERE ts.task_id = %s
        ORDER BY ts.submitted_at DESC
    """, (task_id,))
    
    db.close()
    
    return render_template(
        "teacher/task_submissions.html",
        username=session["username"],
        role=session["role"],
        task=task,
        submissions=submissions,
    )

# ============================================
# TEACHER - GRADE SUBMISSION
# ============================================

@teacher_bp.route("/teacher/submission/<int:submission_id>/grade", methods=["POST"])
@login_required
@teacher_required
def grade_submission(submission_id):
    grade = request.form.get("grade")
    feedback = request.form.get("feedback", "")
    task_id = request.form.get("task_id")
    
    db = Database()
    db.execute("""
        UPDATE task_submissions
        SET grade=%s, feedback=%s, status='graded'
        WHERE id=%s
    """, (grade, feedback, submission_id))
    db.close()
    
    flash("Submission graded successfully.", "success")
    return redirect(url_for("teacher.task_submissions", task_id=task_id))

# ============================================
# TEACHER - RESOURCES
# ============================================

@teacher_bp.route("/teacher/resources", methods=["GET", "POST"])
@login_required
@teacher_required
def resources():
    db = Database()
    teacher_id = session["user_id"]
    
    courses = db.fetch("SELECT id, name FROM courses WHERE teacher_id = %s", (teacher_id,))
    
    if request.method == "POST":
        course_id = request.form.get("course_id")
        title = request.form.get("title")
        description = request.form.get("description")
        link = request.form.get("link")
        
        db.execute("""
            INSERT INTO resources (course_id, teacher_id, title, description, link)
            VALUES (%s, %s, %s, %s, %s)
        """, (course_id, teacher_id, title, description, link))
        
        flash("Resource added successfully.", "success")
        db.close()
        return redirect(url_for("teacher.resources"))
    
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
@login_required
@teacher_required
def delete_resource(resource_id):
    db = Database()
    db.execute(
        "DELETE FROM resources WHERE id=%s AND teacher_id=%s",
        (resource_id, session["user_id"])
    )
    db.close()
    flash("Resource deleted.", "success")
    return redirect(url_for("teacher.resources"))

# ============================================
# TEACHER - REPORTS
# ============================================

@teacher_bp.route("/teacher/reports")
@login_required
@teacher_required
def teacher_reports():
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
        stats=stats,
    )

# ============================================
# TEACHER - MARKS
# ============================================

@teacher_bp.route("/teacher/marks")
@login_required
@teacher_required
def teacher_marks():
    db = Database()
    teacher_id = session["user_id"]
    
    courses = db.fetch("""
        SELECT c.*, COUNT(DISTINCT e.id) as enrolled
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        WHERE c.teacher_id = %s
        GROUP BY c.id
        ORDER BY c.name
    """, (teacher_id,))
    
    db.close()
    
    return render_template(
        "teacher/marks.html",
        username=session["username"],
        role=session["role"],
        courses=courses
    )


@teacher_bp.route("/teacher/marks/course/<int:course_id>", methods=["GET", "POST"])
@login_required
@teacher_required
def teacher_manage_marks(course_id):
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


@teacher_bp.route("/teacher/marks/update/<int:mark_id>", methods=["POST"])
@login_required
@teacher_required
def teacher_update_marks(mark_id):
    score = request.form.get("score")
    total = request.form.get("total", 100)
    reason = request.form.get("reason", "")
    
    marks_model = MarksModel()
    success, message = marks_model.update_marks(
        mark_id, float(score), float(total), session["user_id"], reason
    )
    marks_model.close()
    
    flash(message, "success" if success else "error")
    return redirect(request.referrer or url_for("teacher.teacher_marks"))


@teacher_bp.route("/teacher/marks/delete/<int:mark_id>", methods=["POST"])
@login_required
@teacher_required
def teacher_delete_marks(mark_id):
    db = Database()
    db.execute("DELETE FROM marks WHERE id=%s", (mark_id,))
    db.close()
    
    flash("Marks record deleted successfully.", "success")
    return redirect(request.referrer or url_for("teacher.teacher_marks"))