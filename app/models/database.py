import pymysql
from config import *

class Database:

    @staticmethod
    def get_connection():
        return pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )