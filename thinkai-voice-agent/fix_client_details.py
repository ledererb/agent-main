import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            content = f.read()

        old_dummy_render = """        // Render dummy history matching the design table
        document.getElementById('cd-history-body').innerHTML = `
            <tr>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">${dateStr}<br><span style="color:var(--text-muted);font-size:11px;">14:35</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">Telefon</td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge badge-blue">Bejv</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge" style="background:var(--bg3);color:var(--text);">Idpontfoglals</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">Fogszati konzultci foglalsa prilis 15-re</td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge badge-green">Foglals trtnt</span></td>
            </tr>
            <tr>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">${dateStr}<br><span style="color:var(--text-muted);font-size:11px;">10:20</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">Email</td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge badge-blue">Bejv</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge" style="background:var(--bg3);color:var(--text);">rkrds</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">Fogptlsi lehetsgek rajnlat krse</td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge" style="background:var(--bg3);color:var(--text);">Lezrt</span></td>
            </tr>
            <tr>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">${dateStr}<br><span style="color:var(--text-muted);font-size:11px;">08:15</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">Telefon</td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge badge-purple">Kimen</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge" style="background:var(--bg3);color:var(--text);">Visszahvs</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">Sikertelen hvsksrlet</td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge" style="background:var(--bg3);color:var(--text);">Sikertelen</span></td>
            </tr>
        `;"""

        # Replace unicode errors in script by reading the file and replacing carefully
        content = re.sub(
            r"// Render dummy history matching the design table[\s\S]*?</tr>\s*`;",
            r"""// Render real history matching the design table
        document.getElementById('cd-history-body').innerHTML = `<tr><td colspan="6" style="text-align:center;padding:20px;"><div class="spinner"></div>Betöltés...</td></tr>`;
        
        authFetch('/admin/api/sessions/summary?limit=500')
          .then(res => res.json())
          .then(data => {
            const sessions = data.sessions || [];
            let clientInteractions = [];
            sessions.forEach(s => {
               const cName = (s.participant || s.client_name || '').toLowerCase();
               const isMatch = (clientData.name && cName === clientData.name.toLowerCase()) || 
                               (clientData.email && s.session_id.toLowerCase().includes(clientData.email.toLowerCase()));
               if (isMatch) {
                   (s.interactions || []).forEach(r => {
                       clientInteractions.push({
                           date: r.created_at || s.started_at,
                           channel: s.room_name && s.room_name.includes('Email') ? 'Email' : 'Telefon',
                           type: r.type || '-',
                           topic: r.topic || '-',
                           summary: r.summary || '-',
                           result: r.result || ''
                       });
                   });
               }
            });
            
            clientInteractions.sort((a, b) => (b.date || '').localeCompare(a.date || ''));
            
            document.getElementById('cd-total-interactions').innerText = clientInteractions.length + ' összesen interakció';
            
            if (clientInteractions.length === 0) {
               document.getElementById('cd-history-body').innerHTML = `<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--text-muted);">Nincs rögzített interakció</td></tr>`;
               return;
            }
            
            document.getElementById('cd-history-body').innerHTML = clientInteractions.map(r => {
               let dStr = '-';
               let tStr = '-';
               if (r.date) {
                   const pt = r.date.replace('T', ' ').split(' ');
                   dStr = pt[0].replace(/-/g, '. ') + '.';
                   tStr = pt[1] ? pt[1].substring(0,5) : '';
               }
               return `
                <tr>
                  <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">${dStr}<br><span style="color:var(--text-muted);font-size:11px;">${tStr}</span></td>
                  <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">${esc(r.channel)}</td>
                  <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;">${typeChip(r.type)}</td>
                  <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge" style="background:var(--bg3);color:var(--text);">${esc(r.topic)}</span></td>
                  <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">${esc(r.summary)}</td>
                  <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;">${resultBadge(r.result)}</td>
                </tr>
               `;
            }).join('');
          })
          .catch(err => {
              document.getElementById('cd-history-body').innerHTML = `<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--red);">Hiba a betöltés során</td></tr>`;
          });""",
            content
        )

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(content)

        print("admin.html updated successfully!")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
