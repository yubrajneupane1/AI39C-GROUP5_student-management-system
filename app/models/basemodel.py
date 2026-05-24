from abc import ABC, abstractmethod
from .database import Database

class BaseModel(ABC):
    @property
    @abstractmethod
    def table(self):
        pass

    @classmethod
    def find_by_id(cls, item_id):
        instance = cls()
        db = Database()
        result = db.fetchone(
            f"SELECT * FROM {instance.table} WHERE id=%s",
            (item_id,)
        )
        db.close()
        if result:
            return cls.from_db(result)
        return None

    @classmethod
    def find_by(cls, column, value):
        instance = cls()
        db = Database()
        result = db.fetchone(
            f"SELECT * FROM {instance.table} WHERE {column}=%s",
            (value,)
        )
        db.close()
        if result:
            return cls.from_db(result)
        return None

    @classmethod
    def find_all(cls):
        instance = cls()
        db = Database()
        result = db.fetchall(
            f"SELECT * FROM {instance.table}"
        )
        db.close()
        return result

    @classmethod
    def count_all(cls):
        instance = cls()
        db = Database()
        result = db.fetchone(
            f"SELECT COUNT(*) as total FROM {instance.table}"
        )
        db.close()
        return result["total"]

    @classmethod
    def delete_by_id(cls, item_id):
        instance = cls()
        db = Database()
        db.execute(
            f"DELETE FROM {instance.table} WHERE id=%s",
            (item_id,)
        )
        db.close()