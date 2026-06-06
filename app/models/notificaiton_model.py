from app.models.basemodel import BaseModel

class NotificationModel(BaseModel):
    pass

def get_notifications(self):
    query = """
        SELECT * FROM notifications
    """
    self.cursor.execute(query)
    return self.cursor.fetchall()

def get_unread_count(self, user_id):
    result = self.db.fetchone(
        """
        SELECT COUNT(*) AS total
        FROM notifications
        WHERE user_id=%s
        AND is_read=0
        """,
        (user_id,)
    )

    return result["total"]

def mark_as_read(
    self,
    notification_id
):
    
def get_user_notifications(
    self,
    user_id
):
  query = """
UPDATE notifications
SET is_read=1
WHERE id=%s
"""
  return self.cursor.fetchall()

def get_recent_notifications(self, user_id):
    pass

# Notification cleanup
from app.models.database import Database
from datetime import datetime

class NotificationModel:
    def __init__(self):
        self.db = Database()

    def create_notification(self, user_id, notification_type, title, message, link=None):
        """Create a new notification"""
        self.db.execute("""
            INSERT INTO notifications (user_id, type, title, message, link)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, notification_type, title, message, link))
        return True

    def get_user_notifications(self, user_id, limit=50, unread_only=False):
        """Get notifications for a user"""
        query = "SELECT * FROM notifications WHERE user_id = %s"
        params = [user_id]
        
        if unread_only:
            query += " AND is_read = FALSE"
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        return self.db.fetch(query, tuple(params))

    def mark_as_read(self, notification_id):
        """Mark a notification as read"""
        self.db.execute("""
            UPDATE notifications 
            SET is_read=TRUE, read_at=NOW()
            WHERE id=%s
        """, (notification_id,))
        return True

    def mark_all_as_read(self, user_id):
        """Mark all notifications as read for a user"""
        self.db.execute("""
            UPDATE notifications 
            SET is_read=TRUE, read_at=NOW()
            WHERE user_id=%s AND is_read=FALSE
        """, (user_id,))
        return True

    def get_unread_count(self, user_id):
        """Get count of unread notifications"""
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM notifications WHERE user_id=%s AND is_read=FALSE",
            (user_id,)
        )
        return result['count'] if result else 0

    def get_preferences(self, user_id):
        """Get notification preferences for a user"""
        pref = self.db.fetchone(
            "SELECT * FROM notification_preferences WHERE user_id=%s",
            (user_id,)
        )
        
        if not pref:
            self.db.execute("""
                INSERT INTO notification_preferences (user_id)
                VALUES (%s)
            """, (user_id,))
            pref = self.db.fetchone(
                "SELECT * FROM notification_preferences WHERE user_id=%s",
                (user_id,)
            )
        
        return pref

    def update_preferences(self, user_id, preferences):
        """Update notification preferences"""
        self.db.execute("""
            UPDATE notification_preferences
            SET attendance_alerts=%s, fee_alerts=%s, system_alerts=%s,
                grade_alerts=%s, task_alerts=%s, email_notifications=%s,
                attendance_threshold=%s, updated_at=NOW()
            WHERE user_id=%s
        """, (
            preferences.get('attendance_alerts', True),
            preferences.get('fee_alerts', True),
            preferences.get('system_alerts', True),
            preferences.get('grade_alerts', True),
            preferences.get('task_alerts', True),
            preferences.get('email_notifications', False),
            preferences.get('attendance_threshold', 75),
            user_id
        ))
        return True

    def close(self):
        self.db.close()