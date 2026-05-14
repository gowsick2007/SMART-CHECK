with open(r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE\BACKEND\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "CAST(timestamp AS DATE)" in line or 'a.timestamp' in line:
        print(f"Line {i+1}: {line.strip()}")
