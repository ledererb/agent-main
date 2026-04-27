import re

with open('admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove Tudastar Nav
nav_pattern = re.compile(r'<button class="nav-item" id="nav-tudastar".*?</button>\n', re.DOTALL)
html = nav_pattern.sub('', html)

# 2. Extract Praxis and Szabalyok content
praxis_match = re.search(r'(<!-- PRAXISINFORMÁCIÓ TAB -->\n<div id="tt-content-praxis">.*?</div><!-- end praxis content -->\n)', html, re.DOTALL)
if not praxis_match:
    print("Praxis content not found!")
praxis_html = praxis_match.group(1).replace('id="tt-content-praxis"', 'id="settings-view-praxis" class="settings-subview" style="display:none;"')

szabalyok_match = re.search(r'(<!-- SZABÁLYOK TAB -->\n<div id="tt-content-szabalyok" style="display:none;">.*?</div><!-- end szabalyok content -->\n)', html, re.DOTALL)
if not szabalyok_match:
    print("Szabalyok content not found!")
szabalyok_html = szabalyok_match.group(1).replace('id="tt-content-szabalyok"', 'id="settings-view-szabalyok" class="settings-subview"').replace('id="tt-content-szabalyok" style="display:none;"', 'id="settings-view-szabalyok" class="settings-subview" style="display:none;"')

# 3. Remove entire page-tudastar
page_tudastar_pattern = re.compile(r'<!-- TUDÁSTÁR PAGE -->\n<div class="page" id="page-tudastar">.*?</div><!-- end page-tudastar -->\n', re.DOTALL)
html = page_tudastar_pattern.sub('', html)

# 4. Inject into page-settings
settings_header_pattern = re.compile(r'(<!-- SETTINGS PAGE -->\n<div class="page" id="page-settings">)\n', re.DOTALL)

switcher_html = """
<div class="view-switcher-container" style="margin-bottom: 20px;">
<button class="view-btn active" onclick="switchSettingsView('agent', this)">Agent Beállítások</button>
<button class="view-btn" onclick="switchSettingsView('praxis', this)">Praxisinformáció</button>
<button class="view-btn" onclick="switchSettingsView('szabalyok', this)">Szabályok <span class="wip-badge">🚧</span></button>
</div>
<div id="settings-view-agent" class="settings-subview" style="display:block;">
"""

html = settings_header_pattern.sub(r'\1\n' + switcher_html, html)

# Close settings-view-agent before KANBAN PAGE
kanban_pattern = re.compile(r'(<!-- KANBAN PAGE -->)', re.DOTALL)
html = kanban_pattern.sub('</div><!-- end settings-view-agent -->\n' + praxis_html + szabalyok_html + r'\1', html)

# 5. Fix JS
js_remove_tudastar = re.compile(r'document\.getElementById\(\'nav-tudastar\'\)\.classList\.remove\(\'active\'\);?\n?')
html = js_remove_tudastar.sub('', html)
js_add_tudastar = re.compile(r'\} else if \(pageId === \'tudastar\'\) \{\n\s*document\.getElementById\(\'nav-tudastar\'\)\.classList\.add\(\'active\'\);\n\s*initTudastar\(\);\n\s*\}')
html = js_add_tudastar.sub('}', html)

# Inject JS for switchSettingsView
settings_js = """
function switchSettingsView(viewId, btn) {
    document.querySelectorAll('.settings-subview').forEach(el => el.style.display = 'none');
    document.querySelectorAll('#page-settings .view-btn').forEach(el => el.classList.remove('active'));
    document.getElementById('settings-view-' + viewId).style.display = 'block';
    if(btn) btn.classList.add('active');
}
"""

js_insert_pattern = re.compile(r'(function switchCustomerView)', re.DOTALL)
html = js_insert_pattern.sub(settings_js + r'\n\1', html)

with open('admin.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("HTML DOM refactor complete.")
