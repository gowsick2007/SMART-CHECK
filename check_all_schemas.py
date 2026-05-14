from DATABASE.connection.db_connection import execute_query
try:
    tables = execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    for t in tables:
        tn = t['table_name']
        print(f"Table: {tn}")
        cols = execute_query(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{tn}'")
        for c in cols:
            print("  - " + c['column_name'])
except Exception as e:
    print("Error:", e)
