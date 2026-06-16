# complete_setup_all.py - Complete Database Setup
import pymysql
import config
from werkzeug.security import generate_password_hash
import os
import sys

def complete_setup_all():
    print("="*70)
    print("🚀 ACADLYTICS COMPLETE SETUP")
    print("="*70)
    print("")
    
    # Check MySQL connection
    print("📌 Step 1: Checking database connection...")
    try:
        connection = pymysql.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Database connected successfully!")
        cursor = connection.cursor()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nPlease check:")
        print("1. MySQL is running")
        print("2. Database credentials in config.py are correct")
        print("3. Database 'acadlytics' exists")
        print("\nCreate database with:")
        print("  CREATE DATABASE acadlytics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        return
    
    print("\n📌 Step 2: Creating tables...")
    
    try:
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fullname VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('admin', 'teacher', 'student') DEFAULT 'student',
                phone VARCHAR(20),
                address TEXT,
                profile_pic VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        print("✓ Created users table")
        
        # Create students table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                student_id VARCHAR(20) UNIQUE NOT NULL,
                date_of_birth DATE,
                guardian_name VARCHAR(100),
                guardian_phone VARCHAR(20),
                guardian_email VARCHAR(100),
                admission_date DATE,
                class VARCHAR(20),
                section VARCHAR(10),
                roll_number VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_student_id (student_id),
                INDEX idx_user_id (user_id)
            )
        """)
        print("✓ Created students table")
        
        # Create courses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                teacher_id INT,
                capacity INT DEFAULT 50,
                code VARCHAR(20) UNIQUE,
                credits INT DEFAULT 3,
                department VARCHAR(50),
                semester VARCHAR(20),
                academic_year VARCHAR(20),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_teacher (teacher_id),
                INDEX idx_code (code),
                INDEX idx_active (is_active)
            )
        """)
        print("✓ Created courses table")
        
        # Create enrollments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                course_id INT NOT NULL,
                enrollment_date DATE,
                status ENUM('active', 'completed', 'dropped') DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                UNIQUE KEY unique_enrollment (student_id, course_id),
                INDEX idx_student (student_id),
                INDEX idx_course (course_id),
                INDEX idx_status (status)
            )
        """)
        print("✓ Created enrollments table")
        
        # Create attendance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                course_id INT NOT NULL,
                date DATE NOT NULL,
                status ENUM('present', 'absent', 'late', 'excused') NOT NULL,
                marked_by INT,
                marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (marked_by) REFERENCES users(id) ON DELETE SET NULL,
                UNIQUE KEY unique_attendance (student_id, course_id, date),
                INDEX idx_student (student_id),
                INDEX idx_course (course_id),
                INDEX idx_date (date),
                INDEX idx_status (status)
            )
        """)
        print("✓ Created attendance table")
        
        # Create marks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS marks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                course_id INT NOT NULL,
                title VARCHAR(100) NOT NULL,
                score DECIMAL(5,2) NOT NULL,
                total DECIMAL(5,2) NOT NULL,
                weightage DECIMAL(5,2) DEFAULT 100,
                exam_type ENUM('quiz', 'assignment', 'midterm', 'final', 'project', 'other') DEFAULT 'assignment',
                date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                INDEX idx_student (student_id),
                INDEX idx_course (course_id),
                INDEX idx_type (exam_type)
            )
        """)
        print("✓ Created marks table")
        
        # Create fee_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fee_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                description VARCHAR(200) NOT NULL,
                due_date DATE NOT NULL,
                status ENUM('paid', 'unpaid', 'partial', 'overdue') DEFAULT 'unpaid',
                late_fee DECIMAL(10,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_student (student_id),
                INDEX idx_status (status),
                INDEX idx_due_date (due_date)
            )
        """)
        print("✓ Created fee_records table")
        
        # Create grade_scale table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grade_scale (
                id INT AUTO_INCREMENT PRIMARY KEY,
                grade VARCHAR(5) NOT NULL UNIQUE,
                min_score DECIMAL(5,2) NOT NULL,
                max_score DECIMAL(5,2) NOT NULL,
                gpa DECIMAL(3,2) NOT NULL,
                description VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_grade (grade)
            )
        """)
        print("✓ Created grade_scale table")
        
        # Insert grade scale data
        cursor.execute("""
            INSERT IGNORE INTO grade_scale (grade, min_score, max_score, gpa, description) VALUES
            ('A+', 90, 100, 4.00, 'Excellent'),
            ('A', 85, 89, 3.70, 'Very Good'),
            ('A-', 80, 84, 3.30, 'Good'),
            ('B+', 77, 79, 3.00, 'Above Average'),
            ('B', 73, 76, 2.70, 'Average'),
            ('B-', 70, 72, 2.30, 'Below Average'),
            ('C+', 67, 69, 2.00, 'Satisfactory'),
            ('C', 63, 66, 1.70, 'Passing'),
            ('C-', 60, 62, 1.30, 'Marginal Pass'),
            ('D', 50, 59, 1.00, 'Poor'),
            ('F', 0, 49, 0.00, 'Fail')
        """)
        print("✓ Inserted grade scale data")
        
        # Create notification_preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_preferences (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL UNIQUE,
                attendance_alerts BOOLEAN DEFAULT TRUE,
                fee_alerts BOOLEAN DEFAULT TRUE,
                system_alerts BOOLEAN DEFAULT TRUE,
                grade_alerts BOOLEAN DEFAULT TRUE,
                task_alerts BOOLEAN DEFAULT TRUE,
                email_notifications BOOLEAN DEFAULT FALSE,
                attendance_threshold INT DEFAULT 75,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user (user_id)
            )
        """)
        print("✓ Created notification_preferences table")
        
        # Create notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                type ENUM('attendance', 'fee', 'system', 'grade', 'task') NOT NULL,
                title VARCHAR(100) NOT NULL,
                message TEXT NOT NULL,
                link VARCHAR(255),
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user (user_id),
                INDEX idx_read (is_read),
                INDEX idx_type (type),
                INDEX idx_created (created_at)
            )
        """)
        print("✓ Created notifications table")
        
        # Create weeks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weeks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                course_id INT NOT NULL,
                week_number INT NOT NULL,
                title VARCHAR(200) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                UNIQUE KEY unique_week (course_id, week_number),
                INDEX idx_course (course_id)
            )
        """)
        print("✓ Created weeks table")
        
        # Create lessons table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id INT AUTO_INCREMENT PRIMARY KEY,
                week_id INT NOT NULL,
                lesson_number INT NOT NULL,
                title VARCHAR(200) NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (week_id) REFERENCES weeks(id) ON DELETE CASCADE,
                UNIQUE KEY unique_lesson (week_id, lesson_number),
                INDEX idx_week (week_id)
            )
        """)
        print("✓ Created lessons table")
        
        # Create study_materials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_materials (
                id INT AUTO_INCREMENT PRIMARY KEY,
                course_id INT NOT NULL,
                week_id INT,
                teacher_id INT NOT NULL,
                material_type ENUM('manual', 'file', 'link', 'video') DEFAULT 'file',
                title VARCHAR(200) NOT NULL,
                description TEXT,
                file_url VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (week_id) REFERENCES weeks(id) ON DELETE SET NULL,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_course (course_id),
                INDEX idx_teacher (teacher_id),
                INDEX idx_type (material_type)
            )
        """)
        print("✓ Created study_materials table")
        
        # Create tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                course_id INT NOT NULL,
                week_id INT,
                teacher_id INT NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                time_limit_minutes INT,
                due_date DATETIME,
                submission_type ENUM('text', 'file', 'both') DEFAULT 'text',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (week_id) REFERENCES weeks(id) ON DELETE SET NULL,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_course (course_id),
                INDEX idx_teacher (teacher_id),
                INDEX idx_due_date (due_date)
            )
        """)
        print("✓ Created tasks table")
        
        # Create task_submissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_submissions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id INT NOT NULL,
                student_id INT NOT NULL,
                text_answer TEXT,
                file_url VARCHAR(255),
                status ENUM('submitted', 'late', 'graded') DEFAULT 'submitted',
                grade DECIMAL(5,2),
                feedback TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE KEY unique_submission (task_id, student_id),
                INDEX idx_task (task_id),
                INDEX idx_student (student_id),
                INDEX idx_status (status)
            )
        """)
        print("✓ Created task_submissions table")
        
        # Create resources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INT AUTO_INCREMENT PRIMARY KEY,
                course_id INT NOT NULL,
                teacher_id INT NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                link VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_course (course_id),
                INDEX idx_teacher (teacher_id)
            )
        """)
        print("✓ Created resources table")
        
        # Create attendance_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                attendance_id INT NOT NULL,
                action ENUM('create', 'update', 'delete') NOT NULL,
                old_status VARCHAR(20),
                new_status VARCHAR(20),
                changed_by INT NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reason TEXT,
                FOREIGN KEY (attendance_id) REFERENCES attendance(id) ON DELETE CASCADE,
                FOREIGN KEY (changed_by) REFERENCES users(id),
                INDEX idx_attendance (attendance_id)
            )
        """)
        print("✓ Created attendance_logs table")
        
        # Create attendance_alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_alerts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            course_id INT NOT NULL,
            threshold INT NOT NULL,
            current_percentage DECIMAL(5,2),

            alert_date DATE NOT NULL,

            is_sent BOOLEAN DEFAULT FALSE,
            sent_at TIMESTAMP NULL,
            alert_type ENUM('warning', 'critical') DEFAULT 'warning',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,

            INDEX idx_student (student_id),
            INDEX idx_sent (is_sent)
            )
        """)
        print("✓ Created attendance_alerts table")
        
        # Create payments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fee_record_id INT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                payment_method ENUM('cash', 'bank_transfer', 'credit_card', 'online') DEFAULT 'cash',
                reference_number VARCHAR(50) UNIQUE,
                receipt_number VARCHAR(50) UNIQUE NOT NULL,
                remarks TEXT,
                received_by INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (fee_record_id) REFERENCES fee_records(id) ON DELETE CASCADE,
                FOREIGN KEY (received_by) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_fee_record (fee_record_id),
                INDEX idx_receipt (receipt_number)
            )
        """)
        print("✓ Created payments table")
        
        # Create receipts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                payment_id INT NOT NULL,
                receipt_number VARCHAR(50) UNIQUE NOT NULL,
                receipt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pdf_path VARCHAR(255),
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE,
                INDEX idx_receipt_number (receipt_number)
            )
        """)
        print("✓ Created receipts table")
        
        # Create marks_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS marks_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                mark_id INT NOT NULL,
                old_score DECIMAL(5,2),
                new_score DECIMAL(5,2),
                changed_by INT NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reason TEXT,
                FOREIGN KEY (mark_id) REFERENCES marks(id) ON DELETE CASCADE,
                FOREIGN KEY (changed_by) REFERENCES users(id),
                INDEX idx_mark (mark_id)
            )
        """)
        print("✓ Created marks_history table")
        
        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_token (session_token),
                INDEX idx_user (user_id),
                INDEX idx_expires (expires_at)
            )
        """)
        print("✓ Created sessions table")
        
        # Create login_attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                ip_address VARCHAR(45),
                success BOOLEAN DEFAULT FALSE,
                attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_username (username),
                INDEX idx_ip (ip_address),
                INDEX idx_time (attempted_at)
            )
        """)
        print("✓ Created login_attempts table")
        
        print("\n📌 Step 3: Creating default users...")
        
        # Check if users exist
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        
        if result['count'] == 0:
            users = [
                ('Admin User', 'admin@acadlytics.com', 'admin', generate_password_hash('admin123'), 'admin'),
                ('Teacher User', 'teacher@acadlytics.com', 'teacher', generate_password_hash('teacher123'), 'teacher'),
                ('Student User', 'student@acadlytics.com', 'student', generate_password_hash('student123'), 'student')
            ]
            
            for user in users:
                cursor.execute("""
                    INSERT INTO users (fullname, email, username, password, role, is_active)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                """, user)
                print(f"✓ Created user: {user[2]}")
            
            print("\n📝 Default Login Credentials:")
            print("   Admin: admin / admin123")
            print("   Teacher: teacher / teacher123")
            print("   Student: student / student123")
        else:
            print(f"ℹ Users already exist ({result['count']} found)")
        
        # Add notification preferences for existing users
        print("\n📌 Step 4: Setting up notification preferences...")
        cursor.execute("""
            INSERT IGNORE INTO notification_preferences (user_id)
            SELECT id FROM users
        """)
        print("✓ Added notification preferences for users")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("\n" + "="*70)
        print("✅ SETUP COMPLETE!")
        print("="*70)
        print("")
        print("🚀 Run the application with:")
        print("   python run.py")
        print("")
        print("🌐 Open browser at:")
        print("   http://localhost:5000")
        print("")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure MySQL is running")
        print("2. Check database credentials in config.py")
        print("3. Make sure database 'acadlytics' exists")
        print("4. Try running as administrator")

if __name__ == "__main__":
    complete_setup_all()