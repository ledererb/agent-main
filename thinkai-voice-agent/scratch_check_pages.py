import re
with open("admin.html", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if re.search(r'id=[\"\'](page-|view-)', line):
            print(f"{i+1}: {line.strip()}")
