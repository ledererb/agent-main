import re

with open('admin.html', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('<div class="page active" id="page-analytics">')
end = content.find('</div><!-- end page-analytics -->', start)

if start != -1 and end != -1:
    analytics_html = content[start:end]
    
    # Emojis are generally not in the basic latin/extended latin blocks.
    # Let's find any char > U+2000 that is not a standard punctuation or box drawing, etc.
    # Actually, we can just replace the specific ones the user circled:
    emojis_to_remove = ['📞', '📅', '➖', '⏱️', '⏱', '📤', '✔️', '✅', '⛔', '➖', '✓']
    
    for e in emojis_to_remove:
        analytics_html = analytics_html.replace(e, '')
        
    # Also find any other emoji by replacing any char > U+2600 except 🚧 (U+1F6A7)
    # Be careful not to remove trend arrows ▲ ▼
    # Trend arrows are U+25B2 and U+25BC.
    new_html = ""
    for c in analytics_html:
        if ord(c) > 0x2600 and c not in ['🚧']:
            pass # remove it
        else:
            new_html += c
            
    content = content[:start] + new_html + content[end:]
    
    with open('admin.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Done")
