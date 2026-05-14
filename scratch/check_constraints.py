
from DATABASE.connection.db_connection import execute_query
import json

try:
    constraints = execute_query("""
        SELECT conname, pg_get_constraintdef(oid) 
        FROM pg_constraint 
        WHERE conrelid = 'attendance'::regclass;
    """, fetch="all")
    print(json.dumps(constraints, indent=2))
except Exception as e:
    print(f"Error: {e}")
