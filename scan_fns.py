with open(r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE\BACKEND\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'def api_make_admin(' in l or 'def api_creator_make_admin(' in l:
        print(f"LINE {i+1}: {l.strip()}")
