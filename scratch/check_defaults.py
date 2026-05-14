from DATABASE.connection.db_connection import execute_query

def check():
    print("--- ATTENDANCE DEFAULTS ---")
    res = execute_query("""
        SELECT column_name, column_default 
        FROM information_schema.columns 
        WHERE table_name = 'attendance'
    """, fetch="all")
    for r in res:
        print(f"{r['column_name']}: {r['column_default']}")

if __name__ == "__main__":
    check()
