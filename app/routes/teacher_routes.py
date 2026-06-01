from flask import Blueprint

teacher_bp = Blueprint(
    "teacher",
    __name__,
    url_prefix="/teacher"
)

@teacher_bp.route("/dashboard")
def dashboard():
    return render_template(
        "teacher/dashboard.html"
    )

@teacher_bp.route("/students")
def students():
    return render_template(
        "teacher/students.html"
    )

@teacher_bp.route("/teacher/courses")
def courses():
    return render_template(
        "teacher/courses.html"
    )