from DATABASE.connection.db_connection import execute_query
import json

def check():
    print("--- ALL RECORDS FOR 5247005 ---")
    res = execute_query("""
        SELECT * FROM attendance 
        WHERE student_id = '5247005'
        ORDER BY date DESC 
    """, fetch="all")
    for r in res:
        # Convert date and time to string for printing
        r['date'] = str(r['date'])
        r['time'] = str(r['time'])
        r['marked_at'] = str(r['marked_at'])
        print(r)

if __name__ == "__main__":
    check()
