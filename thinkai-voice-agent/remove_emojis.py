import io

with io.open('admin.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the emojis to remove
emojis_to_remove = ['💡', '📈', '⚠', '⚠️']

for emoji in emojis_to_remove:
    content = content.replace(emoji, '')

with io.open('admin.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Emojis removed successfully.")
