from flask import Blueprint

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)

@admin_bp.route("/dashboard")
def dashboard():
    return render_template(
        "admin/dashboard.html"
    )

@admin_bp.route("/admin/students")
def students():
    return render_template(
        "admin/students.html"
    )

@admin_bp.route("/assign-course")
def assign_course():
    return render_template(
        "admin/assign_course.html"