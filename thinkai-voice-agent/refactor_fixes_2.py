import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            html = f.read()

        # 1. Fix cd-avatar SVG color
        html = html.replace('style="color:var(--brand-primary);"', 'style="color:var(--accent);"')

        # 2. Fix empty field logic in openClientDetails
        old_details = '''        document.getElementById('cd-email').innerText = clientData.email || '';
        document.getElementById('cd-phone').innerText = clientData.phone || '';
        
        // Optional real data fields
        document.getElementById('cd-id').innerText = clientData.id ? `Azonosító: ${clientData.id}` : `Páciens azonosító: PAC-${Math.floor(100000 + Math.random() * 900000)}`;
        document.getElementById('cd-address').innerText = clientData.address || '';
        document.getElementById('cd-birthdate').innerText = clientData.birthdate ? `Születési dátum: ${clientData.birthdate}` : '';'''
        
        new_details = '''        const emailEl = document.getElementById('cd-email');
        emailEl.innerText = clientData.email || '';
        emailEl.parentElement.style.display = clientData.email ? 'flex' : 'none';
        
        const phoneEl = document.getElementById('cd-phone');
        phoneEl.innerText = clientData.phone || '';
        phoneEl.parentElement.style.display = clientData.phone ? 'flex' : 'none';
        
        // Optional real data fields
        document.getElementById('cd-id').innerText = clientData.id ? `Azonosító: ${clientData.id}` : `Páciens azonosító: PAC-${Math.floor(100000 + Math.random() * 900000)}`;
        
        const addressEl = document.getElementById('cd-address');
        addressEl.innerText = clientData.address || '';
        addressEl.parentElement.style.display = clientData.address ? 'flex' : 'none';
        
        const birthdateEl = document.getElementById('cd-birthdate');
        birthdateEl.innerText = clientData.birthdate ? `Születési dátum: ${clientData.birthdate}` : '';
        birthdateEl.parentElement.style.display = clientData.birthdate ? 'flex' : 'none';'''
        
        if old_details in html:
            html = html.replace(old_details, new_details)
            print("Successfully updated empty field logic.")
        else:
            print("Could not find old_details string!")

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Successfully applied fixes!")
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    main()
