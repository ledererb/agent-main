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
        
        # 2. Find the view switcher container inside page-interactions
        interactions_page = soup.find(id='page-interactions')
        switcher = interactions_page.find('div', class_='view-switcher-container')
        
        # Add the new buttons
        if switcher:
            # We must create buttons as BeautifulSoup tags
            btn1 = soup.new_tag('button', attrs={'class': 'view-btn', 'onclick': "switchCustomerView('emails', this)"})
            btn1.string = "E-mailek"
            btn2 = soup.new_tag('button', attrs={'class': 'view-btn', 'onclick': "switchCustomerView('sessions', this)"})
            btn2.string = "Sessionok"
            switcher.append(btn1)
            switcher.append(btn2)
            
        # 3. Find and move page-emails
        page_emails = soup.find(id='page-emails')
        if page_emails:
            page_emails['class'] = 'customer-view'
            page_emails['id'] = 'view-emails'
            page_emails['style'] = 'display:none;'
            
            # Find insertion point: we want to append it inside page-interactions
            # But specifically BEFORE the closing of analytics-shell or inside analytics-shell
            analytics_shell = interactions_page.find('div', class_='analytics-shell')
            if analytics_shell:
                analytics_shell.append(page_emails)
                
        # 4. Find and move page-sessions
        page_sessions = soup.find(id='page-sessions')
        if page_sessions:
            page_sessions['class'] = 'customer-view'
            page_sessions['id'] = 'view-sessions'
            page_sessions['style'] = 'display:none;'
            
            analytics_shell = interactions_page.find('div', class_='analytics-shell')
            if analytics_shell:
                analytics_shell.append(page_sessions)
                
        # 5. Fix JS switchCustomerView function
        # BeautifulSoup doesn't cleanly parse script tags and lets us regex them without destroying CDATA
        # We will convert back to HTML string first, then use regex for the JS parts
        
        new_html = str(soup)
        
        # We also want to delete the old `<!-- EMAILS PAGE -->` and `<!-- SESSIONS PAGE -->` comments
        new_html = new_html.replace('<!-- EMAILS PAGE -->', '')
        new_html = new_html.replace('<!-- SESSIONS PAGE -->', '')
        
        # Fix JS
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

        # BS4 replaces `/>` with `>` in inputs, and messes up some `<br>` formatting but that's standard HTML5.
        # However, to be perfectly safe, we might just use BS4.
        
        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(new_html)
            
        print("admin.html updated successfully via bs4")
        
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
