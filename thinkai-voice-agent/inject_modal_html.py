import re

with open('admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

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

html = html.replace('<!-- Log Modal HTML -->', modal_html + '\n<!-- Log Modal HTML -->')

with open('admin.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Modal HTML injected.")
