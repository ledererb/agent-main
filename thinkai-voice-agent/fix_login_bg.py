import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            content = f.read()

        target = """    #login-screen {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      background:
        radial-gradient(ellipse 80% 60% at 50% 0%, rgba(28,238,224,0.12) 0%, transparent 70%),
        radial-gradient(ellipse 60% 40% at 80% 80%, rgba(28,238,224,0.08) 0%, transparent 60%),
        var(--bg);
    }"""
        
        replacement = """    #login-screen {
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
        
        # bs4 doesn't touch CSS inside <style>, so this should match exactly
        if target in content:
            content = content.replace(target, replacement)
            print("Login background restored!")
        else:
            print("Could not find login screen target block in CSS")

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(content)

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
