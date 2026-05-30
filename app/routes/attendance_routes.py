from flask import Blueprint

attendance_bp = Blueprint(
    "attendance",
    __name__,
    url_prefix="/attendance"
)

@attendance_bp.route("/")
def attendance():
    return render_template(
        "admin/attendance.html"
    )