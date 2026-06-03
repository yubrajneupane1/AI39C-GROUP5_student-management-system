from flask import Blueprint
from flask import render_template
student_bp = Blueprint(
    "student",
    __name__,
    url_prefix="/student"
)
@student_bp.route("/dashboard")
def dashboard():
    return render_template(
        "student/dashboard.html"
    )
@student_bp.route("/courses")
def courses():
    return render_template(
        "student/courses.html"
    )
@student_bp.route("/student/attendance")
def attendance():
    return render_template(
        "student/attendance.html"
    )
@student_bp.route("/student/marks")
def marks():
    return render_template(
        "student/marks.html"
    )