import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            html = f.read()

        # 1. Remove Customer Drawer HTML
        drawer_html_pattern = r'<!-- Customer Drawer -->.*?<!-- Drawer Overlay -->\s*<div id=\"drawer-overlay\" class=\"drawer-overlay\" onclick=\"closeCustomerDrawer\(\)\"></div>'
        html = re.sub(drawer_html_pattern, '', html, flags=re.DOTALL)

        # 2. Insert the new view `#view-client-details` inside `analytics-shell`
        # We need to find the exact place to insert it.
        # It's right before `</div><!-- end view-clients -->` ... wait no, `view-clients` ends, then `analytics-shell` ends.
        # Let's insert it right before `</div><!-- end analytics-shell -->`
        
        client_details_html = '''<!-- CLIENT DETAILS PAGE -->
    <div class="customer-view" id="view-client-details" style="display:none; width: 100%; animation: fadein 0.3s ease;">
      <!-- Back button -->
      <button class="int-toolbar-btn" style="margin-bottom: 20px; border:none; background:transparent; font-weight:600; font-size:14px;" onclick="closeClientDetails()">
        <span style="margin-right:6px;">&larr;</span> Vissza az előző nézethez
      </button>

      <!-- Top Card (Mint gradient) -->
      <div class="cd-top-card">
        <div style="display:flex; align-items:center; gap:20px;">
          <div class="cd-avatar">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--brand-primary);"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          </div>
          <div>
            <h2 id="cd-name" style="margin:0; font-size:24px; font-weight:bold; color:#082432;">Ügyfél Neve</h2>
            <div id="cd-id" style="color:rgba(8,36,50,0.6); font-size:13px; margin-top:2px;">Páciens azonosító: PAC-001234</div>
            
            <div style="display:flex; gap:32px; margin-top:16px; font-size:13px; color:rgba(8,36,50,0.8);">
              <div style="display:flex; align-items:center; gap:8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                <span id="cd-phone">+36 30 123 4567</span>
              </div>
              <div style="display:flex; align-items:center; gap:8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                <span id="cd-email">email@example.com</span>
              </div>
            </div>
            <div style="display:flex; gap:32px; margin-top:8px; font-size:13px; color:rgba(8,36,50,0.8);">
              <div style="display:flex; align-items:center; gap:8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                <span id="cd-address">Ismeretlen cím</span>
              </div>
              <div style="display:flex; align-items:center; gap:8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                <span id="cd-birthdate">Születési dátum: -</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right stats card -->
        <div class="cd-stats-card">
          <div style="font-size:12px; color:rgba(8,36,50,0.6); display:flex; align-items:center; gap:6px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            Utolsó látogatás
          </div>
          <div style="font-size:18px; font-weight:bold; color:#082432; margin-top:4px;" id="cd-last-visit">N/A</div>
          <div style="font-size:12px; font-weight:600; color:rgba(8,36,50,0.8); margin-top:12px;" id="cd-total-interactions">0 összesen interakció</div>
        </div>
      </div>

      <!-- History Table -->
      <div style="margin-top: 32px;">
        <h3 style="font-size:18px; font-weight:bold; margin-bottom:16px;">Interakciók története</h3>
        <div class="int-table-wrapper" style="border-radius:12px; border:1px solid var(--border);">
          <table style="width:100%; border-collapse:collapse; text-align:left;">
            <thead class="int-thead">
              <tr>
                <th style="padding:16px; font-size:11px; font-weight:600; color:#6b8b99; border-bottom:1px solid var(--border);">DÁTUM / IDŐ</th>
                <th style="padding:16px; font-size:11px; font-weight:600; color:#6b8b99; border-bottom:1px solid var(--border);">CSATORNA</th>
                <th style="padding:16px; font-size:11px; font-weight:600; color:#6b8b99; border-bottom:1px solid var(--border);">INTERAKCIÓ TÍPUSA</th>
                <th style="padding:16px; font-size:11px; font-weight:600; color:#6b8b99; border-bottom:1px solid var(--border);">TÉMA</th>
                <th style="padding:16px; font-size:11px; font-weight:600; color:#6b8b99; border-bottom:1px solid var(--border);">ÖSSZEFOGLALÓ</th>
                <th style="padding:16px; font-size:11px; font-weight:600; color:#6b8b99; border-bottom:1px solid var(--border);">EREDMÉNY</th>
              </tr>
            </thead>
            <tbody id="cd-history-body">
              <tr>
                <td colspan="6" style="padding:32px; text-align:center; color:var(--text-muted); font-size:14px;">Még nincsenek adatok...</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
'''
        # Find the last </div><!-- end analytics-shell -->
        parts = html.rpartition('</div><!-- end analytics-shell -->')
        if parts[1]:
            html = parts[0] + client_details_html + '\n' + parts[1] + parts[2]
        else:
            print("Could not find end analytics-shell")
            return

        # 3. Add CSS for Client Details
        css_to_inject = '''
    /* ── Client Details View Styles ────────────────────────────────────────── */
    .cd-top-card {
      background: linear-gradient(100deg, #c5f0ee 0%, #a8e5e3 100%);
      border-radius: 16px;
      padding: 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: relative;
      overflow: hidden;
    }
    body.dark .cd-top-card {
      background: linear-gradient(100deg, #103c44 0%, #0c2b33 100%);
      border: 1px solid rgba(28,238,224,0.1);
    }
    
    .cd-avatar {
      width: 72px; height: 72px; background: #fff; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      border: 3px solid rgba(28,238,224,0.3);
    }
    body.dark .cd-avatar { background: #082432; border-color: #1ceee0; }
    
    .cd-stats-card {
      background: #fff; border-radius: 12px; padding: 16px 24px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center;
      min-width: 180px;
    }
    body.dark .cd-stats-card { background: #082432; box-shadow: 0 4px 12px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.05); }

    body.dark #cd-name { color: #e8edf5 !important; }
    body.dark #cd-id, body.dark #cd-phone, body.dark #cd-email, body.dark #cd-address, body.dark #cd-birthdate { color: #c8d6e5 !important; }
    body.dark #cd-last-visit { color: #e8edf5 !important; }
    body.dark #cd-total-interactions { color: #c8d6e5 !important; }
    /* ───────────────────────────────────────────────────────────────────────── */
'''
        # Replace the old Customer Drawer CSS block with the new one
        drawer_css_pattern = r'/\* ── Ügyfélközpont & Drawer Styles ────────────────────────────────────────── \*/.*?/\* ───────────────────────────────────────────────────────────────────────── \*/'
        html = re.sub(drawer_css_pattern, css_to_inject, html, flags=re.DOTALL)

        # 4. Replace JS functions
        old_js = '''function openCustomerDrawer(clientData) {
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
}'''

        new_js = '''let lastActiveCustomerView = 'interactions';

function openClientDetails(clientData) {
    // Save current active view
    document.querySelectorAll('.customer-view').forEach(el => {
        if(el.style.display !== 'none' && el.id !== 'view-client-details') {
            lastActiveCustomerView = el.id.replace('view-', '');
        }
        el.style.display = 'none';
    });
    
    // Hide view switcher
    const switcher = document.querySelector('.view-switcher-container');
    if(switcher) switcher.style.display = 'none';
    
    // Show details view
    document.getElementById('view-client-details').style.display = 'block';
    
    if(clientData) {
        document.getElementById('cd-name').innerText = clientData.name || 'Ismeretlen ügyfél';
        document.getElementById('cd-email').innerText = clientData.email || 'Nincs megadva email';
        document.getElementById('cd-phone').innerText = clientData.phone || '-';
        
        // Mock data for new design fields
        document.getElementById('cd-id').innerText = `Páciens azonosító: PAC-${Math.floor(100000 + Math.random() * 900000)}`;
        document.getElementById('cd-address').innerText = '1052 Budapest, Városház utca 5.';
        document.getElementById('cd-birthdate').innerText = 'Születési dátum: 1985. 03. 15.';
        
        const dateStr = new Date().toISOString().split('T')[0].replace(/-/g, '. ');
        document.getElementById('cd-last-visit').innerText = dateStr + '.';
        document.getElementById('cd-total-interactions').innerText = Math.floor(Math.random() * 20 + 1) + ' összesen interakció';
        
        // Render dummy history matching the design table
        document.getElementById('cd-history-body').innerHTML = `
            <tr>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">${dateStr}<br><span style="color:var(--text-muted);font-size:11px;">14:35</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">Telefon</td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge badge-info">Bejövő</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge" style="background:var(--bg3);color:var(--text);">Időpontfoglalás</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">Fogászati konzultáció foglalása április 15-re</td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge badge-success">Foglalás történt</span></td>
            </tr>
            <tr>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">${dateStr}<br><span style="color:var(--text-muted);font-size:11px;">10:20</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">Email</td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge badge-info">Bejövő</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge" style="background:var(--bg3);color:var(--text);">Árkérdés</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">Fogpótlási lehetőségek árajánlat kérése</td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge badge-warning">Lezárt</span></td>
            </tr>
        `;
    }
}

function closeClientDetails() {
    document.getElementById('view-client-details').style.display = 'none';
    
    // Show view switcher
    const switcher = document.querySelector('.view-switcher-container');
    if(switcher) switcher.style.display = 'flex';
    
    // Restore last active view
    switchCustomerView(lastActiveCustomerView);
}'''

        html = html.replace(old_js, new_js)

        # 5. Update Kanban Event Listener to use openClientDetails
        kanban_listener_old = '''openCustomerDrawer({ name: name, email: "Kattintásból megnyitva", phone: "-", status: "Folyamatban" });'''
        kanban_listener_new = '''openClientDetails({ name: name, email: "email@example.com", phone: "+36 30 123 4567" });'''
        html = html.replace(kanban_listener_old, kanban_listener_new)

        # 6. Make Clients Table rows clickable
        # In renderClientsTable function, the table body is generated.
        # Let's add onclick to the 'NÉV' column or the whole row.
        clients_table_old = '''return `<td ${i === 0 ? 'style="font-weight:500"' : ''}>${esc(val || '-')}</td>`;'''
        clients_table_new = '''if(i === 2) { // Column index for Name
                return `<td style="font-weight:500; cursor:pointer; color:var(--brand-primary);" onclick="openClientDetails({name: '${esc(val)}'})">${esc(val || '-')}</td>`;
            }
            return `<td ${i === 0 ? 'style="font-weight:500"' : ''}>${esc(val || '-')}</td>`;'''
        html = html.replace(clients_table_old, clients_table_new)

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Successfully refactored client details!")
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    main()
