from flask import Blueprint

profile_bp = Blueprint(
    "profile",
    __name__,
    url_prefix="/profile"
)

@profile_bp.route("/")
def profile():
    return render_template(
        "profile/view.html"
    )