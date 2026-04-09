"""Inject settings JS into admin.html before the last </script>."""

new_js = r"""

// ── SETTINGS ───────────────────────────────────────────────────────────────
const BH_DAYS = [
  { key: 'monday',    label: 'Hétfő' },
  { key: 'tuesday',   label: 'Kedd' },
  { key: 'wednesday', label: 'Szerda' },
  { key: 'thursday',  label: 'Csütörtök' },
  { key: 'friday',    label: 'Péntek' },
  { key: 'saturday',  label: 'Szombat' },
  { key: 'sunday',    label: 'Vasárnap' },
];

let currentKnowledgeFormat = 'json';

async function loadSettings() {
  try {
    const res  = await authFetch('/admin/api/settings');
    const data = await res.json();
    await loadCartesiaVoices(data.voice_id);
    renderBhTable(data.business_hours || {});
    currentKnowledgeFormat = data.knowledge_format || 'json';
    document.getElementById('setting-knowledge').value = data.knowledge_content || '';
    updateFmtButtons();
    const toneEl = document.getElementById('setting-tone');
    toneEl.value = data.tone || 'professional_friendly';
    document.getElementById('setting-tone-custom').value = data.tone_custom || '';
    onToneChange();
  } catch(e) { console.error('Settings load error:', e); }
}

async function loadCartesiaVoices(selectedId) {
  const sel    = document.getElementById('setting-voice');
  const status = document.getElementById('voice-load-status');
  sel.innerHTML = '<option value="">Betöltés...</option>';
  status.textContent = '';
  try {
    const res    = await authFetch('/admin/api/cartesia/voices');
    const voices = await res.json();
    voices.sort((a, b) => {
      const aHu = (a.language || '').startsWith('hu');
      const bHu = (b.language || '').startsWith('hu');
      if (aHu && !bHu) return -1;
      if (!aHu && bHu) return 1;
      return (a.name || '').localeCompare(b.name || '', 'hu');
    });
    sel.innerHTML = voices.map(v => {
      const lang = v.language ? ` [${v.language}]` : '';
      const s    = v.id === selectedId ? ' selected' : '';
      return `<option value="${v.id}"${s}>${v.name}${lang}</option>`;
    }).join('');
    status.textContent = `${voices.length} hang betöltve`;
  } catch(e) {
    sel.innerHTML = '<option value="">Nem sikerült betölteni</option>';
    status.textContent = 'Hiba: ' + e.message;
  }
}

function renderBhTable(bh) {
  const tbody = document.getElementById('bh-tbody');
  tbody.innerHTML = BH_DAYS.map(d => {
    const day = bh[d.key] || { open: '09:00', close: '18:00', enabled: false };
    const dis = day.enabled ? '' : ' disabled';
    return `
      <tr>
        <td class="bh-day-label">${d.label}</td>
        <td><input type="time" class="bh-time" id="bh-${d.key}-open"  value="${day.open || ''}"${dis}></td>
        <td><input type="time" class="bh-time" id="bh-${d.key}-close" value="${day.close || ''}"${dis}></td>
        <td>
          <label class="toggle">
            <input type="checkbox" id="bh-${d.key}-enabled"
              ${day.enabled ? 'checked' : ''}
              onchange="onBhToggle('${d.key}')">
            <span class="toggle-slider"></span>
          </label>
        </td>
      </tr>`;
  }).join('');
}

function onBhToggle(dayKey) {
  const enabled = document.getElementById(`bh-${dayKey}-enabled`).checked;
  document.getElementById(`bh-${dayKey}-open`).disabled  = !enabled;
  document.getElementById(`bh-${dayKey}-close`).disabled = !enabled;
}

function collectBhData() {
  const result = {};
  BH_DAYS.forEach(d => {
    const enabled = document.getElementById(`bh-${d.key}-enabled`).checked;
    result[d.key] = {
      open:    document.getElementById(`bh-${d.key}-open`).value  || null,
      close:   document.getElementById(`bh-${d.key}-close`).value || null,
      enabled,
    };
  });
  return result;
}

function switchKnowledgeFormat(fmt) {
  if (fmt === currentKnowledgeFormat) return;
  if (!confirm(`Formátum váltás → ${fmt.toUpperCase()}?\nA jelenlegi tartalom törlődik — ments el előszőr!`)) return;
  currentKnowledgeFormat = fmt;
  document.getElementById('setting-knowledge').value = fmt === 'json' ? '{}' : '';
  updateFmtButtons();
}

function updateFmtButtons() {
  document.getElementById('fmt-json-btn').classList.toggle('active', currentKnowledgeFormat === 'json');
  document.getElementById('fmt-md-btn').classList.toggle('active',   currentKnowledgeFormat === 'md');
  document.getElementById('fmt-hint').textContent = currentKnowledgeFormat === 'json'
    ? 'Struktúrált JSON formátum — kulcs: érték párok'
    : 'Markdown formátum — ## fejlécekkel, sima szöveg';
  document.getElementById('setting-knowledge').style.fontFamily =
    currentKnowledgeFormat === 'json' ? "'Courier New', monospace" : "'Inter', sans-serif";
}

function onToneChange() {
  const val = document.getElementById('setting-tone').value;
  document.getElementById('tone-custom-row').style.display = val === 'custom' ? 'block' : 'none';
}

async function saveSettings() {
  const btn = document.getElementById('save-settings-btn');
  btn.disabled = true;
  btn.textContent = 'Mentés...';
  try {
    const payload = {
      voice_id:          document.getElementById('setting-voice').value,
      tone:              document.getElementById('setting-tone').value,
      tone_custom:       document.getElementById('setting-tone-custom').value,
      knowledge_format:  currentKnowledgeFormat,
      knowledge_content: document.getElementById('setting-knowledge').value,
      business_hours:    collectBhData(),
    };
    const res  = await authFetch('/admin/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Hiba');
    document.getElementById('restart-banner').classList.add('visible');
    btn.textContent = '✓ Elmentve';
    setTimeout(() => { btn.disabled = false; btn.innerHTML = '&#128190; Mentés'; }, 2500);
  } catch(e) {
    alert('Hiba a mentés során: ' + e.message);
    btn.disabled = false;
    btn.innerHTML = '&#128190; Mentés';
  }
}
"""

with open('admin.html', encoding='utf-8') as f:
    content = f.read()

idx = content.rfind('</script>')
if idx == -1:
    print("ERROR: </script> not found!")
else:
    new_content = content[:idx] + new_js + '</script>' + content[idx+9:]
    with open('admin.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"OK — JS injected at char {idx}, total lines: {new_content.count(chr(10))}")
