from app.models.basemodel import BaseModel

class FeeModel(BaseModel):
    pass
def get_all_fees(self):
    query = "SELECT * FROM fees"
    self.cursor.execute(query)
    return self.cursor.fetchall()