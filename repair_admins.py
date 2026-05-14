import bcrypt
from DATABASE.connection.db_connection import execute_insert

def hash_p(pwd):
    return bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Fix execute_insert crash by passing empty tuple param
execute_insert("UPDATE students SET role = 'admin', is_active = 1 WHERE email LIKE '%%admin%%' AND role != 'creator'", ())
print("Repaired dynamic role elevations.")

new_hash = hash_p("admin123")
execute_insert("UPDATE students SET password_hash = %s WHERE email = 'admin123@gmail.com'", (new_hash,))

giri_hash = hash_p("giri123")
execute_insert("UPDATE students SET password_hash = %s WHERE email = 'giri123@gmail.com'", (giri_hash,))

print("Reset testing passwords successfully.")
