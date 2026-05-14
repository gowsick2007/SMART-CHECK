with open(r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE\BACKEND\app.py", "r", encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "make_admin" in line or "make-admin" in line:
            print(f"LINE {i+1}: {line.strip()}")
