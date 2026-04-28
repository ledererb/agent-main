import re

with open("web_server.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace async def for all admin routes and legacy API
content = re.sub(r'async def admin_', r'def admin_', content)
content = re.sub(r'async def get_calendar', r'def get_calendar', content)
content = re.sub(r'async def get_emails', r'def get_emails', content)

with open("web_server.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed async defs in web_server.py")
