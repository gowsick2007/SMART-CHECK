from DATABASE.connection.db_connection import execute_query
res = execute_query("SELECT name, role, email FROM students WHERE role IN ('admin', 'creator')")
print(res)
