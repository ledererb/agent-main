import re

ADMIN_PATH = 'admin.html'
WIDGET_PATH = 'voice-widget.html'

def update_admin():
    with open(ADMIN_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Text replacements
    content = content.replace('ThinkAI', 'DigiDesk')
    content = content.replace('thinkai.hu', 'digidesk.hu')
    
    # Colors
    content = re.sub(r'--figma-dark:\s*#[0-9a-fA-F]+;', '--figma-dark:     #082432;', content)
    content = re.sub(r'--figma-sidebar:\s*#[0-9a-fA-F]+;', '--figma-sidebar:  #082432;', content)
    content = re.sub(r'--bg:\s*#[0-9a-fA-F]+;', '--bg:         #082432;', content)
    content = re.sub(r'--figma-accent:\s*#[0-9a-fA-F]+;', '--figma-accent:   #1ceee0;', content)
    content = re.sub(r'--accent:\s*#[0-9a-fA-F]+;', '--accent:     #1ceee0;', content)
    content = re.sub(r'--figma-kpi-from:\s*#[0-9a-fA-F]+;', '--figma-kpi-from: #c5f0ee;', content)
    content = re.sub(r'--figma-kpi-to:\s*#[0-9a-fA-F]+;', '--figma-kpi-to:   #a8e5e3;', content)
    
    # Login gradient (radial-gradient replacing rgb values to cyan)
    content = content.replace('rgba(0,153,255,0.12)', 'rgba(28,238,224,0.12)')
    content = content.replace('rgba(0,212,200,0.08)', 'rgba(28,238,224,0.08)')
    content = content.replace('rgba(0,212,200,0.06)', 'rgba(28,238,224,0.06)')
    
    # Hardcoded 00CED1 (if any) -> 1ceee0
    content = content.replace('#00CED1', '#1ceee0')
    content = content.replace('#00ced1', '#1ceee0')

    # Status Badges
    badge_regex = r'\.badge-teal.*?\.badge-gray[^}]+}'
    new_badges = """.badge-teal   { background: rgba(28,238,224,0.12); color: #0f766e; }
    .badge-blue   { background: #dbeafe; color: #1e40af; }
    .badge-green  { background: #dcfce7; color: #166534; }
    .badge-purple { background: #f3e8ff; color: #6b21a8; }
    .badge-yellow { background: #fef3c7; color: #92400e; }
    .badge-orange { background: #ffedd5; color: #9a3412; }
    .badge-red    { background: #fee2e2; color: #991b1b; }
    .badge-gray   { background: #f3f4f6; color: #6b7280; }"""
    content = re.sub(badge_regex, new_badges, content, flags=re.DOTALL)

    # Font Family
    content = re.sub(r"font-family:\s*'Inter',\s*sans-serif;", "font-family: 'Inter', Arial, sans-serif;", content)

    # Radii
    # login-card
    content = re.sub(r'(\.login-card\s*\{[^}]*?border-radius:\s*)20px', r'\g<1>12px', content)
    # table-card
    content = re.sub(r'(\.table-card\s*\{[^}]*?border-radius:\s*)14px', r'\g<1>12px', content)
    # stat-card
    content = re.sub(r'(\.stat-card\s*\{[^}]*?border-radius:\s*)12px', r'\g<1>12px', content) # already 12px
    # chart-card
    content = re.sub(r'(\.chart-card\s*\{[^}]*?border-radius:\s*)12px', r'\g<1>12px', content) # already 12px
    # nav-item, btn-logout, btn-primary
    content = re.sub(r'(\.btn-primary\s*\{[^}]*?border-radius:\s*)10px', r'\g<1>8px', content)
    content = re.sub(r'(\.nav-item\s*\{[^}]*?border-radius:\s*)10px', r'\g<1>8px', content)
    content = re.sub(r'(\.btn-logout\s*\{[^}]*?border-radius:\s*)10px', r'\g<1>8px', content)
    content = re.sub(r'(\.form-input\s*\{[^}]*?border-radius:\s*)10px', r'\g<1>8px', content)
    content = re.sub(r'(\.sidebar-logo-icon\s*\{[^}]*?border-radius:\s*)10px', r'\g<1>8px', content)
    
    # badge radius
    content = re.sub(r'(\.badge\s*\{[^}]*?border-radius:\s*)6px', r'\g<1>9999px', content)

    # Shadows
    # stat-card doesn't have shadow. table-card doesn't. chart-card has:
    # box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    # popups: let's update modal/popups if there are any.
    content = content.replace('box-shadow: 0 8px 32px rgba(0,0,0,0.3);', 'box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);') # shadow-xl
    
    with open(ADMIN_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def update_widget():
    with open(WIDGET_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Text
    content = content.replace('ThinkAI', 'DigiDesk')
    content = content.replace('thinkai.hu', 'digidesk.hu')
    
    # Colors
    content = re.sub(r'--accent:\s*#[0-9a-fA-F]+;', '--accent: #1ceee0;', content)
    content = content.replace('rgba(0, 229, 204,', 'rgba(28, 238, 224,')
    content = content.replace('#00E5CC', '#1ceee0')
    content = content.replace('#33ffe6', '#c5f0ee') # accent-hover
    
    # Dark bg matching admin dark #082432
    content = re.sub(r'--bg-primary:\s*#[0-9a-fA-F]+;', '--bg-primary: #0a1f2e;', content)
    content = re.sub(r'--bg-secondary:\s*#[0-9a-fA-F]+;', '--bg-secondary: #082432;', content)
    
    # Font
    content = re.sub(r"font-family:\s*'Inter',\s*-apple-system,", "font-family: 'Inter', Arial,", content)

    with open(WIDGET_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    update_admin()
    update_widget()
    print("Done")
