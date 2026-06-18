"""
Authentication decorators and utilities for route protection.
"""

from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """
    Decorator to restrict access to logged-in users only.
    
    Usage:
        @app.route("/dashboard")
        @login_required
        def dashboard():
            return "Dashboard"
    
    If user is not logged in:
        - Flashes warning message
        - Redirects to login page
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """
    Decorator to restrict access to admin users only.
    
    Usage:
        @app.route("/admin/dashboard")
        @login_required
        @admin_required
        def admin_dashboard():
            return "Admin Dashboard"
    
    If user is not admin:
        - Flashes danger message
        - Redirects to logout
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))
        
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("auth.logout"))
        
        return f(*args, **kwargs)
    return decorated


def teacher_required(f):
    """
    Decorator to restrict access to teachers only.
    
    Usage:
        @app.route("/teacher/dashboard")
        @login_required
        @teacher_required
        def teacher_dashboard():
            return "Teacher Dashboard"
    
    If user is not teacher or admin:
        - Flashes danger message
        - Redirects to logout
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))
        
        if session.get("role") not in ["admin", "teacher"]:
            flash("Teacher access required.", "danger")
            return redirect(url_for("auth.logout"))
        
        return f(*args, **kwargs)
    return decorated


def student_required(f):
    """
    Decorator to restrict access to students only.
    
    Usage:
        @app.route("/student/dashboard")
        @login_required
        @student_required
        def student_dashboard():
            return "Student Dashboard"
    
    If user is not student or admin:
        - Flashes danger message
        - Redirects to logout
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))
        
        if session.get("role") not in ["admin", "student"]:
            flash("Student access required.", "danger")
            return redirect(url_for("auth.logout"))
        
        return f(*args, **kwargs)
    return decorated


def role_required(allowed_roles):
    """
    Generic decorator to restrict access to specific roles.
    
    Usage:
        @app.route("/staff/dashboard")
        @login_required
        @role_required(['admin', 'teacher'])
        def staff_dashboard():
            return "Staff Dashboard"
    
    Args:
        allowed_roles: List of roles that are allowed to access the route
    
    If user's role is not in allowed_roles:
        - Flashes danger message
        - Redirects to logout
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                flash("Please login first.", "warning")
                return redirect(url_for("auth.login"))
            
            user_role = session.get("role")
            if user_role not in allowed_roles:
                flash("You don't have permission to access this page.", "danger")
                return redirect(url_for("auth.logout"))
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def logout_required(f):
    """
    Decorator to restrict access to logged-out users only.
    Used for login and register pages.
    
    Usage:
        @app.route("/login")
        @logout_required
        def login():
            return "Login Page"
    
    If user is already logged in:
        - Redirects to their respective dashboard
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" in session:
            role = session.get("role")
            if role == "admin":
                return redirect(url_for("admin.dashboard"))
            elif role == "teacher":
                return redirect(url_for("teacher.dashboard"))
            else:
                return redirect(url_for("student.dashboard"))
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    """
    Helper function to get the current logged-in user.
    
    Returns:
        dict: User data if logged in, None otherwise
    """
    from app.models.user_model import User
    
    if "user_id" not in session:
        return None
    
    return User.find_by_id(session["user_id"])