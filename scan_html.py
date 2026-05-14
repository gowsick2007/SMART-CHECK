import re
with open(r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE\BACKEND\app.py", "r", encoding="utf-8") as f:
    content = f.read()
matches = re.findall(r'"[\w\.-]+\.html"', content)
for m in set(matches):
    print(m)
