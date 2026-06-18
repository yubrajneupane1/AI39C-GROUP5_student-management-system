import unittest
from app.models.basemodel import BaseModel
from app.models.database import Database


class TestBaseModel(unittest.TestCase):
    def test_base_model_abstract(self):
        """BaseModel should be abstract and not instantiable directly."""
        with self.assertRaises(TypeError):
            BaseModel()


class TestDatabase(unittest.TestCase):
    def test_database_connection(self):
        """Database connection should be established."""
        # This will use the actual config
        # Skip if no database connection
        try:
            db = Database()
            self.assertIsNotNone(db.connection)
            db.close()
        except Exception:
            self.skipTest("Database not available for testing")


if __name__ == "__main__":
    unittest.main()