import sys
import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            html = f.read()

        # 1. Add Ügyfél to thead
        old_thead = """              <tr>
                <th>Dátum / Idő</th>
                <th>Csatorna</th>
                <th>Típus</th>
                <th>Téma</th>
                <th>Összefoglaló</th>
                <th>Eredmény</th>
              </tr>"""
        new_thead = """              <tr>
                <th>Dátum / Idő</th>
                <th>Csatorna</th>
                <th>Ügyfél</th>
                <th>Típus</th>
                <th>Téma</th>
                <th>Összefoglaló</th>
                <th>Eredmény</th>
              </tr>"""
        html = html.replace(old_thead, new_thead)

        # 2. Add client data to buildFlatInteractionRows
        old_build = """      _allInteractionRows.push({
        date: r.created_at || sessionDate,
        channel: channel,
        type: r.type || '-',
        topic: r.topic || '-',
        summary: r.summary || '-',
        result: r.result || '',
      });"""
        new_build = """      _allInteractionRows.push({
        date: r.created_at || sessionDate,
        channel: channel,
        client: s.participant || s.client_name || 'Ismeretlen',
        type: r.type || '-',
        topic: r.topic || '-',
        summary: r.summary || '-',
        result: r.result || '',
      });"""
        html = html.replace(old_build, new_build)

        old_build2 = """      _allInteractionRows.push({
        date: sessionDate,
        channel: channel,
        type: 'session',
        topic: 'Egyéb beszélgetés',
        summary: s.summary || '-',
        result: '',
      });"""
        new_build2 = """      _allInteractionRows.push({
        date: sessionDate,
        channel: channel,
        client: s.participant || s.client_name || 'Ismeretlen',
        type: 'session',
        topic: 'Egyéb beszélgetés',
        summary: s.summary || '-',
        result: '',
      });"""
        html = html.replace(old_build2, new_build2)

        # 3. Add client data to filterInteractionsTable rendering
        # We need to find the specific map block.
        old_map = """      <td style="padding:12px 16px;font-size:13px;color:${txt};white-space:nowrap;">
        <div style="font-weight:500;color:${txtH};">${fmtDt(r.date)}</div>
      </td>
      <td style="padding:12px 16px;font-size:13px;color:${txt};">${esc(r.channel)}</td>
      <td style="padding:12px 16px;">${typeChip(r.type)}</td>"""
      
        new_map = """      <td style="padding:12px 16px;font-size:13px;color:${txt};white-space:nowrap;">
        <div style="font-weight:500;color:${txtH};">${fmtDt(r.date)}</div>
      </td>
      <td style="padding:12px 16px;font-size:13px;color:${txt};">${esc(r.channel)}</td>
      <td style="padding:12px 16px;font-size:13px;font-weight:500;color:${txtH};">${esc(r.client || 'Ismeretlen')}</td>
      <td style="padding:12px 16px;">${typeChip(r.type)}</td>"""
        
        html = html.replace(old_map, new_map)

        # 4. Add sorting logic to filterInteractionsTable
        # Right after `const filtered = _allInteractionRows.filter(...)`
        # Let's find the filter block
        
        old_filter = """  const filtered = _allInteractionRows.filter(r => {
    const matchType = !typeF || r.type.toLowerCase().includes(typeF);
    const matchQ    = !q || [r.channel, r.type, r.topic, r.summary, r.result].join(' ').toLowerCase().includes(q);
    return matchType && matchQ;
  });"""
        
        new_filter = """  const sortVal = (document.getElementById('interaction-sort')?.value || 'date_desc');
  let filtered = _allInteractionRows.filter(r => {
    const matchType = !typeF || r.type.toLowerCase().includes(typeF);
    const matchQ    = !q || [r.channel, r.client, r.type, r.topic, r.summary, r.result].join(' ').toLowerCase().includes(q);
    return matchType && matchQ;
  });
  
  filtered.sort((a, b) => {
      if(sortVal === 'date_desc') return (b.date || '').localeCompare(a.date || '');
      if(sortVal === 'date_asc') return (a.date || '').localeCompare(b.date || '');
      if(sortVal === 'client_asc') return (a.client || '').localeCompare(b.client || '');
      if(sortVal === 'topic_asc') return (a.topic || '').localeCompare(b.topic || '');
      return 0;
  });"""
        html = html.replace(old_filter, new_filter)

        # 5. Change the "Rendezés" dummy button to a real select dropdown matching the style
        old_sort_btn = """            <div style="position:relative; display:inline-block;">
                <button class="int-toolbar-btn" style="gap:6px; display:flex; align-items:center;" title="Rendezés">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline></svg>
                    Rendezés
                </button>
            </div>"""
        
        new_sort_btn = """            <div style="position:relative; display:inline-block;">
                <select id="interaction-sort" onchange="filterInteractionsTable()" class="int-toolbar-btn" style="gap:6px; display:flex; align-items:center; appearance:none; padding-right:32px; background-image: url('data:image/svg+xml;utf8,<svg width=\"14\" height=\"14\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"%236b7280\" stroke-width=\"2\"><polyline points=\"6 9 12 15 18 9\"></polyline></svg>'); background-repeat:no-repeat; background-position:right 8px center; cursor:pointer;">
                    <option value="date_desc">⬇ Legújabb elöl</option>
                    <option value="date_asc">⬆ Legrégebbi elöl</option>
                    <option value="client_asc">A-Z Ügyfél név szerint</option>
                    <option value="topic_asc">A-Z Téma szerint</option>
                </select>
            </div>"""
        html = html.replace(old_sort_btn, new_sort_btn)
        
        # In case the mock interactions-flat-body has colspan="6" loading states, change to 7
        html = html.replace('colspan="6"', 'colspan="7"')

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Updated sorting and client column successfully!")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
