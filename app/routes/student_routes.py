from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models.database import Database
from app.auth import login_required, student_required
from datetime import datetime
import os
from werkzeug.utils import secure_filename

student_bp = Blueprint("student", __name__)

UPLOAD_FOLDER = os.path.join("app", "static", "uploads", "submissions")
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx", "txt", "png", "jpg", "jpeg", "zip"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================
# STUDENT - DASHBOARD
# ============================================

@student_bp.route("/student/dashboard")
@login_required
@student_required
def dashboard():
    db = Database()
    student_id = session["user_id"]
    
    # Get enrolled courses
    courses = db.fetch("""
        SELECT c.id, c.name, c.description
        FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        WHERE e.student_id = %s
    """, (student_id,))
    
    # Get attendance
    attendance = db.fetchone("""
        SELECT COUNT(*) as total, SUM(status = 'present') as present
        FROM attendance WHERE student_id = %s
    """, (student_id,))
    
    # Get marks average
    avg_marks = db.fetchone("""
        SELECT ROUND(AVG(score / total * 100), 1) as average
        FROM marks WHERE student_id = %s
    """, (student_id,))
    
    # Get fees
    fees = db.fetch("SELECT status FROM fee_records WHERE student_id = %s", (student_id,))
    
    # Get pending tasks count
    pending_tasks = db.fetchone("""
        SELECT COUNT(*) as count
        FROM tasks t
        JOIN enrollments e ON t.course_id = e.course_id
        WHERE e.student_id = %s
          AND t.id NOT IN (
              SELECT task_id FROM task_submissions WHERE student_id = %s
          )
          AND (t.due_date IS NULL OR t.due_date >= NOW())
    """, (student_id, student_id))
    
    # Get recent notifications
    notifications = db.fetch("""
        SELECT * FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 5
    """, (student_id,))
    
    db.close()
    
    att_percent = 0
    if attendance and attendance["total"] > 0:
        att_percent = round((attendance["present"] or 0) / attendance["total"] * 100, 1)
    
    unpaid = sum(1 for f in fees if f["status"] == "unpaid")
    fee_status = "Unpaid" if unpaid > 0 else "Paid"
    
    return render_template(
        "home.html",
        username=session["username"],
        role=session["role"],
        courses=courses,
        att_percent=att_percent,
        avg_marks=avg_marks["average"] if avg_marks and avg_marks["average"] else 0,
        fee_status=fee_status,
        total_courses=len(courses),
        pending_tasks=pending_tasks["count"] if pending_tasks else 0,
        notifications=notifications,
        active_page="student_dashboard"
    )

# ============================================
# STUDENT - COURSES
# ============================================

@student_bp.route("/student/courses")
@login_required
@student_required
def courses():
    db = Database()
    student_id = session["user_id"]
    
    courses = db.fetch("""
        SELECT c.id, c.name, c.description,
               u.fullname as teacher_name,
               COUNT(DISTINCT t.id) as total_tasks,
               COUNT(DISTINCT sm.id) as total_materials
        FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        LEFT JOIN users u ON c.teacher_id = u.id
        LEFT JOIN tasks t ON c.id = t.course_id
        LEFT JOIN study_materials sm ON c.id = sm.course_id
        WHERE e.student_id = %s
        GROUP BY c.id, c.name, c.description, u.fullname
    """, (student_id,))
    
    db.close()
    
    return render_template(
        "student/courses.html",
        username=session["username"],
        role=session["role"],
        courses=courses,
        active_page="student_courses"
    )


