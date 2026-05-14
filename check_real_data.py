from DATABASE.connection.db_connection import execute_query
res = execute_query("SELECT * FROM attendance WHERE recorded_by_role != 'system' LIMIT 5")
for r in res:
    print(r)
