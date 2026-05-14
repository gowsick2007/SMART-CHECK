from DATABASE.connection.db_connection import get_connection
conn = get_connection()
import psycopg2.extras
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
for tbl in ['attendance', 'auto_verify_log']:
    print(f"--- {tbl} ---")
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{tbl}'")
    for r in cur.fetchall():
        print(dict(r))
conn.close()
