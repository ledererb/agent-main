import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            html = f.read()

        # 1. Update Sidebar Navigation
        html = re.sub(r'<button class="nav-item"\s*onclick="showPage\(\'kanban\'\)" id="nav-kanban">.*?</button>', '', html, flags=re.DOTALL)
        html = re.sub(r'<button class="nav-item"\s*onclick="showPage\(\'clients\'\)" id="nav-clients">.*?</button>', '', html, flags=re.DOTALL)

        nav_inter_pattern = r'(<button class="nav-item"\s*onclick="showPage\(\'interactions\'\)" id="nav-interactions">\s*<svg.*?</svg>\s*<span>)Interakciók(</span>\s*</button>)'
        html = re.sub(nav_inter_pattern, r'\g<1>Ügyfélközpont\g<2>', html)

        # 2. Extract pages
        page_kanban_match = re.search(r'(<div class="page" id="page-kanban">.*?</div>\n\n\s*<!-- CLIENTS PAGE -->)', html, flags=re.DOTALL)
        page_clients_match = re.search(r'(<div class="page" id="page-clients">.*?(<!-- Client Fields Setup Modal -->.*?<!-- Log Modal HTML -->.*?</div>\s*</div>\s*)\n)', html, flags=re.DOTALL)

        if not page_kanban_match or not page_clients_match:
            print("Kanban or Clients page not found!")
            return

        page_kanban = page_kanban_match.group(1).replace('class="page" id="page-kanban"', 'class="customer-view" id="view-kanban" style="display:none;"')
        page_clients = page_clients_match.group(1).replace('class="page" id="page-clients"', 'class="customer-view" id="view-clients" style="display:none;"')
        
        # Remove from original location
        html = html.replace(page_kanban_match.group(1), '')
        html = html.replace(page_clients_match.group(1), '')
        
        # 3. Inject Switcher
        switcher_html = '''
        <!-- View Switcher -->
        <div style="display:flex; gap: 8px; margin-bottom: 20px; background: rgba(8, 36, 50, 0.05); padding: 4px; border-radius: 12px; width: max-content; border: 1px solid rgba(8, 36, 50, 0.1);">
          <button class="view-btn active" onclick="switchCustomerView('interactions', this)" style="padding: 8px 16px; border:none; border-radius: 8px; font-weight:600; font-size:14px; cursor:pointer; transition:all 0.2s; background:var(--brand-primary); color:#082432; box-shadow:0 1px 2px rgba(0,0,0,0.05);">Interakciós lista</button>
          <button class="view-btn" onclick="switchCustomerView('kanban', this)" style="padding: 8px 16px; border:none; border-radius: 8px; font-weight:600; font-size:14px; cursor:pointer; transition:all 0.2s; background:transparent; color:rgba(8, 36, 50, 0.6);">Kanban</button>
          <button class="view-btn" onclick="switchCustomerView('clients', this)" style="padding: 8px 16px; border:none; border-radius: 8px; font-weight:600; font-size:14px; cursor:pointer; transition:all 0.2s; background:transparent; color:rgba(8, 36, 50, 0.6);">Ügyfelek adatbázisa</button>
        </div>
        
        <div class="customer-view" id="view-interactions" style="display:block;">
        '''
        
        # We need to correctly target the page-interactions container
        page_inter_pattern = r'(<div class="page" id="page-interactions">\s*<div class="analytics-shell">)'
        html = re.sub(page_inter_pattern, r'\g<1>\n' + switcher_html, html)
        
        # We need to find the specific closing div for page-interactions to inject Kanban and Clients.
        # page-interactions ends before <!-- CALENDAR PAGE -->
        end_inter_pattern = r'(</div><!-- end analytics-shell -->\s*</div>\s*)(<!-- CALENDAR PAGE -->)'
        replacement = r'</div><!-- end view-interactions -->\n' + page_kanban + '\n' + page_clients + '\n      \g<1>\g<2>'
        html = re.sub(end_inter_pattern, replacement, html)

        # 5. Add JS and Drawer HTML
        drawer_html = '''
    <!-- Customer Drawer -->
    <div id="customer-drawer" style="position:fixed; top:0; right:-100%; width:400px; height:100vh; background:#fff; z-index:10000; box-shadow:-5px 0 30px rgba(0,0,0,0.1); transition:right 0.3s cubic-bezier(0.4, 0, 0.2, 1); display:flex; flex-direction:column;">
      <div style="padding:24px; border-bottom:1px solid rgba(8,36,50,0.1);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div>
            <h2 id="drawer-name" style="font-size:20px; font-weight:bold; color:#082432; margin-bottom:8px;">Ügyfél neve</h2>
            <div style="color:rgba(8,36,50,0.7); font-size:14px; margin-bottom:4px;" id="drawer-email">email@example.com</div>
            <div style="color:rgba(8,36,50,0.7); font-size:14px;" id="drawer-phone">+36 30 123 4567</div>
          </div>
          <button onclick="closeCustomerDrawer()" style="background:transparent; border:none; cursor:pointer; padding:8px; border-radius:50%; color:rgba(8,36,50,0.5);">✖</button>
        </div>
        <div style="margin-top:20px;">
          <label style="display:block; font-size:12px; font-weight:600; text-transform:uppercase; color:rgba(8,36,50,0.6); margin-bottom:8px;">Státusz</label>
          <select id="drawer-status" style="width:100%; padding:10px; border-radius:8px; border:1px solid rgba(8,36,50,0.1); background:rgba(8,36,50,0.05); color:#082432; font-weight:500; outline:none;">
            <option value="Új">Új</option>
            <option value="Folyamatban">Folyamatban</option>
            <option value="Lezárt">Lezárt</option>
          </select>
        </div>
      </div>
      <div style="flex:1; overflow-y:auto; padding:24px; background:rgba(8,36,50,0.02);">
        <h3 style="font-size:12px; font-weight:600; text-transform:uppercase; color:rgba(8,36,50,0.8); margin-bottom:20px;">Interakciós történet</h3>
        <div id="drawer-timeline" style="display:flex; flex-direction:column; gap:16px;">
          <div style="color:rgba(8,36,50,0.5); font-size:14px;">Még nincsenek adatok...</div>
        </div>
      </div>
    </div>
    <!-- Drawer Overlay -->
    <div id="drawer-overlay" onclick="closeCustomerDrawer()" style="display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(8,36,50,0.3); backdrop-filter:blur(2px); z-index:9999;"></div>
'''

        js_script = '''
// Customer Center JS
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
}

function openCustomerDrawer(clientData) {
    document.getElementById('drawer-overlay').style.display = 'block';
    setTimeout(() => {
        document.getElementById('customer-drawer').style.right = '0';
    }, 10);
    
    if(clientData) {
        document.getElementById('drawer-name').innerText = clientData.name || 'Ismeretlen ügyfél';
        document.getElementById('drawer-email').innerText = clientData.email || '-';
        document.getElementById('drawer-phone').innerText = clientData.phone || '-';
        if(clientData.status) document.getElementById('drawer-status').value = clientData.status;
    }
}

function closeCustomerDrawer() {
    document.getElementById('customer-drawer').style.right = '-100%';
    setTimeout(() => {
        document.getElementById('drawer-overlay').style.display = 'none';
    }, 300);
}

document.addEventListener('click', function(e) {
    if(e.target.closest('.kanban-card') || (e.target.closest('#clients-body tr') && !e.target.closest('.loading-row')) || (e.target.closest('#interactions-flat-body tr') && !e.target.closest('th'))) {
        let name = "Ügyfél";
        let card = e.target.closest('.kanban-card');
        if(card) {
            let strong = card.querySelector('strong');
            if(strong) name = strong.innerText;
        }
        let tr = e.target.closest('#clients-body tr') || e.target.closest('#interactions-flat-body tr');
        if(tr) {
            if(tr.cells && tr.cells[0]) name = tr.cells[0].innerText;
        }
        openCustomerDrawer({ name: name, email: "Kattintásból megnyitva", phone: "-", status: "Folyamatban" });
    }
});
'''
        html = html.replace('</body>', drawer_html + '\n<script>\n' + js_script + '\n</script>\n</body>')

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Successfully refactored admin.html')
    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    main()
