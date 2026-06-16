from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models.database import Database
from werkzeug.security import generate_password_hash, check_password_hash

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile")
def view_profile():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    db = Database()
    user = db.fetchone("SELECT * FROM users WHERE id=%s", (session["user_id"],))
    db.close()
    
    return render_template(
        "profile/view.html",
        username=session["username"],
        role=session["role"],
        user=user
    )

@profile_bp.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    db = Database()
    user = db.fetchone("SELECT * FROM users WHERE id=%s", (session["user_id"],))
    
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not fullname:
            flash("Full name is required.", "error")
            db.close()
            return redirect(url_for("profile.edit_profile"))
        
        if not email or "@" not in email or "." not in email:
            flash("Please enter a valid email address.", "error")
            db.close()
            return redirect(url_for("profile.edit_profile"))
        
        existing = db.fetchone(
            "SELECT id FROM users WHERE email=%s AND id!=%s",
            (email, session["user_id"])
        )
        if existing:
            flash("This email is already in use.", "error")
            db.close()
            return redirect(url_for("profile.edit_profile"))
        
        db.execute("""
            UPDATE users 
            SET fullname=%s, email=%s, phone=%s, address=%s, updated_at=NOW()
            WHERE id=%s
        """, (fullname, email, phone, address, session["user_id"]))
        
        if current_password and new_password:
            if not check_password_hash(user["password"], current_password):
                flash("Current password is incorrect.", "error")
                db.close()
                return redirect(url_for("profile.edit_profile"))
            
            if len(new_password) < 8:
                flash("New password must be at least 8 characters.", "error")
                db.close()
                return redirect(url_for("profile.edit_profile"))
            
            if new_password != confirm_password:
                flash("New passwords do not match.", "error")
                db.close()
                return redirect(url_for("profile.edit_profile"))
            
            hashed_password = generate_password_hash(new_password)
            db.execute(
                "UPDATE users SET password=%s WHERE id=%s",
                (hashed_password, session["user_id"])
            )
            flash("Password updated successfully!", "success")
        
        db.close()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile.view_profile"))
    
    db.close()
    
    return render_template(
        "profile/edit.html",
        username=session["username"],
        role=session["role"],
        user=user
    )