from DATABASE.connection.db_connection import execute_query
cols = execute_query("SELECT column_name FROM information_schema.columns WHERE table_name = 'attendance';", fetch="all")
for c in cols:
    print(c['column_name'])
