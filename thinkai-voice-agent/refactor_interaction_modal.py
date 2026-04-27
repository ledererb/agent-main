import re

with open('admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add modal HTML
modal_html = """
<!-- INTERACTION SUMMARY MODAL -->
<div id="ism-modal" class="ism-modal">
  <div class="ism-content">
    <div class="ism-header">
      <button onclick="document.getElementById('ism-modal').style.display='none'" class="ism-close">&times;</button>
      <h2 class="ism-title">Interakciós összefoglaló</h2>
      <div class="ism-meta">
        <span id="ism-client"></span> • <span id="ism-channel"></span> • <span id="ism-date"></span>
      </div>
    </div>
    <div class="ism-body">
      <div style="margin-bottom:24px;">
        <h3 class="ism-section-title">Összefoglaló</h3>
        <p id="ism-summary" class="ism-summary-text"></p>
      </div>
      <div class="ism-result-box">
        <h3 class="ism-result-title">Eredmény</h3>
        <div id="ism-result-grid" class="ism-result-grid"></div>
        <div style="margin-top:20px; display:flex; align-items:center; gap:8px;">
          <span class="ism-result-label" style="margin:0;">Státusz:</span>
          <span id="ism-result-badge"></span>
        </div>
      </div>
      <div id="ism-transcript-section" style="margin-top:24px; display:none;">
        <h3 class="ism-section-title">Beszélgetés napló</h3>
        <textarea id="ism-transcript" class="ism-textarea" readonly></textarea>
      </div>
    </div>
  </div>
</div>
"""

html = html.replace('<!-- Log Modal -->', modal_html + '\n<!-- Log Modal -->')

# 2. Add CSS
css_content = """
    /* Interaction Summary Modal */
    .ism-modal { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(8,36,50,0.6); z-index:9999; align-items:center; justify-content:center; }
    .ism-content { background:#fff; border-radius:16px; width:700px; max-width:90%; overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,0.2); display:flex; flex-direction:column; max-height:90vh; }
    .ism-header { background:#1ceee0; padding:24px 32px; position:relative; }
    .ism-close { position:absolute; top:20px; right:24px; background:transparent; border:none; color:#082432; font-size:24px; cursor:pointer; opacity:0.7; }
    .ism-close:hover { opacity:1; }
    .ism-title { margin:0 0 8px 0; color:#082432; font-size:22px; font-weight:700; font-family:'Inter', Arial, sans-serif; }
    .ism-meta { color:#082432; font-size:13px; font-weight:600; opacity:0.9; }
    .ism-body { padding:32px; overflow-y:auto; flex:1; }
    .ism-section-title { font-size:12px; color:#6b8b99; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px; font-weight:700; }
    .ism-summary-text { font-size:15px; color:#0a1f2e; line-height:1.6; margin:0; }
    .ism-result-box { background:#f0fdfa; border:1px solid #99f6e4; border-radius:12px; padding:24px; margin-bottom:24px; }
    .ism-result-title { font-size:12px; color:#0f766e; text-transform:uppercase; letter-spacing:1px; margin-bottom:16px; font-weight:700; }
    .ism-result-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
    .ism-result-label { font-size:12px; color:#0f766e; opacity:0.8; margin-bottom:4px; font-weight:600; }
    .ism-result-val { font-size:14px; font-weight:600; color:#0f766e; }
    .ism-textarea { width:100%; height:200px; background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px; padding:16px; font-family:'Inter', Arial, sans-serif; font-size:13px; color:#374151; line-height:1.5; resize:vertical; }
    
    .summary-link { cursor: pointer; color: #082432; font-weight: 600; transition: color 0.2s; }
    .summary-link:hover { color: #1ceee0; }

    body.dark .ism-content { background:#0b1e2b; }
    body.dark .ism-summary-text { color:#e8edf5; }
    body.dark .ism-result-box { background:rgba(28,238,224,0.05); border-color:rgba(28,238,224,0.2); }
    body.dark .ism-result-title { color:#1ceee0; }
    body.dark .ism-result-label { color:#6b8b99; }
    body.dark .ism-result-val { color:#e8edf5; }
    body.dark .ism-textarea { background:#0d2538; border-color:#1a3548; color:#c8d6e5; }
    body.dark .summary-link { color: #1ceee0; }
    body.dark .summary-link:hover { color: #4cf2e6; }
"""

html = html.replace('</style>', css_content + '\n  </style>')

# 3. Add JS function
js_content = """
async function openInteractionSummaryModal(idx) {
    const r = window._filteredInteractionRows[idx];
    if(!r) return;
    
    document.getElementById('ism-client').textContent = r.client || 'Ismeretlen';
    document.getElementById('ism-channel').textContent = r.channel || 'Telefon';
    document.getElementById('ism-date').textContent = r.date ? fmtDt(r.date) : '';
    document.getElementById('ism-summary').textContent = r.summary || 'Nincs összefoglaló';
    document.getElementById('ism-result-badge').innerHTML = resultBadge(r.result);
    
    // Clear dynamic fields
    const grid = document.getElementById('ism-result-grid');
    grid.innerHTML = '';
    
    document.getElementById('ism-transcript-section').style.display = 'none';
    document.getElementById('ism-modal').style.display = 'flex';
    
    // Fetch client to get structured result and transcript
    try {
        const res = await authFetch('/admin/api/clients');
        const data = await res.json();
        const clients = data.clients || [];
        const client = clients.find(c => c.custom_data && (c.custom_data.nev === r.client || c.custom_data.name === r.client || c.custom_data['név'] === r.client));
        
        if (client && client.custom_data) {
            const cd = client.custom_data;
            const fieldsToShow = [
                {id: 'idopont', label: 'Befoglalt időpont'},
                {id: 'szolgaltatas', label: 'Szolgáltatás'},
                {id: 'orvos', label: 'Orvos'},
                {id: 'prioritas', label: 'Prioritás'}
            ];
            
            fieldsToShow.forEach(f => {
                let val = cd[f.id] || cd[f.label] || cd[f.id.toLowerCase()] || cd[f.label.toLowerCase()];
                if(val) {
                    grid.innerHTML += `<div><div class="ism-result-label">${f.label}</div><div class="ism-result-val">${esc(val)}</div></div>`;
                }
            });
            
            if (cd.beszelgetes_naplo) {
                document.getElementById('ism-transcript').value = cd.beszelgetes_naplo;
                document.getElementById('ism-transcript-section').style.display = 'block';
            }
        }
    } catch(e) {
        console.error('Error fetching client details for modal:', e);
    }
}
"""

html = html.replace('function filterInteractionsTable() {', js_content + '\nfunction filterInteractionsTable() {')

# 4. Modify filterInteractionsTable to store filtered globally and add click event
html = html.replace('let filtered = _allInteractionRows.filter', 'window._filteredInteractionRows = _allInteractionRows.filter')
html = html.replace('filtered.sort(', 'window._filteredInteractionRows.sort(')
html = html.replace('if (!filtered.length)', 'if (!window._filteredInteractionRows.length)')
html = html.replace('tbody.innerHTML = filtered.map', 'tbody.innerHTML = window._filteredInteractionRows.map')
html = html.replace('countEl.textContent = `${filtered.length}', 'countEl.textContent = `${window._filteredInteractionRows.length}')

# 5. Make the summary cell clickable with class="summary-link"
td_old_pattern = re.compile(r'<td style="padding:12px 16px;font-size:13px;color:\$\{txtM\};max-width:340px;">\s*<div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="\$\{esc\(r\.summary\)\}">(.*?)</div>\s*</td>', re.DOTALL)

td_new = r"""<td style="padding:12px 16px;font-size:13px;color:${txtM};max-width:340px;">
          <div onclick="openInteractionSummaryModal(${i})" class="summary-link" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="Összefoglaló és beszélgetés napló megtekintése">${esc(r.summary)}</div>
        </td>"""

html = td_old_pattern.sub(td_new, html)

with open('admin.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated admin.html successfully.")
