import io
import re

with io.open('admin.html', 'r', encoding='utf-8') as f:
    content = f.read()

# check all emojis globally
chars = set()
for c in content:
    if ord(c) > 127:
        chars.add(c)
        
hungarian = set('áéíóöőúüűÁÉÍÓÖŐÚÜŰ')
other_chars = [c for c in chars if c not in hungarian]

with io.open('emojis_global.txt', 'w', encoding='utf-8') as out:
    for c in other_chars:
        out.write(f"{c} (U+{ord(c):04X})\n")
print("Done")
