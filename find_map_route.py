import re
with open(r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE\BACKEND\app.py", "r", encoding="utf-8") as f:
    content = f.read()
for match in re.finditer(r'def .*?map_select\.html.*?(?=def|\Z)', content, re.DOTALL):
    print(match.group(0))
    break # Just the first one is enough to see the surrounding route context

lines = content.splitlines()
for i, l in enumerate(lines):
    if 'map_select.html' in l:
        print(f"Line {i+1}: {l}")
        print("\n".join(lines[i-5:i+5]))
