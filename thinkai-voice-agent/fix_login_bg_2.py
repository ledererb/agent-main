import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the login-screen CSS block
        pattern = r'(#login-screen\s*\{[^}]*?background:.*?)(var\(--bg\);)(.*?\} )'
        # The background currently has radial-gradients followed by var(--bg);
        # Let's just replace the whole background property.
        pattern = r'#login-screen\s*\{[^}]*?\}'
        
        match = re.search(pattern, content)
        if match:
            new_css = """#login-screen {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      background:
        radial-gradient(ellipse 80% 60% at 50% 0%, rgba(28,238,224,0.12) 0%, transparent 70%),
        url('login-bg.jpg') center/cover no-repeat;
      background-blend-mode: overlay;
      background-color: var(--bg);
    }"""
            content = content.replace(match.group(0), new_css)
            print("Login background restored!")
        else:
            print("Could not find login screen target block in CSS")

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(content)

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
