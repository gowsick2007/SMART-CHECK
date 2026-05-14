import sys
import os
sys.path.insert(0, r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE")
from DATABASE.connection.db_connection import execute_query

def check_schema():
    tables = ["attendance", "students"]
    for table in tables:
        print(f"\n--- Table: {table} ---")
        res = execute_query(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}'
        """)
        for row in res:
            print(f"{row['column_name']}: {row['data_type']}")

if __name__ == "__main__":
    check_schema()
