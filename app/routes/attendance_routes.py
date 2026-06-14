from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models.attendance_model import AttendanceModel
from app.models.database import Database
from datetime import date

attendance_bp = Blueprint("attendance", __name__)

def attendance_allowed():
    """Check if user has permission to access attendance"""
    if "role" not in session:
        return False
    return session["role"] in ["admin", "teacher"]

@attendance_bp.route("/teacher/attendance")
def teacher_attendance():
    """Main attendance page for teachers and admins"""
    if not attendance_allowed():
        flash("You don't have permission to access attendance.", "error")
        return redirect(url_for("auth.login"))
    
    db = Database()
    user_id = session["user_id"]
    role = session["role"]
    
    if role == "admin":
        # Admin sees all courses
        courses = db.fetch("""
            SELECT c.*, u.fullname as teacher_name,
                   COUNT(DISTINCT e.id) as enrolled
            FROM courses c
            LEFT JOIN users u ON c.teacher_id = u.id
            LEFT JOIN enrollments e ON c.id = e.course_id
            GROUP BY c.id
            ORDER BY c.name
        """)
    else:
        # Teacher sees only their courses
        courses = db.fetch("""
            SELECT c.*, COUNT(DISTINCT e.id) as enrolled
            FROM courses c
            LEFT JOIN enrollments e ON c.id = e.course_id
            WHERE c.teacher_id = %s
            GROUP BY c.id
            ORDER BY c.name
        """, (user_id,))
    
    db.close()
    
    return render_template(
        "teacher/attendance.html",
        username=session["username"],
        role=role,
        courses=courses
    )

@attendance_bp.route("/teacher/course/<int:course_id>/attendance", methods=["GET", "POST"])
def mark_attendance(course_id):
    """Mark attendance for a specific course"""
    if not attendance_allowed():
        flash("You don't have permission to mark attendance.", "error")
        return redirect(url_for("auth.login"))
    
    db = Database()
    user_id = session["user_id"]
    role = session["role"]
    
    # Verify teacher owns this course or user is admin
    if role == "teacher":
        course = db.fetchone(
            "SELECT * FROM courses WHERE id=%s AND teacher_id=%s",
            (course_id, user_id)
        )
    else:
        course = db.fetchone("SELECT * FROM courses WHERE id=%s", (course_id,))
    
    if not course:
        flash("Course not found or you don't have permission.", "error")
        db.close()
        return redirect(url_for("attendance.teacher_attendance"))
    
    if request.method == "POST":
        attendance_model = AttendanceModel()
        
        # Get all students in this course
        students = db.fetch(
            "SELECT u.id FROM users u JOIN enrollments e ON u.id=e.student_id WHERE e.course_id=%s",
            (course_id,)
        )
        
        marked_count = 0
        for student in students:
            status = request.form.get(f"status_{student['id']}")
            remarks = request.form.get(f"remarks_{student['id']}", "")
            
            if status:
                success, message = attendance_model.mark_attendance(
                    student['id'], course_id, status, user_id, remarks
                )
                if success:
                    marked_count += 1
        
        attendance_model.close()
        flash(f"Attendance marked for {marked_count} students.", "success")
        db.close()
        return redirect(url_for("attendance.mark_attendance", course_id=course_id))
    
    # Get students enrolled in this course with their today's status
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
        "teacher/mark_attendance.html",
        username=session["username"],
        role=role,
        course=course,
        students=students,
        today=date.today()
    )

@attendance_bp.route("/teacher/course/<int:course_id>/attendance/report")
def attendance_report(course_id):
    """View attendance report for a course"""
    if not attendance_allowed():
        flash("You don't have permission to view attendance reports.", "error")
        return redirect(url_for("auth.login"))
    
    db = Database()
    user_id = session["user_id"]
    role = session["role"]
    
    if role == "teacher":
        course = db.fetchone(
            "SELECT * FROM courses WHERE id=%s AND teacher_id=%s",
            (course_id, user_id)
        )
    else:
        course = db.fetchone("SELECT * FROM courses WHERE id=%s", (course_id,))
    
    if not course:
        flash("Course not found.", "error")
        db.close()
        return redirect(url_for("attendance.teacher_attendance"))
    
    attendance_model = AttendanceModel()
    summary = attendance_model.get_course_attendance_summary(course_id)
    attendance_model.close()
    db.close()
    
    return render_template(
        "teacher/attendance_report.html",
        username=session["username"],
        role=role,
        course=course,
        summary=summary
    )