from DATABASE.connection.db_connection import execute_query
users = execute_query("SELECT email, role, password_hash FROM students WHERE role = 'admin';", fetch="all")
print("RAW PASSWORD HASHES:")
for u in users:
    print(f"EMAIL: {u['email']} | HASH: [{u['password_hash']}]")
