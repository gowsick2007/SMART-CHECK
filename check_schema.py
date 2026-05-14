from DATABASE.connection.db_connection import execute_query
try:
    cols = execute_query("SELECT column_name FROM information_schema.columns WHERE table_name = 'attendance'")
    print("ATTENDANCE COLUMNS:")
    for c in cols: print("- " + c['column_name'])
except Exception as e:
    print("Error:", e)
