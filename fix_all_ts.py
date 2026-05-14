import sys
import os
filepath = r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE\BACKEND\app.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

fixed = content.replace("CAST(timestamp AS DATE) = CURRENT_DATE", "date = CURRENT_DATE")
with open(filepath, "w", encoding="utf-8") as f:
    f.write(fixed)
print("Replacement check successful.")