@student_bp.route("/student/course/<int:course_id>")
@login_required
@student_required
def course_detail(course_id):
    db = Database()
    student_id = session["user_id"]
    
    # Verify enrollment
    enrollment = db.fetchone("""
        SELECT id FROM enrollments
        WHERE student_id=%s AND course_id=%s
    """, (student_id, course_id))
    
    if not enrollment:
        flash("You are not enrolled in this course.", "error")
        return redirect(url_for("student.courses"))
    
    # Get course details
    course = db.fetchone("""
        SELECT c.*, u.fullname as teacher_name
        FROM courses c
        LEFT JOIN users u ON c.teacher_id = u.id
        WHERE c.id = %s
    """, (course_id,))
    
    # Get weeks and lessons
    weeks = db.fetch(
        "SELECT * FROM weeks WHERE course_id=%s ORDER BY week_number",
        (course_id,)
    )
    for week in weeks:
        week["lessons"] = db.fetch(
            "SELECT * FROM lessons WHERE week_id=%s ORDER BY lesson_number",
            (week["id"],)
        )
    
    # Get study materials
    materials = db.fetch("""
        SELECT sm.*, c.name as course_name, w.title as week_title, w.week_number
        FROM study_materials sm
        JOIN courses c ON sm.course_id = c.id
        LEFT JOIN weeks w ON sm.week_id = w.id
        WHERE sm.course_id = %s
        ORDER BY w.week_number, sm.created_at DESC
    """, (course_id,))
    
    # Get tasks with submission status
    tasks = db.fetch("""
        SELECT t.*,
               w.title as week_title,
               ts.id as submission_id,
               ts.status as submission_status,
               ts.grade,
               ts.feedback,
               ts.submitted_at,
               ts.text_answer,
               ts.file_url as submission_file
        FROM tasks t
        LEFT JOIN weeks w ON t.week_id = w.id
        LEFT JOIN task_submissions ts
            ON t.id = ts.task_id AND ts.student_id = %s
        WHERE t.course_id = %s
        ORDER BY t.due_date ASC, t.created_at DESC
    """, (student_id, course_id))
    
    db.close()
    now = datetime.now()
    
    return render_template(
        "student/course_detail.html",
        username=session["username"],
        role=session["role"],
        course=course,
        weeks=weeks,
        materials=materials,
        tasks=tasks,
        now=now,
        active_page="student_courses"
    )


# ============================================
# STUDENT - SUBMIT TASK
# ============================================

@student_bp.route("/student/task/<int:task_id>/submit", methods=["POST"])
@login_required
@student_required
def submit_task(task_id):
    student_id = session["user_id"]
    text_answer = request.form.get("text_answer", "")
    file_url = None
    
    db = Database()
    task = db.fetchone("SELECT * FROM tasks WHERE id=%s", (task_id,))
    
    if not task:
        flash("Task not found.", "error")
        db.close()
        return redirect(url_for("student.courses"))
    
    # Check if already submitted
    existing = db.fetchone("""
        SELECT id FROM task_submissions
        WHERE task_id=%s AND student_id=%s
    """, (task_id, student_id))
    
    if existing:
        flash("You have already submitted this task.", "warning")
        db.close()
        return redirect(url_for("student.course_detail", course_id=task["course_id"]))
    
    # Check if overdue
    if task["due_date"] and datetime.now() > task["due_date"]:
        # Allow late submission but mark as late
        pass
    
    # Handle file upload
    if "file" in request.files and request.files["file"].filename != "":
        file = request.files["file"]
        if allowed_file(file.filename):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(file.filename)
            filename = f"sub_{student_id}_{task_id}_{int(datetime.now().timestamp())}_{filename}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            file_url = f"/static/uploads/submissions/{filename}"
        else:
            flash("File type not allowed.", "error")
            db.close()
            return redirect(url_for("student.course_detail", course_id=task["course_id"]))
    
    # Determine if late
    status = "submitted"
    if task["due_date"] and datetime.now() > task["due_date"]:
        status = "late"
    
    db.execute("""
        INSERT INTO task_submissions
            (task_id, student_id, text_answer, file_url, status)
        VALUES (%s, %s, %s, %s, %s)
    """, (task_id, student_id, text_answer, file_url, status))
    
    db.close()
    
    flash("Task submitted successfully!" if status == "submitted" else "Task submitted (late).", "success")
    return redirect(url_for("student.course_detail", course_id=task["course_id"]))


