from flask import render_template, request, redirect, url_for, session, flash
from app.models.user_model import User

class AuthController:

    # ─────────────────────────────────────────────
    # LOGIN
    # ─────────────────────────────────────────────

    def login(self):
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            
            print(f"Login attempt: username={username}")  # Debug
            
            # Check if user exists
            user = User.login(username)
            
            if user:
                print(f"User found: {user.username}, role={user.role}")  # Debug
                password_valid = user.check_password(password)
                print(f"Password valid: {password_valid}")  # Debug
                
                if password_valid:
                    session["user_id"] = user.id
                    session["username"] = user.username
                    session["role"] = user.role
                    
                    print(f"Session set: {session}")  # Debug
                    
                    if user.role == "admin":
                        return redirect(url_for("admin.dashboard"))
                    elif user.role == "teacher":
                        return redirect(url_for("teacher.dashboard"))
                    else:
                        return redirect(url_for("student.dashboard"))
                else:
                    flash("Invalid username or password.", "error")
                    print("Invalid password")  # Debug
            else:
                flash("Invalid username or password.", "error")
                print(f"User not found: {username}")  # Debug
            
            return render_template("login.html")

        return render_template("login.html")

    # ─────────────────────────────────────────────
    # REGISTER
    # ─────────────────────────────────────────────

    def register(self):
        if "user_id" in session:
            role = session.get("role")
            if role == "admin":
                return redirect(url_for("admin.dashboard"))
            elif role == "teacher":
                return redirect(url_for("teacher.dashboard"))
            else:
                return redirect(url_for("student.dashboard"))

        if request.method == "POST":
            fullname = request.form.get("fullname", "").strip()
            email = request.form.get("email", "").strip()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            role = request.form.get("role", "student")

            if not all([fullname, email, username, password, confirm_password]):
                flash("All fields are required.", "error")
                return render_template("register.html")

            if password != confirm_password:
                flash("Passwords do not match.", "error")
                return render_template("register.html")

            if len(password) < 8:
                flash("Password must be at least 8 characters.", "error")
                return render_template("register.html")

            if role not in ("student", "teacher"):
                role = "student"

            user = User(
                name=fullname,
                email=email,
                username=username,
                password=password,
                role=role,
            )

            if user.email_exists():
                flash("An account with this email already exists.", "error")
                return render_template("register.html")

            if user.username_exists():
                flash("Username is already taken.", "error")
                return render_template("register.html")

            user.save()
            flash("Account created! You can now log in.", "success")
            return redirect(url_for("auth.login"))

        return render_template("register.html")

    # ─────────────────────────────────────────────
    # HOME
    # ─────────────────────────────────────────────

    def home(self):
        """Redirect to the appropriate dashboard based on user role"""
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        
        role = session.get("role")
        
        if role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif role == "teacher":
            return redirect(url_for("teacher.dashboard"))
        elif role == "student":
            return redirect(url_for("student.dashboard"))
        else:
            return redirect(url_for("auth.login"))

    # ─────────────────────────────────────────────
    # LOGOUT
    # ─────────────────────────────────────────────

    def logout(self):
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("auth.login"))