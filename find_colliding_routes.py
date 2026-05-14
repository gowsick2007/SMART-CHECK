with open(r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE\BACKEND\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if '@app.route' in l and ('/api/make-admin' in l or '/make-admin' in l):
        print(f"ROUTE ON LINE {i+1}: {l.strip()}")
