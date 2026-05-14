import sys
import os
sys.path.insert(0, r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE")
from DATABASE.connection.db_connection import execute_query
res = execute_query("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'auto_verify_log'")
for row in res: print(f"{row['column_name']}: {row['data_type']}")