# ============================================
# STUDENT - RESOURCES
# ============================================

@student_bp.route("/student/resources")
@login_required
@student_required
def resources():
    db = Database()
    student_id = session["user_id"]
    
    # Get resources from enrolled courses
    resources = db.fetch("""
        SELECT r.*, c.name as course_name, u.fullname as teacher_name
        FROM resources r
        JOIN courses c ON r.course_id = c.id
        JOIN enrollments e ON c.id = e.course_id
        LEFT JOIN users u ON r.teacher_id = u.id
        WHERE e.student_id = %s
        ORDER BY r.created_at DESC
    """, (student_id,))
    
    # Get study materials from enrolled courses
    materials = db.fetch("""
        SELECT sm.*, c.name as course_name, w.title as week_title
        FROM study_materials sm
        JOIN courses c ON sm.course_id = c.id
        JOIN enrollments e ON c.id = e.course_id
        LEFT JOIN weeks w ON sm.week_id = w.id
        WHERE e.student_id = %s
        ORDER BY sm.created_at DESC
    """, (student_id,))
    
    db.close()
    
    return render_template(
        "student/resources.html",
        username=session["username"],
        role=session["role"],
        resources=resources,
        materials=materials,
        active_page="student_resources"
    )


# ============================================
# STUDENT - ATTENDANCE
# ============================================

@student_bp.route("/student/attendance")
@login_required
@student_required
def attendance():
    db = Database()
    student_id = session["user_id"]
    
    records = db.fetch("""
        SELECT a.date, a.status, c.name as course_name
        FROM attendance a
        JOIN courses c ON a.course_id = c.id
        WHERE a.student_id = %s
        ORDER BY a.date DESC
    """, (student_id,))
    
    summary = db.fetchone("""
        SELECT COUNT(*) as total,
               SUM(status = 'present') as present,
               SUM(status = 'absent') as absent
        FROM attendance WHERE student_id = %s
    """, (student_id,))
    
    db.close()
    
    att_percent = 0
    if summary and summary["total"] > 0:
        att_percent = round((summary["present"] or 0) / summary["total"] * 100, 1)
    
    return render_template(
        "student/attendance.html",
        username=session["username"],
        role=session["role"],
        records=records,
        summary=summary,
        att_percent=att_percent,
        active_page="student_attendance"
    )


# ============================================
# STUDENT - MARKS
# ============================================

@student_bp.route("/student/marks")
@login_required
@student_required
def marks():
    db = Database()
    student_id = session["user_id"]
    
    records = db.fetch("""
        SELECT m.title, m.score, m.total, c.name as course_name,
               ROUND(m.score / m.total * 100, 1) as percentage,
               (SELECT grade FROM grade_scale 
                WHERE ROUND(m.score / m.total * 100, 1) BETWEEN min_score AND max_score 
                LIMIT 1) as grade
        FROM marks m
        JOIN courses c ON m.course_id = c.id
        WHERE m.student_id = %s
        ORDER BY m.created_at DESC
    """, (student_id,))
    
    avg = db.fetchone("""
        SELECT ROUND(AVG(score / total * 100), 1) as average
        FROM marks WHERE student_id = %s
    """, (student_id,))
    
    db.close()
    
    return render_template(
        "student/marks.html",
        username=session["username"],
        role=session["role"],
        records=records,
        average=avg["average"] if avg and avg["average"] else 0,
        active_page="student_marks"
    )


# ============================================
# STUDENT - FEES
# ============================================

@student_bp.route("/student/fees")
@login_required
@student_required
def fees():
    db = Database()
    student_id = session["user_id"]
    
    records = db.fetch("""
        SELECT amount, description, status, due_date
        FROM fee_records WHERE student_id = %s
        ORDER BY due_date DESC
    """, (student_id,))
    
    db.close()
    
    total = sum(f["amount"] for f in records)
    paid = sum(f["amount"] for f in records if f["status"] == "paid")
    unpaid = sum(f["amount"] for f in records if f["status"] == "unpaid")
    
    return render_template(
        "student/fees.html",
        username=session["username"],
        role=session["role"],
        records=records,
        total=total,
        paid=paid,
        unpaid=unpaid,
        active_page="student_fees"
    )


