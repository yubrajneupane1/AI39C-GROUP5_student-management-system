import pymysql
import config

try:
    connection = pymysql.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE
    )
    print("✅ Database connected successfully!")
    connection.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("\nPlease check:")
    print("1. MySQL is running")
    print("2. Database 'acadlytics' exists")
    print("3. Credentials in config.py are correct")