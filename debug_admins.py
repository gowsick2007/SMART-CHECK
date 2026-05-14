from DATABASE.connection.db_connection import execute_query
users = execute_query("SELECT name, email, role, is_active FROM students WHERE role = 'admin';", fetch="all")
print("ALL REGISTERED ADMINS:")
for u in users:
    print(u)

all_users = execute_query("SELECT name, email, role FROM students ORDER BY role ASC LIMIT 10;", fetch="all")
print("\nTOP 10 OTHER USERS:")
for u in all_users:
    print(u)
