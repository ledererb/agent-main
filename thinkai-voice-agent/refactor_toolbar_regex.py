import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            html = f.read()

        # We will use regex to find the toolbar block and replace it
        # Block starts with: <input id="interaction-search"
        # Ends with: </button>\n          </div>
        
        pattern = re.compile(r"<input id=\"interaction-search\".*?</select>\s*<button onclick=\"loadInteractions.*?</div>", re.DOTALL)
        
        new_toolbar = """<input id="interaction-search" type="text" placeholder="🔍 Keresés..." oninput="filterInteractionsTable()" class="int-toolbar-input">
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
                <select id="interaction-sort" onchange="filterInteractionsTable()" class="int-toolbar-btn" style="gap:6px; display:flex; align-items:center; appearance:none; padding-right:32px; background-image: url('data:image/svg+xml;utf8,<svg width=\\"14\\" height=\\"14\\" viewBox=\\"0 0 24 24\\" fill=\\"none\\" stroke=\\"%236b7280\\" stroke-width=\\"2\\"><polyline points=\\"6 9 12 15 18 9\\"></polyline></svg>'); background-repeat:no-repeat; background-position:right 8px center; cursor:pointer;">
                    <option value="date_desc">⬇ Legújabb elöl</option>
                    <option value="date_asc">⬆ Legrégebbi elöl</option>
                    <option value="client_asc">A-Z Ügyfél név szerint</option>
                    <option value="topic_asc">A-Z Téma szerint</option>
                </select>
            </div>
            
            <div style="position:relative; display:inline-block;">
                <button class="int-toolbar-btn" style="gap:6px; display:flex; align-items:center;" title="Oszlopok">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
                    Oszlopok
                </button>
            </div>

            <button onclick="loadInteractions()" class="int-toolbar-btn" style="margin-left:8px;">🔄 Frissítés</button>
          </div>"""
        
        new_html = pattern.sub(new_toolbar, html)
        
        if new_html != html:
            with open('admin.html', 'w', encoding='utf-8') as f:
                f.write(new_html)
            print("Toolbar replaced successfully!")
        else:
            print("Could not match toolbar pattern!")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
