import io

with io.open('admin.html', 'r', encoding='utf-8') as f:
    content = f.read()

emojis_to_remove = [
    '📞', '📅', '➖', '⏱️', '⏱', '📤', '✔️', '✅', '⛔', '✓', '💡', '📈', '⚠', '⚠️', '📈'
]

for emoji in emojis_to_remove:
    content = content.replace(emoji, '')

# Also let's just make sure there are no other emojis in JS.
# I will use a regex to strip any non-ASCII character that is not a hungarian letter,
# punctuation, etc. But that's dangerous. Doing explicit string replacements is safer.

with io.open('admin.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Emojis removed globally.")
