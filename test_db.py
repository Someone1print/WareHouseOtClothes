import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

print("DB_NAME:", os.getenv('DB_NAME'))
print("DB_USER:", os.getenv('DB_USER'))
# print("DB_PASSWORD:", os.getenv('DB_PASSWORD')) # Not printing password for security in logs
print("DB_HOST:", os.getenv('DB_HOST'))
print("DB_PORT:", os.getenv('DB_PORT'))

os.environ["PGCLIENTENCODING"] = "utf-8"

try:
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
