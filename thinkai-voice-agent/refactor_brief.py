import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            html = f.read()

        # 1. Update .badge CSS
        old_badge = '''    .badge {
      display: inline-flex;
      align-items: center;
      padding: 3px 10px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
      white-space: nowrap;
    }'''
        new_badge = '''    .badge {
      display: inline-flex;
      align-items: center;
      padding: 2px 10px; /* equivalent to px-2.5 py-0.5 */
      border-radius: 9999px; /* rounded-full */
      font-size: 11px; /* text-xs */
      font-weight: 500; /* font-medium */
      white-space: nowrap;
    }'''
        html = html.replace(old_badge, new_badge)

        # 2. Update log-modal HTML
        old_log_modal = '''    <div id="log-modal" style="display:none; position:fixed; top:0;left:0;right:0;bottom:0; background:rgba(0,0,0,0.6); z-index:9999; align-items:center; justify-content:center;">
      <div class="login-card" style="width:600px; max-width:90vw;">
        <h3 style="margin-bottom:16px;">Beszélgetés napló</h3>
        <textarea id="log-modal-content" class="settings-textarea" style="min-height:350px; font-family: 'Inter', Arial, sans-serif; font-size:12px; line-height:1.5; margin-bottom: 20px;" readonly></textarea>
        <button class="btn-primary" style="background:var(--bg3);color:var(--text);width:100%" onclick="document.getElementById('log-modal').style.display='none'">Bezárás</button>
      </div>
    </div>'''
        
        new_log_modal = '''    <div id="log-modal" style="display:none; position:fixed; top:0;left:0;right:0;bottom:0; background:rgba(0,0,0,0.6); z-index:9999; align-items:center; justify-content:center;">
      <div class="login-card" style="width:650px; max-width:90vw; padding:0; overflow:hidden; border-radius:16px; border:none; box-shadow: 0 20px 40px rgba(0,0,0,0.2);">
        <!-- Header -->
        <div style="background: linear-gradient(to right, #c5f0ee, #a8e5e3); padding: 20px 24px; border-bottom: 1px solid rgba(0,0,0,0.05);">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <h3 id="log-modal-title-name" style="margin:0 0 4px 0; color:#082432; font-size:18px; font-weight:700;">Ügyfél neve</h3>
                    <div style="display:flex; gap:12px; font-size:12px; color:rgba(8,36,50,0.7); font-weight:500;">
                        <span>📞 <span id="log-modal-channel">Telefon</span></span>
                        <span>•</span>
                        <span id="log-modal-topic">Téma</span>
                        <span>•</span>
                        <span id="log-modal-date">Dátum</span>
                    </div>
                </div>
                <button onclick="document.getElementById('log-modal').style.display='none'" style="background:rgba(8,36,50,0.1); border:none; border-radius:50%; width:28px; height:28px; display:flex; align-items:center; justify-content:center; cursor:pointer; color:#082432; transition:background 0.2s;">
                    ✕
                </button>
            </div>
        </div>
        <!-- Content -->
        <div style="padding: 24px; background:var(--card);">
            <textarea id="log-modal-content" class="settings-textarea" style="min-height:300px; font-family: 'Inter', Arial, sans-serif; font-size:13px; line-height:1.6; margin-bottom: 0; border:none; box-shadow:none; background:var(--bg); border-radius:8px; padding:16px;" readonly></textarea>
        </div>
        <!-- Footer -->
        <div style="padding: 16px 24px; background:var(--bg3); border-top: 1px solid var(--border); display:flex; justify-content:flex-end; gap:12px;">
            <button class="btn-primary" style="background:transparent; color:var(--text-muted); border:1px solid var(--border);" onclick="document.getElementById('log-modal').style.display='none'">Bezárás</button>
            <button class="btn-primary" style="opacity:0.5; cursor:not-allowed;" disabled title="Hamarosan elérhető">▶ Interakció lejátszása</button>
        </div>
      </div>
    </div>'''
        html = html.replace(old_log_modal, new_log_modal)

        # 3. Update Interakciók toolbar
        old_toolbar = '''          <div style="display:flex;gap:10px;align-items:center;">
            <input id="interaction-search" type="text" placeholder="🔍 Keresés..." oninput="filterInteractionsTable()" class="int-toolbar-input">
            <select id="interaction-type-filter" onchange="filterInteractionsTable()" class="int-toolbar-select">
              <option value="">Minden típus</option>
              <option value="foglalás">Foglalás</option>
              <option value="email">Email</option>
              <option value="feladat">Feladat</option>
              <option value="kérdés">Kérdés</option>
            </select>
            <button onclick="loadInteractions()" class="int-toolbar-btn">🔄 Frissítés</button>
          </div>'''
        
        new_toolbar = '''          <div style="display:flex;gap:10px;align-items:center;">
            <input id="interaction-search" type="text" placeholder="🔍 Keresés..." oninput="filterInteractionsTable()" class="int-toolbar-input">
            <select id="interaction-type-filter" onchange="filterInteractionsTable()" class="int-toolbar-select" style="display:none;">
              <option value="">Minden típus</option>
            </select>
            
            <div style="position:relative; display:inline-block;">
                <button class="int-toolbar-btn" style="gap:6px; display:flex; align-items:center;" title="Szűrés">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>
                    Szűrés
                </button>
            </div>
            
            <div style="position:relative; display:inline-block;">
                <button class="int-toolbar-btn" style="gap:6px; display:flex; align-items:center;" title="Rendezés">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline></svg>
                    Rendezés
                </button>
            </div>
            
            <div style="position:relative; display:inline-block;">
                <button class="int-toolbar-btn" style="gap:6px; display:flex; align-items:center;" title="Oszlopok">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
                    Oszlopok
                </button>
            </div>

            <button onclick="loadInteractions()" class="int-toolbar-btn" style="margin-left:8px;">🔄 Frissítés</button>
          </div>'''
        html = html.replace(old_toolbar, new_toolbar)

        # 4. Replace inline text in cd-history-body to badges
        html = html.replace('<span style="color:#3b82f6; font-weight:500;">Bejövő</span>', '<span class="badge badge-blue">Bejövő</span>')
        html = html.replace('<span style="color:#ef4444; font-weight:500;">Kimenő</span>', '<span class="badge badge-purple">Kimenő</span>')

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Done!")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
