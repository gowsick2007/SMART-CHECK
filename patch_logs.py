import re
filepath = r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE\FRONTEND\js\creator.js"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Automatically inject console log after every const data = await res.json()
fixed = re.sub(r'(const data = await res\.json\(\);)', r'\1\n                console.log("API Response:", data);', content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(fixed)

print("API response logs injected everywhere successfully.")
