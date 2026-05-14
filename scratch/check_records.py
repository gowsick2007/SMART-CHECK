from DATABASE.connection.db_connection import execute_query

def check():
    print("--- ATTENDANCE RECORDS ---")
    res = execute_query("""
        SELECT student_id, date, status, face_match_status, recorded_by_role, marked_by_name 
        FROM attendance 
        ORDER BY marked_at DESC 
        LIMIT 10
    """, fetch="all")
    for r in res:
        print(r)

if __name__ == "__main__":
    check()
