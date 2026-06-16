# Acadlytics - Education Management System
## 📥 Quick Installation Starts From Line 53!!##
## 📌 Overview
**Acadlytics** is a complete education management system built with Flask and MySQL. It manages students, teachers, courses, attendance, marks, fees, and notifications in one place.

---

## ✨ Key Features

### 👑 Admin
- Student/Teacher/Course Management
- Enrollment & Attendance
- Marks & Grade Management
- Fee Management
- Reports & Analytics
- Custom Notifications (Send to All/Teachers/Students)

### 👨‍🏫 Teacher
- Course Content Management
- Mark Attendance
- Add/Manage Marks
- Create Tasks & Grade Submissions
- Share Resources
- View Reports

### 👨‍🎓 Student
- View Attendance & Marks
- Access Course Materials
- Submit Tasks
- Track Fees
- Manage Profile
- Receive Notifications

### 🔔 Notification System
- Admin can send custom notifications
- Send to All, Teachers, Students, or Specific User
- User preferences (enable/disable types)
- Unread count badge

---

## 🛠 Tech Stack

```yaml
Backend: Flask 3.1.0, PyMySQL 1.1.1
Security: Cryptography 44.0.0, Flask-WTF 1.2.2
Frontend: HTML5, CSS3, JavaScript, Chart.js
Database: MySQL 5.7+ / 8.0+
```

---

## 📥 Quick Installation

### Prerequisites
- Python 3.8+
- MySQL 5.7+

### Steps
```bash
# 1. Clone/Extract project
cd Acadlytics_final

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# 3. Install dependencies
pip install Flask==3.1.0 pymysql==1.1.1 cryptography==44.0.0 flask-wtf==1.2.2

# 4. Create database
mysql -u root -p
CREATE DATABASE acadlytics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

# 5. Configure config.py
# Edit config.py with your MySQL password

# 6. Run setup
python complete_setup_all.py

# 7. Run application
python run.py
```

---

## 🔐 Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Teacher | teacher | teacher123 |
| Student | student | student123 |

---

## 📁 Project Structure

```
Acadlytics_final/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # Route handlers
│   ├── templates/       # HTML templates
│   └── static/          # CSS, JS, images
├── config.py            # Configuration
├── run.py               # Entry point
├── complete_setup_all.py # Complete setup script
└── requirements.txt     # Dependencies
```
## Detailed Structure
Acadlytics_final/
│
├── run.py
├── config.py
├── database.sql
├── requirement.txt
├── README.md
├── create_users.py
├── migrate_db.py
├── migrate_existing.py
├── complete_setup_all.py
├── test_db.py
│
├── app/
│   │
│   ├── __init__.py
│   │
│   ├── controller/
│   │   ├── __init__.py
│   │   └── auth.py
│   │
│   ├── models/
│   │   ├── basemodel.py
│   │   ├── database.py
│   │   ├── user_model.py
│   │   ├── coursemodel.py
│   │   ├── lessonmodel.py
│   │   ├── weekmodel.py
│   │   ├── attendance_model.py
│   │   ├── marks_model.py
│   │   ├── fee_model.py
│   │   └── notification_model.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── admin_routes.py
│   │   ├── student_routes.py
│   │   ├── teacher_routes.py
│   │   ├── profile_routes.py
│   │   ├── attendance_routes.py
│   │   └── notification_routes.py
│   │
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   ├── images/
│   │   └── uploads/
│   │
│   └── templates/
│       │
│       ├── home.html
│       ├── about.html
│       ├── contact.html
│       ├── login.html
│       ├── register.html
│       ├── notifications.html
│       ├── notification_preferences.html
│       │
│       ├── layouts/
│       ├── partials/
│       ├── components/
│       │
│       ├── profile/
│       │
│       ├── admin/
│       │   ├── dashboard.html
│       │   ├── students.html
│       │   ├── teachers.html
│       │   ├── courses.html
│       │   ├── add_course.html
│       │   ├── edit_course.html
│       │   ├── assign_course.html
│       │   ├── create_user.html
│       │   ├── edit_student.html
│       │   ├── edit_teacher.html
│       │   ├── attendance.html
│       │   ├── mark_attendance.html
│       │   ├── marks.html
│       │   ├── manage_marks.html
│       │   ├── fees.html
│       │   ├── reports.html
│       │   └── notifications.html
│       │
│       ├── student/
│       │   ├── dashboard.html
│       │   ├── courses.html
│       │   ├── course_details.html
│       │   ├── attendance.html
│       │   ├── marks.html
│       │   ├── fees.html
│       │   ├── reports.html
│       │   └── resources.html
│       │
│       └── teacher/
│           ├── dashboard.html
│           ├── students.html
│           ├── courses.html
│           ├── course_detail.html
│           ├── attendance.html
│           ├── mark_attendance.html
│           ├── marks.html
│           ├── manage_marks.html
│           ├── reports.html
│           ├── resources.html
│           └── task_submissions.html
│
├── venv/
└── .venv/

---

## 🔄 Key Modules

### Attendance
- Mark with validation (no duplicates, no future dates)
- Update with audit logging
- Automatic alerts when below threshold

### Marks & Grades
- Add/update with history tracking
- Auto grade calculation (A+ to F)
- GPA calculation

### Fee Management
- Add fee records with due dates
- Full/partial payments
- Auto late fee calculation
- Unique receipt numbers

### Notifications
- Admin sends custom notifications
- Recipient: All, Teachers, Students, Specific
- User preferences
- Unread count badge

---

## 🐛 Common Issues

### "No module named 'flask'"
```bash
venv\Scripts\activate  # Activate virtual environment
pip install -r requirements.txt
```

### "Access denied for user 'root'"
```python
# Check config.py
MYSQL_PASSWORD = 'YOUR_ACTUAL_PASSWORD'
```

### "Table 'acadlytics.users' doesn't exist"
```bash
python complete_setup_all.py
```

### Port 5000 in use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux
sudo lsof -ti:5000 | xargs kill
```

---

## 🌐 API Endpoints

| Module | Endpoints |
|--------|-----------|
| Auth | `/login`, `/register`, `/logout` |
| Admin | `/admin/dashboard`, `/admin/students`, `/admin/courses` |
| Student | `/student/dashboard`, `/student/courses`, `/student/attendance` |
| Teacher | `/teacher/dashboard`, `/teacher/courses`, `/teacher/marks` |
| Notifications | `/notifications`, `/admin/notifications` |



---

## 🙏 Acknowledgments
Flask, MySQL, Chart.js, Font Awesome

---

**Made with ❤️ for education**

---

## 🚀 Quick Start

```bash
# One-command setup (after configuring config.py)
python complete_setup_all.py && python run.py

# Then open: http://localhost:5000
```

**Login:** admin / admin123

---

