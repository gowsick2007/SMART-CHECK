with open(r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE\BACKEND\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'map_select.html' in l:
        print(f"FOUND AT LINE {i+1}")
        for offset in range(-4, 4):
             print(lines[i+offset].strip())
