from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from app.models.database import Database
from app.models.attendance_model import AttendanceModel
from app.models.marks_model import MarksModel
from app.models.fee_model import FeeModel
from datetime import datetime, date

admin_bp = Blueprint("admin", __name__)

def admin_required():
    return "role" not in session or session["role"] != "admin"

# ============================================
# ADMIN DASHBOARD
# ============================================

@admin_bp.route("/admin/dashboard")
def dashboard():
    if admin_required():
        return redirect(url_for("auth.login"))

    db = Database()
    
    total_students = db.fetchone("SELECT COUNT(*) as count FROM users WHERE role='student'")
    total_teachers = db.fetchone("SELECT COUNT(*) as count FROM users WHERE role='teacher'")
    total_courses = db.fetchone("SELECT COUNT(*) as count FROM courses")
    
    attendance_today = db.fetchone("""
        SELECT COUNT(*) as count FROM attendance 
        WHERE date=CURDATE() AND status='present'
    """)
    
    pending_fees = db.fetchone("""
        SELECT SUM(amount) as total FROM fee_records 
        WHERE status IN ('unpaid', 'partial')
    """)
    
    students = db.fetch("SELECT * FROM users WHERE role='student' ORDER BY id DESC LIMIT 5")
    teachers = db.fetch("SELECT * FROM users WHERE role='teacher' LIMIT 5")
    
    db.close()

    return render_template(
        "admin/dashboard.html",
        username=session["username"],
        role=session["role"],
        total_students=total_students["count"] if total_students else 0,
        total_teachers=total_teachers["count"] if total_teachers else 0,
        total_courses=total_courses["count"] if total_courses else 0,
        attendance_today=attendance_today["count"] if attendance_today else 0,
        pending_fees=pending_fees["total"] if pending_fees else 0,
        students=students,
        teachers=teachers,
    )

# ============================================
# ADMIN - STUDENT MANAGEMENT
# ============================================

@admin_bp.route("/admin/students")
def students():
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    students = db.fetch("SELECT * FROM users WHERE role='student'")
    db.close()
    return render_template(
        "admin/students.html",
        username=session["username"],
        role=session["role"],
        students=students,
    )

@admin_bp.route("/admin/users/create", methods=["GET", "POST"])
def create_user():
    if admin_required():
        return redirect(url_for("auth.login"))
    from app.models.user_model import User
    if request.method == "POST":
        name = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")
        if not all([name, email, username, password, role]):
            flash("All fields are required.", "error")
            return redirect(url_for("admin.create_user"))
        user = User(name=name, email=email, username=username, password=password, role=role)
        if user.email_exists():
            flash("Email is already in use.", "error")
            return redirect(url_for("admin.create_user"))
        if user.username_exists():
            flash("Username is already taken.", "error")
            return redirect(url_for("admin.create_user"))
        user.save()
        flash(f"Account for '{username}' ({role}) created successfully.", "success")
        return redirect(url_for("admin.students"))
    return render_template(
        "admin/create_user.html",
        username=session["username"],
        role=session["role"],
    )

