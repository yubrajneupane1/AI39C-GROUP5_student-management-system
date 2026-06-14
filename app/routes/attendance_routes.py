from flask import Blueprint

attendance_bp = Blueprint(
    "attendance",
    __name__,
    url_prefix="/attendance"
)

@attendance_bp.route("/")
def attendance():
    return render_templates("admin/attendance.html")
    
@attendance_bp.route("/mark")
def mark_attendance():
    return render_templates("teacher/mark_attendance.html")

try:
    pass
except Exception:
    pass