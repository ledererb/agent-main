import io

with io.open('admin.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Emojis to keep
keep = set(['🚧', '▲', '▼'])

new_content = ""
removed = set()

for c in content:
    # Character codes:
    # U+2600 and above are mostly symbols and emojis.
    # U+2000 to U+206F are general punctuation (keep en-dash, em-dash, bullets).
    # U+1F000 to U+1FFFF are miscellaneous symbols and pictographs (emojis).
    
    # We want to remove emojis. Emojis generally are in these ranges:
    # U+2600 - U+27BF (Misc symbols, Dingbats)
    # U+1F300 - U+1F9FF (Misc Symbols and Pictographs, Transport, Supplement, etc.)
    # U+1FA70 - U+1FAFF (Symbols and Pictographs Extended-A)
    # Let's just remove anything >= U+2600 except our keep set.
    
    # Wait, some math symbols are in U+2190 - U+22FF. 
    # Let's remove >= U+1F000 (all high emojis).
    # And specifically remove things in U+2600-U+27BF (like ⚙, ✉, ❌, etc.)
    code = ord(c)
    
    if c in keep:
        new_content += c
    elif (0x1F000 <= code <= 0x1FAFF) or (0x2600 <= code <= 0x27BF):
        removed.add(c)
    else:
        new_content += c

with io.open('admin.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Removed {len(removed)} unique emojis: {' '.join(removed)}")
