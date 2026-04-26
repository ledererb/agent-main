import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            html = f.read()

        # 1. Fix the icons color in dark mode by replacing the inline style with a class
        html = html.replace('color:rgba(8,36,50,0.8);', 'color:inherit; opacity:0.8;')
        
        # 2. Fix openClientDetails empty fields
        old_details = '''if(clientData) {
        document.getElementById('cd-name').innerText = clientData.name || 'Ismeretlen ügyfél';
        document.getElementById('cd-email').innerText = clientData.email || 'Nincs megadva email';
        document.getElementById('cd-phone').innerText = clientData.phone || '-';'''
        
        new_details = '''if(clientData) {
        document.getElementById('cd-name').innerText = clientData.name || 'Ismeretlen ügyfél';
        document.getElementById('cd-email').innerText = clientData.email || '';
        document.getElementById('cd-phone').innerText = clientData.phone || '';'''
        html = html.replace(old_details, new_details)

        # 3. Fix the renderClientsTable name column
        # Find the block where i === 2 was added
        old_table = '''if(i === 2) { // Column index for Name
                return `<td style="font-weight:500; cursor:pointer; color:var(--brand-primary);" onclick="openClientDetails({name: '${esc(val)}'})">${esc(val || '-')}</td>`;
            }'''
            
        new_table = '''if(f.id === 'nev' || f.name.toLowerCase() === 'név') { // Column index for Name
                return `<td style="font-weight:500; cursor:pointer; color:var(--brand-primary);" onclick="openClientDetails({name: '${esc(val)}', email: '${esc(customObj.email || '')}', phone: '${esc(customObj.telefonszam || customObj.phone || customObj.telefon || '')}'})">${esc(val || '-')}</td>`;
            }'''
            
        html = html.replace(old_table, new_table)
        
        # 4. Make sure Kanban also passes email and phone if available
        # Wait, kanban already passes static email/phone. Let's fix Kanban to pass real email/phone from the card if possible.
        # Currently Kanban cards have email and phone in the DOM!
        # The DOM looks like:
        # <strong>Kis József</strong>
        # <div><i class="..."></i> email</div>
        # <div><i class="..."></i> phone</div>
        # The JS: `const name = card.querySelector('strong').innerText;`
        # We can extract email and phone from the DOM!
        old_kanban_js = '''const name = card.querySelector('strong').innerText;
        openClientDetails({ name: name, email: "email@example.com", phone: "+36 30 123 4567" });'''
        
        new_kanban_js = '''const name = card.querySelector('strong').innerText;
        const infoDivs = card.querySelectorAll('div[style*="font-size:12px"]');
        let email = '';
        let phone = '';
        infoDivs.forEach(d => {
            if(d.innerText.includes('@')) email = d.innerText.trim();
            else if(d.innerText.trim().length > 0) phone = d.innerText.trim();
        });
        openClientDetails({ name: name, email: email, phone: phone });'''
        
        html = html.replace(old_kanban_js, new_kanban_js)

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Successfully applied fixes!")
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    main()
