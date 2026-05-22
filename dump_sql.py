import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothes_factory_warehouse.settings')
django.setup()

from django.db import connection

query = "SELECT name, object_definition(object_id) FROM sys.triggers"

with connection.cursor() as cursor:
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"Found {len(rows)} triggers")
        for row in rows:
            print(f"--- TRIGGER: {row[0]} ---")
            print(row[1])
            print("\n")
    except Exception as e:
        print(f"Error: {e}")
