import re

with open('admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the client find logic
old_find = r"const client = clients\.find\(c => c\.custom_data && \(c\.custom_data\.nev === r\.client \|\| c\.custom_data\.name === r\.client \|\| c\.custom_data\['név'\] === r\.client\)\);"
new_find = """const client = clients.find(c => {
              if (!c.custom_data) return false;
              let cd = {};
              try { cd = typeof c.custom_data === 'string' ? JSON.parse(c.custom_data) : c.custom_data; } catch(e){}
              let cn = (cd.nev || cd.name || cd['név'] || cd['Név'] || '').toLowerCase().trim();
              let rn = (r.client || '').toLowerCase().trim();
              if (cn && rn && cn === rn) return true;
              let em = (cd.email || '').toLowerCase().trim();
              if (em && rn && rn.includes(em)) return true;
              return false;
          });"""

html = re.sub(old_find, new_find, html)

old_cd = r"if \(client && client\.custom_data\) \{\s*const cd = client\.custom_data;"
new_cd = """if (client && client.custom_data) {
              let cd = {};
              try { cd = typeof client.custom_data === 'string' ? JSON.parse(client.custom_data) : client.custom_data; } catch(e){}"""

html = re.sub(old_cd, new_cd, html)

# Stop event propagation so it doesn't open the client view in the background
old_click = r'onclick="openInteractionSummaryModal\(\$\{i\}\)"'
new_click = 'onclick="event.stopPropagation(); openInteractionSummaryModal(${i})"'
html = html.replace(old_click, new_click)

with open('admin.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated admin.html.")
