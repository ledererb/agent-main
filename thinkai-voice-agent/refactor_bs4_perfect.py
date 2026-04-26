import sys
from bs4 import BeautifulSoup

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            html = f.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Remove sidebar buttons
        nav_emails = soup.find(id='nav-emails')
        nav_sessions = soup.find(id='nav-sessions')
        if nav_emails: nav_emails.decompose()
        if nav_sessions: nav_sessions.decompose()
        
        # 2. Add the new buttons to the view switcher container inside page-interactions
        interactions_page = soup.find(id='page-interactions')
        switcher = interactions_page.find('div', class_='view-switcher-container')
        
        if switcher:
            # We want to reorder them as well!
            # Desired order: Ügyfelek adatbázisa, Kanban, Interakciós lista, E-mailek, Sessionok
            switcher.clear()
            
            btn1 = soup.new_tag('button', attrs={'class': 'view-btn active', 'onclick': "switchCustomerView('clients', this)"})
            btn1.string = "Ügyfelek adatbázisa"
            
            btn2 = soup.new_tag('button', attrs={'class': 'view-btn', 'onclick': "switchCustomerView('kanban', this)"})
            btn2.string = "Kanban"
            
            btn3 = soup.new_tag('button', attrs={'class': 'view-btn', 'onclick': "switchCustomerView('interactions', this)"})
            btn3.string = "Interakciós lista"
            
            btn4 = soup.new_tag('button', attrs={'class': 'view-btn', 'onclick': "switchCustomerView('emails', this)"})
            btn4.string = "E-mailek"
            
            btn5 = soup.new_tag('button', attrs={'class': 'view-btn', 'onclick': "switchCustomerView('sessions', this)"})
            btn5.string = "Sessionok"
            
            switcher.append(btn1)
            switcher.append(btn2)
            switcher.append(btn3)
            switcher.append(btn4)
            switcher.append(btn5)
            
        # 3. Modify visibility for interactions and clients
        view_interactions = soup.find(id='view-interactions')
        if view_interactions:
            view_interactions['style'] = 'display:none;'
            
        view_clients = soup.find(id='view-clients')
        if view_clients:
            view_clients['style'] = 'display:block;'

        # 4. Find and move page-emails
        page_emails = soup.find(id='page-emails')
        if page_emails:
            page_emails['class'] = 'customer-view'
            page_emails['id'] = 'view-emails'
            page_emails['style'] = 'display:none;'
            
            # Find insertion point: we want to append it inside page-interactions > analytics-shell
            analytics_shell = interactions_page.find('div', class_='analytics-shell')
            if analytics_shell:
                analytics_shell.append(page_emails)
                
        # 5. Find and move page-sessions
        page_sessions = soup.find(id='page-sessions')
        if page_sessions:
            page_sessions['class'] = 'customer-view'
            page_sessions['id'] = 'view-sessions'
            page_sessions['style'] = 'display:none;'
            
            analytics_shell = interactions_page.find('div', class_='analytics-shell')
            if analytics_shell:
                analytics_shell.append(page_sessions)
                
        # Convert back to string
        new_html = str(soup)
        
        # We also want to delete the old `<!-- EMAILS PAGE -->` and `<!-- SESSIONS PAGE -->` comments
        new_html = new_html.replace('<!-- EMAILS PAGE -->', '')
        new_html = new_html.replace('<!-- SESSIONS PAGE -->', '')
        
        # 6. Fix JS
        old_switch_js = """    if(viewId === 'clients') loadClientsTable();
    if(viewId === 'interactions') loadInteractions();
}"""
        new_switch_js = """    if(viewId === 'clients') loadClientsTable();
    if(viewId === 'interactions') loadInteractions();
    if(viewId === 'emails') loadEmails();
    if(viewId === 'sessions') loadSessions();
}"""
        new_html = new_html.replace(old_switch_js, new_switch_js)
        
        # Update showPage JS
        old_showpage = """  if (page === 'calendar')     loadCalendar();
  if (page === 'emails')       loadEmails();
  if (page === 'sessions')     loadSessions();
  if (page === 'settings')     loadSettings();"""
        new_showpage = """  if (page === 'calendar')     loadCalendar();
  if (page === 'settings')     loadSettings();"""
        new_html = new_html.replace(old_showpage, new_showpage)

        # Update lastActiveCustomerView default
        new_html = new_html.replace("let lastActiveCustomerView = 'interactions';", "let lastActiveCustomerView = 'clients';")
        
        # Fix enterApp
        new_html = new_html.replace("  loadInteractions();\n}", "  loadClientsTable();\n}")
        
        # BS4 can sometimes change <input ... > to <input ... /> or similar.
        # It's generally harmless.
        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(new_html)
            
        print("admin.html updated successfully via bs4")
        
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
