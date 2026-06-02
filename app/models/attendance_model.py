from app.models.database import Database
from datetime import datetime, date

class AttendanceModel:
    def __init__(self):
        self.db = Database()

    def mark_attendance(self, student_id, course_id, status, marked_by, remarks=None):
        """Mark attendance with validation"""
        today = date.today()
        
        # Validate: No duplicate attendance
        existing = self.db.fetchone(
            "SELECT id FROM attendance WHERE student_id=%s AND course_id=%s AND date=%s",
            (student_id, course_id, today)
        )
        
        if existing:
            return False, "Attendance already marked for today"
        
        # Insert attendance
        self.db.execute(
            """INSERT INTO attendance 
               (student_id, course_id, date, status, marked_by, remarks, marked_at) 
               VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
            (student_id, course_id, today, status, marked_by, remarks)
        )
        
        # Check for attendance alerts
        self._check_attendance_alerts(student_id, course_id)
        
        return True, "Attendance marked successfully"

    def update_attendance(self, attendance_id, status, changed_by, reason=None):
        """Update attendance with audit logging"""
        existing = self.db.fetchone(
            "SELECT * FROM attendance WHERE id=%s", 
            (attendance_id,)
        )
        
        if not existing:
            return False, "Attendance record not found"
        
        # Prevent updating future dates
        if existing['date'] > date.today():
            return False, "Cannot update future attendance"
        
        self.db.execute(
            "UPDATE attendance SET status=%s, updated_at=NOW() WHERE id=%s",
            (status, attendance_id)
        )
        
        # Add to audit log
        self.db.execute("""
            INSERT INTO attendance_logs (attendance_id, action, old_status, new_status, changed_by, reason)
            VALUES (%s, 'update', %s, %s, %s, %s)
        """, (attendance_id, existing['status'], status, changed_by, reason))
        
        return True, "Attendance updated successfully"

    def get_student_attendance(self, student_id, course_id=None):
        """Get attendance records with filters"""
        query = """
            SELECT a.*, c.name as course_name, 
                   u.fullname as marked_by_name
            FROM attendance a
            JOIN courses c ON a.course_id = c.id
            LEFT JOIN users u ON a.marked_by = u.id
            WHERE a.student_id = %s
        """
        params = [student_id]
        
        if course_id:
            query += " AND a.course_id = %s"
            params.append(course_id)
        
        query += " ORDER BY a.date DESC"
        
        return self.db.fetch(query, tuple(params))

    def get_attendance_summary(self, student_id):
        """Get attendance summary statistics"""
        result = self.db.fetchone("""
            SELECT 
                COUNT(*) as total_classes,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late,
                SUM(CASE WHEN status = 'excused' THEN 1 ELSE 0 END) as excused,
                ROUND(AVG(CASE WHEN status = 'present' THEN 1 ELSE 0 END) * 100, 2) as percentage
            FROM attendance
            WHERE student_id = %s
        """, (student_id,))
        
        return result

    def get_course_attendance_summary(self, course_id):
        """Get attendance summary for a course"""
        results = self.db.fetch("""
            SELECT 
                u.fullname,
                u.id as student_id,
                COUNT(a.id) as total_classes,
                SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present,
                ROUND(AVG(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) * 100, 2) as percentage
            FROM users u
            JOIN enrollments e ON u.id = e.student_id
            LEFT JOIN attendance a ON u.id = a.student_id AND a.course_id = %s
            WHERE e.course_id = %s AND u.role = 'student'
            GROUP BY u.id, u.fullname
            ORDER BY percentage DESC
        """, (course_id, course_id))
        
        return results

    def _check_attendance_alerts(self, student_id, course_id):
        """Check if attendance percentage falls below threshold"""
        summary = self.get_attendance_summary(student_id)
        
        if summary and summary['percentage'] is not None:
            # Get user preference
            pref = self.db.fetchone(
                "SELECT attendance_threshold FROM notification_preferences WHERE user_id=%s",
                (student_id,)
            )
            
            threshold = pref['attendance_threshold'] if pref else 75
            
            if summary['percentage'] < threshold:
                # Check if alert already sent this week
                recent_alert = self.db.fetchone("""
                    SELECT id FROM attendance_alerts
                    WHERE student_id=%s AND course_id=%s 
                    AND alert_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                    AND is_sent = TRUE
                """, (student_id, course_id))
                
                if not recent_alert:
                    # Create alert
                    self.db.execute("""
                        INSERT INTO attendance_alerts 
                        (student_id, course_id, threshold, current_percentage, alert_date, alert_type)
                        VALUES (%s, %s, %s, %s, CURDATE(), 'warning')
                    """, (student_id, course_id, threshold, summary['percentage']))
                    
                    # Create notification
                    course = self.db.fetchone("SELECT name FROM courses WHERE id=%s", (course_id,))
                    self.db.execute("""
                        INSERT INTO notifications 
                        (user_id, type, title, message, link)
                        VALUES (%s, 'attendance', 'Attendance Warning', 
                        CONCAT('Your attendance in ', %s, ' is below ', %s, '%. Current: ', %s, '%. Please ensure regular attendance.'),
                        '/student/attendance')
                    """, (student_id, course['name'] if course else 'course', threshold, summary['percentage']))

    def close(self):
        self.db.close()