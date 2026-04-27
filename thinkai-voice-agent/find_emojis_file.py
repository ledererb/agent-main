import re

with open('admin.html', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('<div class="page active" id="page-analytics">')
end = content.find('</div><!-- end page-analytics -->', start)

if start != -1 and end != -1:
    analytics_html = content[start:end]
    
    # Extract all non-ascii characters
    chars = set()
    for c in analytics_html:
        if ord(c) > 127:
            chars.add(c)
            
    # Filter out common Hungarian accented letters
    hungarian = set('áéíóöőúüűÁÉÍÓÖŐÚÜŰ')
    other_chars = [c for c in chars if c not in hungarian]
    
    with open('emojis_found.txt', 'w', encoding='utf-8') as out:
        for c in other_chars:
            out.write(f"{c} (U+{ord(c):04X})\n")
    print("Done")
