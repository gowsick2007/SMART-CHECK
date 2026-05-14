from DATABASE.connection.db_connection import execute_query
import json

def check():
    print("--- STUDENTS COLUMNS ---")
    res = execute_query("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'students'", fetch="all")
    for r in res:
        print(f"{r['column_name']}: {r['data_type']}")
    
    print("\n--- ATTENDANCE COLUMNS ---")
    res = execute_query("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'attendance'", fetch="all")
    for r in res:
        print(f"{r['column_name']}: {r['data_type']}")

if __name__ == "__main__":
    check()
