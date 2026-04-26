import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            html = f.read()

        # 1. Update View Switcher
        # Find the Switcher div
        switcher_pattern = r'<!-- View Switcher -->\s*<div style=\"display:flex; gap: 8px; margin-bottom: 20px; background: rgba\(8, 36, 50, 0\.05\); padding: 4px; border-radius: 12px; width: max-content; border: 1px solid rgba\(8, 36, 50, 0\.1\);\">.*?</div>'

        new_switcher_html = '''<!-- View Switcher -->
        <div class="view-switcher-container">
          <button class="view-btn active" onclick="switchCustomerView('interactions', this)">Interakciós lista</button>
          <button class="view-btn" onclick="switchCustomerView('kanban', this)">Kanban</button>
          <button class="view-btn" onclick="switchCustomerView('clients', this)">Ügyfelek adatbázisa</button>
        </div>'''

        html = re.sub(switcher_pattern, new_switcher_html, html, flags=re.DOTALL)

        # 2. Update Drawer HTML
        drawer_pattern = r'<!-- Customer Drawer -->.*?<!-- Drawer Overlay -->\s*<div id=\"drawer-overlay\".*?</div>'

        new_drawer_html = '''<!-- Customer Drawer -->
    <div id="customer-drawer" class="customer-drawer">
      <div class="drawer-header">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div>
            <h2 id="drawer-name" class="drawer-title">Ügyfél neve</h2>
            <div id="drawer-email" class="drawer-subtitle">email@example.com</div>
            <div id="drawer-phone" class="drawer-subtitle">+36 30 123 4567</div>
          </div>
          <button onclick="closeCustomerDrawer()" class="drawer-close-btn">✖</button>
        </div>
        <div style="margin-top:20px;">
          <label class="drawer-label">Státusz</label>
          <select id="drawer-status" class="drawer-select">
            <option value="Új">Új</option>
            <option value="Folyamatban">Folyamatban</option>
            <option value="Lezárt">Lezárt</option>
          </select>
        </div>
      </div>
      <div class="drawer-body">
        <h3 class="drawer-label" style="margin-bottom:20px;">Interakciós történet</h3>
        <div id="drawer-timeline" style="display:flex; flex-direction:column; gap:16px;">
          <div class="drawer-empty">Még nincsenek adatok...</div>
        </div>
      </div>
    </div>
    <!-- Drawer Overlay -->
    <div id="drawer-overlay" class="drawer-overlay" onclick="closeCustomerDrawer()"></div>'''

        html = re.sub(drawer_pattern, new_drawer_html, html, flags=re.DOTALL)

        # 3. Update switchCustomerView JS to remove inline style assignments
        old_js = '''// Customer Center JS
function switchCustomerView(viewId, btn) {
    document.querySelectorAll('.customer-view').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.view-btn').forEach(el => {
        el.classList.remove('active');
        el.style.background = 'transparent';
        el.style.color = 'rgba(8, 36, 50, 0.6)';
        el.style.boxShadow = 'none';
    });
    
    document.getElementById('view-' + viewId).style.display = 'block';
    
    if(btn) {
        btn.classList.add('active');
        btn.style.background = 'var(--brand-primary)';
        btn.style.color = '#082432';
        btn.style.boxShadow = '0 1px 2px rgba(0,0,0,0.05)';
    }
}'''

        new_js = '''// Customer Center JS
function switchCustomerView(viewId, btn) {
    document.querySelectorAll('.customer-view').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.view-btn').forEach(el => {
        el.classList.remove('active');
    });
    
    document.getElementById('view-' + viewId).style.display = 'block';
    
    if(btn) {
        btn.classList.add('active');
    }
}'''

        html = html.replace(old_js, new_js)

        # 4. Insert new CSS into the <style> section
        css_to_inject = '''
    /* ── Ügyfélközpont & Drawer Styles ────────────────────────────────────────── */
    .view-switcher-container {
      display: flex; gap: 8px; margin-bottom: 20px; background: rgba(8, 36, 50, 0.05); padding: 4px; border-radius: 12px; width: max-content; border: 1px solid rgba(8, 36, 50, 0.1);
    }
    body.dark .view-switcher-container { background: rgba(28, 238, 224, 0.05); border: 1px solid rgba(28, 238, 224, 0.1); }
    
    .view-btn {
      padding: 8px 16px; border:none; border-radius: 8px; font-weight:600; font-size:14px; cursor:pointer; transition:all 0.2s; background:transparent; color:rgba(8, 36, 50, 0.6);
    }
    body.dark .view-btn { color: rgba(255, 255, 255, 0.5); }
    
    .view-btn.active {
      background: var(--brand-primary); color: #082432; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    body.dark .view-btn.active { color: #082432; }

    .customer-drawer {
      position:fixed; top:0; right:-100%; width:400px; height:100vh; background:#fff; z-index:10000; box-shadow:-5px 0 30px rgba(0,0,0,0.1); transition:right 0.3s cubic-bezier(0.4, 0, 0.2, 1); display:flex; flex-direction:column;
    }
    body.dark .customer-drawer { background: #0b1c27; box-shadow:-5px 0 30px rgba(0,0,0,0.5); border-left: 1px solid rgba(255,255,255,0.05); }
    
    .drawer-header {
      padding:24px; border-bottom:1px solid rgba(8,36,50,0.1);
    }
    body.dark .drawer-header { border-bottom:1px solid rgba(255,255,255,0.05); }

    .drawer-title { font-size:20px; font-weight:bold; color:#082432; margin-bottom:8px; }
    body.dark .drawer-title { color: #c8d6e5; }

    .drawer-subtitle { color:rgba(8,36,50,0.7); font-size:14px; margin-bottom:4px; }
    body.dark .drawer-subtitle { color:#6b8b99; }

    .drawer-close-btn { background:transparent; border:none; cursor:pointer; padding:8px; border-radius:50%; color:rgba(8,36,50,0.5); transition:background 0.2s; }
    .drawer-close-btn:hover { background: rgba(8,36,50,0.05); }
    body.dark .drawer-close-btn { color:#6b8b99; }
    body.dark .drawer-close-btn:hover { background: rgba(255,255,255,0.1); }

    .drawer-label { display:block; font-size:12px; font-weight:600; text-transform:uppercase; color:rgba(8,36,50,0.6); margin-bottom:8px; }
    body.dark .drawer-label { color:#6b8b99; }

    .drawer-select { width:100%; padding:10px; border-radius:8px; border:1px solid rgba(8,36,50,0.1); background:rgba(8,36,50,0.05); color:#082432; font-weight:500; outline:none; }
    body.dark .drawer-select { background: #132b3b; border:1px solid rgba(255,255,255,0.1); color: #c8d6e5; }

    .drawer-body { flex:1; overflow-y:auto; padding:24px; background:rgba(8,36,50,0.02); }
    body.dark .drawer-body { background: #08151f; }

    .drawer-empty { color:rgba(8,36,50,0.5); font-size:14px; }
    body.dark .drawer-empty { color:#6b8b99; }

    .drawer-overlay { display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(8,36,50,0.3); backdrop-filter:blur(2px); z-index:9999; }
    body.dark .drawer-overlay { background:rgba(0,0,0,0.5); }
    /* ───────────────────────────────────────────────────────────────────────── */
'''

        html = html.replace('</style>', css_to_inject + '\n</style>')

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Successfully added Dark Mode support!')
    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    main()
