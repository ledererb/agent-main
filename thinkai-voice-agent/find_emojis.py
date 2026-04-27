import re
with open('admin.html', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('<div class="page active" id="page-analytics">')
end = content.find('</div><!-- end page-analytics -->', start)

if start != -1 and end != -1:
    analytics_html = content[start:end]
    # Find all emojis (or non-ascii chars)
    emojis = re.findall(r'[^\x00-\x7F]+', analytics_html)
    unique_emojis = set(emojis)
    print("Non-ASCII strings found:")
    for e in unique_emojis:
        print(repr(e), e)
else:
    print("Could not find #page-analytics")