# ============================================
# STUDENT - REPORTS
# ============================================

@student_bp.route("/student/reports")
@login_required
@student_required
def reports():
    db = Database()
    student_id = session["user_id"]
    
    # Get student info
    student = db.fetchone("SELECT * FROM users WHERE id=%s", (student_id,))
    
    # Overall Statistics
    stats = db.fetchone("""
        SELECT 
            (SELECT COUNT(*) FROM enrollments WHERE student_id = %s) as enrolled_courses,
            (SELECT ROUND(AVG(score / total * 100), 1) FROM marks WHERE student_id = %s) as overall_avg_marks,
            (SELECT ROUND(AVG(CASE WHEN status = 'present' THEN 1 ELSE 0 END) * 100, 2) 
             FROM attendance WHERE student_id = %s) as overall_attendance,
            (SELECT COUNT(*) FROM tasks t 
             JOIN enrollments e ON t.course_id = e.course_id 
             WHERE e.student_id = %s) as total_tasks,
            (SELECT COUNT(*) FROM task_submissions WHERE student_id = %s) as completed_tasks
    """, (student_id, student_id, student_id, student_id, student_id))
    
    # Calculate task completion rate
    if stats and stats['total_tasks'] > 0:
        stats['task_completion_rate'] = round((stats['completed_tasks'] / stats['total_tasks']) * 100, 2)
    else:
        stats['task_completion_rate'] = 0
    
    # Course-wise performance
    course_performance = db.fetch("""
        SELECT 
            c.id,
            c.name,
            c.code,
            c.credits,
            ROUND(AVG(m.score / m.total * 100), 1) as avg_marks,
            (SELECT grade FROM grade_scale 
             WHERE ROUND(AVG(m.score / m.total * 100), 1) BETWEEN min_score AND max_score 
             LIMIT 1) as grade,
            (SELECT gpa FROM grade_scale 
             WHERE ROUND(AVG(m.score / m.total * 100), 1) BETWEEN min_score AND max_score 
             LIMIT 1) as gpa,
            ROUND(AVG(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) * 100, 2) as attendance_percentage,
            COUNT(DISTINCT a.id) as total_attendance,
            SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_attendance,
            (SELECT COUNT(*) FROM tasks t WHERE t.course_id = c.id) as course_tasks,
            (SELECT COUNT(*) FROM task_submissions ts 
             WHERE ts.task_id IN (SELECT id FROM tasks WHERE course_id = c.id) 
             AND ts.student_id = %s) as completed_course_tasks
        FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        LEFT JOIN marks m ON c.id = m.course_id AND m.student_id = %s
        LEFT JOIN attendance a ON c.id = a.course_id AND a.student_id = %s
        WHERE e.student_id = %s
        GROUP BY c.id, c.name, c.code, c.credits
        ORDER BY avg_marks DESC
    """, (student_id, student_id, student_id, student_id))
    
    # Calculate GPA
    total_credits = 0
    total_grade_points = 0
    for course in course_performance:
        if course.get('gpa') and course.get('credits'):
            total_grade_points += course['gpa'] * course['credits']
            total_credits += course['credits']
    
    gpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0
    
    # Fee summary
    fee_summary = db.fetchone("""
        SELECT 
            SUM(amount) as total_fees,
            SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as paid_fees,
            SUM(CASE WHEN status IN ('unpaid', 'partial') THEN amount ELSE 0 END) as pending_fees
        FROM fee_records
        WHERE student_id = %s
    """, (student_id,))
    
    db.close()
    
    return render_template(
        "student/reports.html",
        username=session["username"],
        role=session["role"],
        student=student,
        stats=stats,
        course_performance=course_performance,
        gpa=gpa,
        fee_summary=fee_summary,
        active_page="student_reports"
    )