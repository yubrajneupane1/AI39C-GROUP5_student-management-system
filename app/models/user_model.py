from werkzeug.security import generate_password_hash, check_password_hash
from app.models.basemodel import BaseModel
from .database import Database

class User(BaseModel):

    @property
    def table(self):
        return "users"

    def __init__(self, name=None, email=None, username=None, password=None, role="student"):
        self.id = None
        self.name = name
        self.email = email
        self.username = username
        self._password = None  
        self.role = role
        if password:
            self.set_password(password)

    def set_password(self, plain_password):
        self._password = generate_password_hash(plain_password)

    def check_password(self, plain_password):
        
        if not self._password:
            return False
        return check_password_hash(self._password, plain_password)

    @classmethod
    def login(cls, username):
        db = Database()
        result = db.fetchone(
            "SELECT * FROM users WHERE username = %s",
            (username,)
        )
        db.close()
        return cls.from_db(result)

    @classmethod
    def from_db(cls, data):
        if data is None:
            return None
        user = cls()
        user.id = data.get("id")
        user.name = data.get("fullname")
        user.username = data.get("username")
        user.email = data.get("email")
        user._password = data.get("password")  
        user.role = data.get("role")
        return user

    def save(self):
        db = Database()
        db.execute(
            """
            INSERT INTO users (fullname, email, username, password, role)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (self.name, self.email, self.username, self._password, self.role),
        )
        db.close()

    def update(self, user_id, update_password=False):
        db = Database()
        if update_password:
            db.execute(
                "UPDATE users SET fullname=%s, email=%s, password=%s, role=%s WHERE id=%s",
                (self.name, self.email, self._password, self.role, user_id),
            )
        else:
            db.execute(
                "UPDATE users SET fullname=%s, email=%s, role=%s WHERE id=%s",
                (self.name, self.email, self.role, user_id),
            )
        db.close()

    def update_profile(self, user_id, update_password=False):
        db = Database()
        if update_password:
            db.execute(
                "UPDATE users SET fullname=%s, email=%s, password=%s WHERE id=%s",
                (self.name, self.email, self._password, user_id),
            )
        else:
            db.execute(
                "UPDATE users SET fullname=%s, email=%s WHERE id=%s",
                (self.name, self.email, user_id),
            )
        db.close()

    def email_exists(self, exclude_id=None):
        db = Database()
        if exclude_id:
            result = db.fetchone(
                "SELECT id FROM users WHERE email=%s AND id!=%s",
                (self.email, exclude_id),
            )
        else:
            result = db.fetchone(
                "SELECT id FROM users WHERE email=%s",
                (self.email,),
            )
        db.close()
        return result is not None

    def username_exists(self, exclude_id=None):
        db = Database()
        if exclude_id:
            result = db.fetchone(
                "SELECT id FROM users WHERE username=%s AND id!=%s",
                (self.username, exclude_id),
            )
        else:
            result = db.fetchone(
                "SELECT id FROM users WHERE username=%s",
                (self.username,),
            )
        db.close()
        return result is not None

    def __str__(self):
        return f"User(name={self.name}, email={self.email}, role={self.role})"

    def __repr__(self):
        return f"<User email={self.email}>"