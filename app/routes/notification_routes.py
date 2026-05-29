from flask import Blueprint

notification_bp = Blueprint(
    "notification",
    __name__,
    url_prefix="/notifications"
)

@notification_bp.route("/")
def notifications():
    return render_template(
        "notifications.html"
    )

@notification_bp.route("/preferences")
def preferences():
    return render_template(
        "notification_preferences.html"
    )