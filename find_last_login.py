with open(r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE\FRONTEND\pages\creator_dashboard.html", "r", encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "LAST LOGIN" in line.upper():
            print(f"LINE {i+1}: {line.strip()}")
