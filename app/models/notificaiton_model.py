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