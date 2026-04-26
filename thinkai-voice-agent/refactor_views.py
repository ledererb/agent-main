import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Extract EMAILS PAGE
        emails_match = re.search(r'<!-- EMAILS PAGE -->\s*<div class="page" id="page-emails">(.*?)</div>\s*<!-- SESSIONS PAGE -->', content, re.DOTALL)
        if not emails_match:
            print("Could not find emails page")
            return
        emails_inner = emails_match.group(1)
        
        # 2. Extract SESSIONS PAGE
        sessions_match = re.search(r'<!-- SESSIONS PAGE -->\s*<div class="page" id="page-sessions">(.*?)</div>\s*<!-- SETTINGS PAGE -->', content, re.DOTALL)
        if not sessions_match:
            print("Could not find sessions page")
            return
        sessions_inner = sessions_match.group(1)

        # 3. Remove them from their original locations
        content = re.sub(r'<!-- EMAILS PAGE -->\s*<div class="page" id="page-emails">.*?</div>\s*<!-- SESSIONS PAGE -->\s*<div class="page" id="page-sessions">.*?</div>\s*<!-- SETTINGS PAGE -->', '<!-- SETTINGS PAGE -->', content, flags=re.DOTALL)

        # 4. Prepare new customer-view blocks
        new_views = f"""
        <!-- EMAILS VIEW -->
        <div class="customer-view" id="view-emails" style="display:none;">{emails_inner}</div>
        
        <!-- SESSIONS VIEW -->
        <div class="customer-view" id="view-sessions" style="display:none;">{sessions_inner}</div>
        """

        # 5. Insert new_views before </div><!-- end analytics-shell -->
        content = content.replace("</div><!-- end analytics-shell -->", new_views + "\n</div><!-- end analytics-shell -->")

        # 6. Remove sidebar buttons
        sidebar_to_remove = """    <button class="nav-item" onclick="showPage('emails')" id="nav-emails">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 4h16a2 2 0 012 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6a2 2 0 012-2zm0 0l8 7 8-7"/></svg>
      <span>Emailek</span>
    </button>
    <button class="nav-item" onclick="showPage('sessions')" id="nav-sessions">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
      <span>Sessionök</span>
    </button>"""
        # The file might have "Sessionk" due to encoding, so regex remove:
        content = re.sub(r'<button class="nav-item" onclick="showPage\(\'emails\'\)" id="nav-emails">.*?</button>\s*<button class="nav-item" onclick="showPage\(\'sessions\'\)" id="nav-sessions">.*?</button>', '', content, flags=re.DOTALL)

        # 7. Add view-switcher buttons
        old_switcher = """<button class="view-btn" onclick="switchCustomerView('clients', this)">Ügyfelek adatbázisa</button>
        </div>"""
        
        # We need regex to match it properly because of Ügyfelek encoding issues
        switcher_match = re.search(r'<button class="view-btn" onclick="switchCustomerView\(\'clients\', this\)">.*?</button>\s*</div>', content)
        if switcher_match:
            new_switcher = switcher_match.group(0).replace('</div>', """          <button class="view-btn" onclick="switchCustomerView('emails', this)">E-mailek</button>
          <button class="view-btn" onclick="switchCustomerView('sessions', this)">Sessionok</button>
        </div>""")
            content = content.replace(switcher_match.group(0), new_switcher)
        else:
            print("Could not find view switcher")
            return

        # 8. Update switchCustomerView JS
        old_switch_js = """    if(viewId === 'clients') loadClientsTable();
    if(viewId === 'interactions') loadInteractions();
}"""
        new_switch_js = """    if(viewId === 'clients') loadClientsTable();
    if(viewId === 'interactions') loadInteractions();
    if(viewId === 'emails') loadEmails();
    if(viewId === 'sessions') loadSessions();
}"""
        content = content.replace(old_switch_js, new_switch_js)

        # 9. Update showPage JS
        old_showpage = """  if (page === 'calendar')     loadCalendar();
  if (page === 'emails')       loadEmails();
  if (page === 'sessions')     loadSessions();
  if (page === 'settings')     loadSettings();"""
        new_showpage = """  if (page === 'calendar')     loadCalendar();
  if (page === 'settings')     loadSettings();"""
        content = content.replace(old_showpage, new_showpage)

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(content)

        print("Refactored admin.html successfully!")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
