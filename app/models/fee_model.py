from app.models.basemodel import BaseModel

class FeeModel(BaseModel):
    pass
def get_all_fees(self):
    query = "SELECT * FROM fees"
    self.cursor.execute(query)
    return self.cursor.fetchall()
def get_pending_fees(self):
    query = """
    SELECT *
    FROM fees
    WHERE status='Pending'
    """
    self.cursor.execute(query)
    return self.cursor.fetchall()