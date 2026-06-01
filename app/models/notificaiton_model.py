from app.models.basemodel import BaseModel

class NotificationModel(BaseModel):
    pass

def get_notifications(self):
    query = """
        SELECT * FROM notifications
    """
    self.cursor.execute(query)
    return self.cursor.fetchall()
