import pymysql
import config

class Database:
    def __init__(self):
        try:
            self.connection = pymysql.connect(
                host=config.MYSQL_HOST,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
                database=config.MYSQL_DATABASE,
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.connection.cursor()
            print("Database Connected")
        except Exception as e:
            print("Database Error:", e)

    def fetch(self, query, values=None):
        self.cursor.execute(query, values)
        return self.cursor.fetchall()

    def fetchone(self, query, values=None):
        self.cursor.execute(query, values)
        return self.cursor.fetchone()

    def execute(self, query, values=None):
        self.cursor.execute(query, values)
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()