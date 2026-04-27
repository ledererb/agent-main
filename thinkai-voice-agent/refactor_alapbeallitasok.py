import sys

def main():
    with open('admin.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove the Alapbeállítások button
    button_str = '<button class="view-btn" onclick="switchSettingsView(\'alap\', this)">Alapbeállítások</button>\n'
    content = content.replace(button_str, '')

    # 2. Extract the Csatornák section
    start_csatornak = content.find('<div class="settings-section">\n<div class="settings-section-title">Csatornák</div>')
    end_csatornak = content.find('</div>\n</div>\n</div>\n<div id="settings-view-agent" class="settings-subview" style="display:block;">')
    
    # We add the two closing divs that belong to the Csatornák section
    csatornak_html = content[start_csatornak:end_csatornak] + '</div>\n</div>\n\n'

    # 3. Remove the entire settings-view-alap
    start_alap = content.find('<div id="settings-view-alap" class="settings-subview" style="display:none;">')
    end_alap = content.find('<div id="settings-view-agent" class="settings-subview" style="display:block;">')
    
    # Slice it out
    content = content[:start_alap] + content[end_alap:]

    # 4. Insert Csatornák before Nyitvatartás
    nyitvatartas_str = '<div class="settings-section">\n<div class="settings-section-title"> Nyitvatartás</div>'
    content = content.replace(nyitvatartas_str, csatornak_html + nyitvatartas_str)

    with open('admin.html', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Refactoring complete.")

if __name__ == "__main__":
    main()
