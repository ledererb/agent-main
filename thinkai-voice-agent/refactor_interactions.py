import sys

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            html = f.read()

        # Fix 1: Bejövő styling
        html = html.replace('<span class="badge badge-info">Bejövő</span>', '<span style="color:#3b82f6; font-weight:500;">Bejövő</span>')

        # Fix 2: Eredmény badge styling
        html = html.replace('<span class="badge badge-success">Foglalás történt</span>', '<span class="badge badge-blue">Foglalás történt</span>')
        html = html.replace('<span class="badge badge-warning">Lezárt</span>', '<span class="badge badge-gray">Lezárt</span>')

        # Wait, the user mentioned "bejövő interakció legyen kék-kimenő piros".
        # Let's add a 3rd row with a "Kimenő" interaction to show the red color, just in case!
        
        # Let's find the closing tr of the second row:
        row_3 = """
            <tr>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">${dateStr}<br><span style="color:var(--text-muted);font-size:11px;">09:15</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">Telefon</td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span style="color:#ef4444; font-weight:500;">Kimenő</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge" style="background:var(--bg3);color:var(--text);">Visszahívás</span></td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text);">Sikertelen híváskísérlet</td>
              <td style="padding:16px; border-bottom:1px solid var(--border); font-size:13px;"><span class="badge badge-gray">Sikertelen</span></td>
            </tr>"""
        
        # Insert row_3 before the closing </tbody> tag of the string literal
        # Actually it's right before `        `;`
        
        if "badge badge-warning" not in html: # we replaced it above, so search for badge-gray
            html = html.replace('Lezárt</span></td>\n            </tr>', 'Lezárt</span></td>\n            </tr>' + row_3)
            
        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Updated mock interaction table to match design.")

    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    main()
