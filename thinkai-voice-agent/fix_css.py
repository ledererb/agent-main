with open('admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace all occurrences of #page-tudastar with #page-settings in CSS
html = html.replace('#page-tudastar', '#page-settings')

with open('admin.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("CSS selectors updated.")
