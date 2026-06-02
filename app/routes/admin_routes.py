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