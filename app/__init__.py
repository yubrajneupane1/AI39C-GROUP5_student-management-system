from flask import Flask
<<<<<<< HEAD

def create_app():
    app = Flask(__name__)
=======
from app.routes.auth import AuthRoutes
from app.routes.student_routes import student_bp
from app.routes.admin_routes import admin_bp
from app.routes.teacher_routes import teacher_bp
from app.routes.profile_routes import profile_bp
from app.routes.attendance_routes import attendance_bp
from app.routes.notification_routes import notification_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = "secretkey"
    
    auth_routes = AuthRoutes()
    app.register_blueprint(auth_routes.register())
    
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(notification_bp)
    
>>>>>>> 9faed573f76eed3936674153176b8d09a5b1e756
    return app