"""Patch admin.html renderStats with trend indicators — encoding-safe approach."""
from pathlib import Path

f = Path(__file__).parent / "admin.html"
content = f.read_bytes().decode("utf-8")

# Find the function bounds
start_marker = "function renderStats(data) {"
end_marker = "  // Sessions per day chart"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)
assert start_idx != -1, "start_marker not found"
assert end_idx != -1, "end_marker not found"

new_render = (
    "function renderStats(data) {\r\n"
    "  const grid = document.getElementById('stats-grid');\r\n"
    "  const period = document.getElementById('stats-days').value;\r\n"
    "  const prefix = { week: 'Heti', month: 'Havi', year: '\u00c9vi' }[period] || '';\r\n"
    "  const prevLabel = { week: 'el\u0151z\u0151 h\u00e9thez', month: 'el\u0151z\u0151 h\u00f3naphoz', year: 'el\u0151z\u0151 \u00e9vhez' }[period] || '';\r\n"
    "  const prev = data.previous_period || {};\r\n"
    "\r\n"
    "  function trendHtml(current, previous) {\r\n"
    "    if (previous === undefined || previous === null) return '';\r\n"
    "    const cur = Number(current) || 0;\r\n"
    "    const pre = Number(previous) || 0;\r\n"
    "    if (pre === 0 && cur === 0) return '';\r\n"
    "    if (pre === 0) return '<div class=\"stat-trend up\">\u25b2 \u00daj adat</div>';\r\n"
    "    const diff = cur - pre;\r\n"
    "    const pct  = Math.round(Math.abs(diff / pre) * 100);\r\n"
    "    const sign = diff >= 0 ? '+' : '\u2212';\r\n"
    "    const dir  = diff >= 0 ? 'up' : 'down';\r\n"
    "    const arrow = diff >= 0 ? '\u25b2' : '\u25bc';\r\n"
    "    return `<div class=\"stat-trend ${dir}\">${arrow} ${sign}${pct}% <span style=\"font-weight:400;color:var(--text-muted);font-size:10px;\">${prevLabel} k\u00e9pest</span></div>`;\r\n"
    "  }\r\n"
    "\r\n"
    "  const stats = [\r\n"
    "    { label: `${prefix} session`,           value: data.total_sessions,       prev: prev.total_sessions,       icon: '\U0001f399\ufe0f', cls: 'teal',   page: 'sessions' },\r\n"
    "    { label: `${prefix} interakci\u00f3`,        value: data.total_interactions,   prev: prev.total_interactions,   icon: '\u26a1',  cls: 'blue',   page: 'interactions' },\r\n"
    "    { label: `${prefix} foglal\u00e1s`,          value: data.total_bookings,       prev: prev.total_bookings,       icon: '\U0001f4c5',  cls: 'green',  page: 'calendar' },\r\n"
    "    { label: `${prefix} email`,              value: data.total_emails,          prev: prev.total_emails,         icon: '\u2709\ufe0f',  cls: 'purple', page: 'emails' },\r\n"
    "    { label: 'Nyitott feladatok',            value: data.open_tasks,            prev: null,                      icon: '\u2713',   cls: 'yellow', page: 'sessions' },\r\n"
    "    { label: `${prefix} \u00e1tl. session (mp)`, value: data.avg_session_duration,  prev: prev.avg_session_duration, icon: '\u23f1\ufe0f',  cls: 'orange', page: 'sessions' },\r\n"
    "  ];\r\n"
    "\r\n"
    "  grid.innerHTML = stats.map(s => `\r\n"
    "    <div class=\"stat-card\" onclick=\"showPage('${s.page}')\" style=\"cursor:pointer;\" title=\"${s.label}\">\r\n"
    "      <div class=\"stat-icon ${s.cls}\">${s.icon}</div>\r\n"
    "      <div class=\"stat-label\">${s.label}</div>\r\n"
    "      <div class=\"stat-value\">${s.value ?? 0}</div>\r\n"
    "      ${trendHtml(s.value, s.prev)}\r\n"
    "    </div>\r\n"
    "  `).join('');\r\n"
    "\r\n"
    "  // Sessions per day chart"
)

content = content[:start_idx] + new_render + content[end_idx + len("  // Sessions per day chart"):]
f.write_bytes(content.encode("utf-8"))
print("OK — admin.html renderStats patched with trend indicators")