@admin_bp.route("/admin/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    student = db.fetchone("SELECT * FROM users WHERE id=%s AND role='student'", (student_id,))
    if not student:
        flash("Student not found.", "error")
        db.close()
        return redirect(url_for("admin.students"))
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        if not fullname or not email or not username:
            flash("All fields are required.", "error")
            db.close()
            return redirect(url_for("admin.edit_student", student_id=student_id))
        existing_email = db.fetchone("SELECT id FROM users WHERE email=%s AND id != %s", (email, student_id))
        if existing_email:
            flash("Email is already in use.", "error")
            db.close()
            return redirect(url_for("admin.edit_student", student_id=student_id))
        existing_username = db.fetchone("SELECT id FROM users WHERE username=%s AND id != %s", (username, student_id))
        if existing_username:
            flash("Username is already taken.", "error")
            db.close()
            return redirect(url_for("admin.edit_student", student_id=student_id))
        db.execute("UPDATE users SET fullname=%s, email=%s, username=%s WHERE id=%s", (fullname, email, username, student_id))
        db.close()
        flash(f"Student '{username}' updated successfully.", "success")
        return redirect(url_for("admin.students"))
    db.close()
    return render_template(
        "admin/edit_student.html",
        username=session["username"],
        role=session["role"],
        student=student,
    )

@admin_bp.route("/admin/students/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    student = db.fetchone("SELECT * FROM users WHERE id=%s AND role='student'", (student_id,))
    if not student:
        flash("Student not found.", "error")
        db.close()
        return redirect(url_for("admin.students"))
    db.execute("DELETE FROM enrollments WHERE student_id=%s", (student_id,))
    db.execute("DELETE FROM attendance WHERE student_id=%s", (student_id,))
    db.execute("DELETE FROM marks WHERE student_id=%s", (student_id,))
    db.execute("DELETE FROM fee_records WHERE student_id=%s", (student_id,))
    db.execute("DELETE FROM users WHERE id=%s", (student_id,))
    db.close()
    flash("Student and all related records deleted.", "success")
    return redirect(url_for("admin.students"))

@admin_bp.route("/admin/teachers")
def teachers():
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    teachers = db.fetch("SELECT * FROM users WHERE role='teacher'")
    db.close()
    return render_template(
        "admin/teachers.html",
        username=session["username"],
        role=session["role"],
        teachers=teachers,
    )

@admin_bp.route("/admin/teachers/edit/<int:teacher_id>", methods=["GET", "POST"])
def edit_teacher(teacher_id):
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    teacher = db.fetchone("SELECT * FROM users WHERE id=%s AND role='teacher'", (teacher_id,))
    if not teacher:
        flash("Teacher not found.", "error")
        db.close()
        return redirect(url_for("admin.teachers"))
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        if not fullname or not email or not username:
            flash("All fields are required.", "error")
            db.close()
            return redirect(url_for("admin.edit_teacher", teacher_id=teacher_id))
        existing_email = db.fetchone("SELECT id FROM users WHERE email=%s AND id != %s", (email, teacher_id))
        if existing_email:
            flash("Email is already in use.", "error")
            db.close()
            return redirect(url_for("admin.edit_teacher", teacher_id=teacher_id))
        existing_username = db.fetchone("SELECT id FROM users WHERE username=%s AND id != %s", (username, teacher_id))
        if existing_username:
            flash("Username is already taken.", "error")
            db.close()
            return redirect(url_for("admin.edit_teacher", teacher_id=teacher_id))
        db.execute("UPDATE users SET fullname=%s, email=%s, username=%s WHERE id=%s", (fullname, email, username, teacher_id))
        db.close()
        flash(f"Teacher '{username}' updated successfully.", "success")
        return redirect(url_for("admin.teachers"))
    db.close()
    return render_template(
        "admin/edit_teacher.html",
        username=session["username"],
        role=session["role"],
        teacher=teacher,
    )

@admin_bp.route("/admin/teachers/delete/<int:teacher_id>", methods=["POST"])
def delete_teacher(teacher_id):
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    teacher = db.fetchone("SELECT * FROM users WHERE id=%s AND role='teacher'", (teacher_id,))
    if not teacher:
        flash("Teacher not found.", "error")
        db.close()
        return redirect(url_for("admin.teachers"))
    db.execute("UPDATE courses SET teacher_id=NULL WHERE teacher_id=%s", (teacher_id,))
    db.execute("DELETE FROM users WHERE id=%s", (teacher_id,))
    db.close()
    flash("Teacher deleted successfully.", "success")
    return redirect(url_for("admin.teachers"))

# ============================================
# ADMIN - COURSE MANAGEMENT
# ============================================

@admin_bp.route("/admin/courses")
def courses():
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    courses = db.fetch("""
        SELECT c.*, u.fullname as teacher_name,
               COUNT(DISTINCT e.id) as enrolled
        FROM courses c
        LEFT JOIN users u ON c.teacher_id = u.id
        LEFT JOIN enrollments e ON c.id = e.course_id
        GROUP BY c.id
    """)
    db.close()
    return render_template(
        "admin/courses.html",
        username=session["username"],
        role=session["role"],
        courses=courses,
    )

@admin_bp.route("/admin/courses/add", methods=["GET", "POST"])
def add_course():
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    teachers = db.fetch("SELECT id, fullname FROM users WHERE role='teacher'")
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        teacher_id = request.form.get("teacher_id") or None
        capacity = request.form.get("capacity") or 50
        existing = db.fetchone("SELECT id FROM courses WHERE name=%s", (name,))
        if existing:
            flash("A course with this name already exists.", "error")
            db.close()
            return redirect(url_for("admin.add_course"))
        db.execute(
            "INSERT INTO courses (name, description, teacher_id, capacity) VALUES (%s, %s, %s, %s)",
            (name, description, teacher_id, capacity)
        )
        db.close()
        flash("Course added successfully.", "success")
        return redirect(url_for("admin.courses"))
    db.close()
    return render_template(
        "admin/add_course.html",
        username=session["username"],
        role=session["role"],
        teachers=teachers,
    )

@admin_bp.route("/admin/courses/edit/<int:course_id>", methods=["GET", "POST"])
def edit_course(course_id):
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    course = db.fetchone("SELECT * FROM courses WHERE id=%s", (course_id,))
    teachers = db.fetch("SELECT id, fullname FROM users WHERE role='teacher'")
    if not course:
        flash("Course not found.", "error")
        db.close()
        return redirect(url_for("admin.courses"))
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        teacher_id = request.form.get("teacher_id") or None
        capacity = request.form.get("capacity") or 50
        existing = db.fetchone("SELECT id FROM courses WHERE name=%s AND id != %s", (name, course_id))
        if existing:
            flash("Another course with this name already exists.", "error")
            db.close()
            return redirect(url_for("admin.edit_course", course_id=course_id))
        db.execute(
            "UPDATE courses SET name=%s, description=%s, teacher_id=%s, capacity=%s WHERE id=%s",
            (name, description, teacher_id, capacity, course_id)
        )
        db.close()
        flash("Course updated successfully.", "success")
        return redirect(url_for("admin.courses"))
    db.close()
    return render_template(
        "admin/edit_course.html",
        username=session["username"],
        role=session["role"],
        course=course,
        teachers=teachers,
    )

@admin_bp.route("/admin/courses/delete/<int:course_id>", methods=["POST"])
def delete_course(course_id):
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    enrolled = db.fetchone("SELECT COUNT(*) as count FROM enrollments WHERE course_id=%s", (course_id,))
    if enrolled["count"] > 0:
        flash("Cannot delete a course with enrolled students.", "error")
        db.close()
        return redirect(url_for("admin.courses"))
    db.execute("DELETE FROM courses WHERE id=%s", (course_id,))
    db.close()
    flash("Course deleted successfully.", "success")
    return redirect(url_for("admin.courses"))

@admin_bp.route("/admin/assign", methods=["GET", "POST"])
def assign_course():
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    students = db.fetch("SELECT id, fullname, username FROM users WHERE role='student'")
    courses = db.fetch("""
        SELECT c.id, c.name, c.capacity, COUNT(e.id) as enrolled
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        GROUP BY c.id
    """)
    if request.method == "POST":
        student_id = request.form.get("student_id")
        course_id = request.form.get("course_id")
        existing = db.fetchone("SELECT id FROM enrollments WHERE student_id=%s AND course_id=%s", (student_id, course_id))
        if existing:
            flash("Student is already enrolled.", "error")
            db.close()
            return redirect(url_for("admin.assign_course"))
        course = db.fetchone("""
            SELECT c.capacity, COUNT(e.id) as enrolled
            FROM courses c
            LEFT JOIN enrollments e ON c.id = e.course_id
            WHERE c.id = %s
            GROUP BY c.id
        """, (course_id,))
        if course and course["enrolled"] >= course["capacity"]:
            flash("Course is full.", "error")
            db.close()
            return redirect(url_for("admin.assign_course"))
        db.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
        db.close()
        flash("Student enrolled successfully.", "success")
        return redirect(url_for("admin.assign_course"))
    db.close()
    return render_template(
        "admin/assign_course.html",
        username=session["username"],
        role=session["role"],
        students=students,
        courses=courses,
    )

# ============================================
# ADMIN - ATTENDANCE
# ============================================


@admin_bp.route("/admin/attendance")
def admin_attendance():
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    courses = db.fetch("""
        SELECT c.*, u.fullname as teacher_name,
               COUNT(DISTINCT e.id) as enrolled
        FROM courses c
        LEFT JOIN users u ON c.teacher_id = u.id
        LEFT JOIN enrollments e ON c.id = e.course_id
        GROUP BY c.id
    """)
    db.close()
    return render_template(
        "admin/attendance.html",
        username=session["username"],
        role=session["role"],
        courses=courses,
    )

@admin_bp.route("/admin/attendance/course/<int:course_id>", methods=["GET", "POST"])
def admin_mark_attendance(course_id):
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    course = db.fetchone("SELECT * FROM courses WHERE id=%s", (course_id,))
    if not course:
        flash("Course not found.", "error")
        db.close()
        return redirect(url_for("admin.admin_attendance"))
    
    if request.method == "POST":
        attendance_model = AttendanceModel()
        students = db.fetch("SELECT u.id FROM users u JOIN enrollments e ON u.id=e.student_id WHERE e.course_id=%s", (course_id,))
        marked_count = 0
        for student in students:
            status = request.form.get(f"status_{student['id']}")
            if status:
                success, message = attendance_model.mark_attendance(
                    student['id'], course_id, status, session["user_id"], ""
                )
                if success:
                    marked_count += 1
        attendance_model.close()
        flash(f"Attendance marked for {marked_count} students.", "success")
        db.close()
        return redirect(url_for("admin.admin_mark_attendance", course_id=course_id))
    
    students = db.fetch("""
        SELECT u.id, u.fullname, u.email,
               (SELECT status FROM attendance 
                WHERE student_id=u.id AND course_id=%s AND date=CURDATE()) as today_status
        FROM users u
        JOIN enrollments e ON u.id = e.student_id
        WHERE e.course_id=%s AND u.role='student'
        ORDER BY u.fullname
    """, (course_id, course_id))
    db.close()
    return render_template(
        "admin/mark_attendance.html",
        username=session["username"],
        role=session["role"],
        course=course,
        students=students,
        today=date.today()
    )

# ============================================
# ADMIN - MARKS
# ============================================

@admin_bp.route("/admin/marks")
def admin_marks():
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    courses = db.fetch("""
        SELECT c.*, u.fullname as teacher_name
        FROM courses c
        LEFT JOIN users u ON c.teacher_id = u.id
        ORDER BY c.name
    """)
    db.close()
    return render_template(
        "admin/marks.html",
        username=session["username"],
        role=session["role"],
        courses=courses
    )

@admin_bp.route("/admin/marks/course/<int:course_id>", methods=["GET", "POST"])
def admin_manage_marks(course_id):
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    course = db.fetchone("SELECT * FROM courses WHERE id=%s", (course_id,))
    if not course:
        flash("Course not found.", "error")
        db.close()
        return redirect(url_for("admin.admin_marks"))
    if request.method == "POST":
        marks_model = MarksModel()
        title = request.form.get("title")
        total = float(request.form.get("total", 100))
        exam_type = request.form.get("exam_type", "assignment")
        students = db.fetch("SELECT u.id FROM users u JOIN enrollments e ON u.id=e.student_id WHERE e.course_id=%s", (course_id,))
        marked_count = 0
        for student in students:
            score = request.form.get(f"score_{student['id']}")
            if score:
                success, message = marks_model.add_marks(
                    student['id'], course_id, title, float(score), total, exam_type
                )
                if success:
                    marked_count += 1
        marks_model.close()
        flash(f"Marks added for {marked_count} students.", "success")
        db.close()
        return redirect(url_for("admin.admin_manage_marks", course_id=course_id))
    students = db.fetch("""
        SELECT u.id, u.fullname, u.email,
               (SELECT ROUND(AVG(score / total * 100), 1) 
                FROM marks m 
                WHERE m.student_id = u.id AND m.course_id = %s) as avg_percentage
        FROM users u
        JOIN enrollments e ON u.id = e.student_id
        WHERE e.course_id=%s AND u.role='student'
        ORDER BY u.fullname
    """, (course_id, course_id))
    existing_marks = db.fetch("""
        SELECT m.*, u.fullname as student_name
        FROM marks m
        JOIN users u ON m.student_id = u.id
        WHERE m.course_id = %s
        ORDER BY m.created_at DESC
    """, (course_id,))
    db.close()
    return render_template(
        "admin/manage_marks.html",
        username=session["username"],
        role=session["role"],
        course=course,
        students=students,
        existing_marks=existing_marks
    )

# ============================================
# ADMIN - FEES
# ============================================

@admin_bp.route("/admin/fees")
def admin_fees():
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    fees = db.fetch("""
        SELECT fr.*, u.fullname as student_name
        FROM fee_records fr
        JOIN users u ON fr.student_id = u.id
        ORDER BY fr.due_date DESC
    """)
    students = db.fetch("SELECT id, fullname FROM users WHERE role='student' ORDER BY fullname")
    db.close()
    return render_template(
        "admin/fees.html",
        username=session["username"],
        role=session["role"],
        fees=fees,
        students=students
    )

@admin_bp.route("/admin/fees/add", methods=["POST"])
def admin_add_fee():
    if admin_required():
        return redirect(url_for("auth.login"))
    student_id = request.form.get("student_id")
    amount = request.form.get("amount")
    description = request.form.get("description")
    due_date = request.form.get("due_date")
    fee_model = FeeModel()
    success, message = fee_model.add_fee_record(student_id, float(amount), description, due_date)
    fee_model.close()
    flash(message, "success" if success else "error")
    return redirect(url_for("admin.admin_fees"))

@admin_bp.route("/admin/fees/update/<int:fee_id>", methods=["POST"])
def admin_update_fee(fee_id):
    if admin_required():
        return redirect(url_for("auth.login"))
    status = request.form.get("status")
    db = Database()
    db.execute("UPDATE fee_records SET status=%s WHERE id=%s", (status, fee_id))
    db.close()
    flash("Fee status updated.", "success")
    return redirect(url_for("admin.admin_fees"))

@admin_bp.route("/admin/fees/delete/<int:fee_id>", methods=["POST"])
def admin_delete_fee(fee_id):
    if admin_required():
        return redirect(url_for("auth.login"))
    db = Database()
    db.execute("DELETE FROM fee_records WHERE id=%s", (fee_id,))
    db.close()
    flash("Fee deleted.", "success")
    return redirect(url_for("admin.admin_fees"))

# ============================================
# ADMIN - REPORTS (Complete with all calculations)
# ============================================

@admin_bp.route("/admin/reports")
def admin_reports():
    if admin_required():
        return redirect(url_for("auth.login"))
    
    db = Database()
    
    # Overall Statistics
    stats = db.fetchone("""
        SELECT 
            (SELECT COUNT(*) FROM users WHERE role='student') as total_students,
            (SELECT COUNT(*) FROM users WHERE role='teacher') as total_teachers,
            (SELECT COUNT(*) FROM courses) as total_courses,
            (SELECT COUNT(*) FROM enrollments) as total_enrollments
    """)
    
    # Attendance Statistics
    attendance_stats = db.fetchone("""
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_count,
            ROUND(AVG(CASE WHEN status = 'present' THEN 1 ELSE 0 END) * 100, 2) as overall_percentage
        FROM attendance
    """)
    
    # Course-wise Performance with Completion Tracking
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
        GROUP BY c.id, c.name
        ORDER BY completion_rate DESC
    """)
    
    # Student-wise Performance Report
    student_performance = db.fetch("""
        SELECT 
            u.id,
            u.fullname,
            u.email,
            COUNT(DISTINCT e.course_id) as enrolled_courses,
            ROUND(AVG(m.score / m.total * 100), 1) as avg_marks,
            ROUND(AVG(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) * 100, 2) as attendance_percentage,
            (SELECT COUNT(DISTINCT t.id) 
             FROM tasks t 
             JOIN enrollments e2 ON t.course_id = e2.course_id 
             WHERE e2.student_id = u.id) as total_tasks,
            (SELECT COUNT(DISTINCT ts.id) 
             FROM task_submissions ts 
             WHERE ts.student_id = u.id) as completed_tasks,
            ROUND(
                (SELECT COUNT(DISTINCT ts.id) 
                 FROM task_submissions ts 
                 WHERE ts.student_id = u.id) / 
                NULLIF((SELECT COUNT(DISTINCT t.id) 
                        FROM tasks t 
                        JOIN enrollments e2 ON t.course_id = e2.course_id 
                        WHERE e2.student_id = u.id), 0) * 100, 2
            ) as task_completion_rate,
            (SELECT grade FROM grade_scale 
             WHERE ROUND(AVG(m.score / m.total * 100), 1) BETWEEN min_score AND max_score 
             LIMIT 1) as grade
        FROM users u
        LEFT JOIN enrollments e ON u.id = e.student_id
        LEFT JOIN marks m ON u.id = m.student_id
        LEFT JOIN attendance a ON u.id = a.student_id
        WHERE u.role = 'student'
        GROUP BY u.id, u.fullname, u.email
        ORDER BY avg_marks DESC
    """)
    
    # Fee Summary
    fee_summary = db.fetchone("""
        SELECT 
            SUM(amount) as total_fees,
            SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as collected_fees,
            SUM(CASE WHEN status IN ('unpaid', 'partial') THEN amount ELSE 0 END) as pending_fees,
            COUNT(CASE WHEN status = 'paid' THEN 1 END) as paid_count,
            COUNT(CASE WHEN status IN ('unpaid', 'partial') THEN 1 END) as pending_count
        FROM fee_records
    """)
    
    db.close()
    
    return render_template(
        "admin/reports.html",
        username=session["username"],
        role=session["role"],
        stats=stats,
        attendance_stats=attendance_stats,
        course_performance=course_performance,
        student_performance=student_performance,
        fee_summary=fee_summary
    )
