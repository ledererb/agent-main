import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Remove sidebar buttons
        sidebar_buttons = r"""    <button class="nav-item" onclick="showPage\('emails'\)" id="nav-emails">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 4h16a2 2 0 012 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6a2 2 0 012-2zm0 0l8 7 8-7"/></svg>
      <span>Emailek</span>
    </button>
    <button class="nav-item" onclick="showPage\('sessions'\)" id="nav-sessions">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
      <span>Sessionö?k</span>
    </button>"""
        # Using regex to catch Sessionök/Sessionk
        content = re.sub(r'    <button class="nav-item" onclick="showPage\(\'emails\'\)" id="nav-emails">.*?</button>\s*<button class="nav-item" onclick="showPage\(\'sessions\'\)" id="nav-sessions">.*?</button>', '', content, flags=re.DOTALL)

        # 2. Extract EMAILS page
        # It's bounded by <div class="page" id="page-emails"> and <!-- SESSIONS PAGE -->
        emails_pattern = r'(<div class="page" id="page-emails">.*?)<!-- SESSIONS PAGE -->'
        emails_match = re.search(emails_pattern, content, re.DOTALL)
        if not emails_match:
            print("Could not find emails page")
            return
        emails_html = emails_match.group(1).strip()
        # Remove from document
        content = content.replace(emails_html, '')
        
        # 3. Extract SESSIONS page
        # It's bounded by <div class="page" id="page-sessions"> and <!-- SETTINGS PAGE -->
        sessions_pattern = r'(<div class="page" id="page-sessions">.*?)<!-- SETTINGS PAGE -->'
        sessions_match = re.search(sessions_pattern, content, re.DOTALL)
        if not sessions_match:
            print("Could not find sessions page")
            return
        sessions_html = sessions_match.group(1).strip()
        # Remove from document
        content = content.replace(sessions_html, '')

        # 4. Process the extracted blocks
        emails_html = emails_html.replace('<div class="page" id="page-emails">', '<div class="customer-view" id="view-emails" style="display:none;">')
        sessions_html = sessions_html.replace('<div class="page" id="page-sessions">', '<div class="customer-view" id="view-sessions" style="display:none;">')

        # 5. Find insertion point: inside page-interactions, at the end of analytics-shell
        insertion_target = "</div><!-- end analytics-shell -->"
        new_views = f"\n\n<!-- EMAILS VIEW -->\n{emails_html}\n\n<!-- SESSIONS VIEW -->\n{sessions_html}\n\n"
        content = content.replace(insertion_target, new_views + insertion_target)

        # 6. Add buttons to view-switcher
        switcher_pattern = r'(<button class="view-btn" onclick="switchCustomerView\(\'clients\', this\)">.*?</button>\s*)</div>'
        switcher_match = re.search(switcher_pattern, content)
        if switcher_match:
            new_buttons = switcher_match.group(1) + """          <button class="view-btn" onclick="switchCustomerView('emails', this)">E-mailek</button>
          <button class="view-btn" onclick="switchCustomerView('sessions', this)">Sessionok</button>
        </div>"""
            content = content.replace(switcher_match.group(0), new_buttons)
        else:
            print("Could not find switcher")
            return
            
        # 7. Clean up JS
        old_switch_js = """    if(viewId === 'clients') loadClientsTable();
    if(viewId === 'interactions') loadInteractions();
}"""
        new_switch_js = """    if(viewId === 'clients') loadClientsTable();
    if(viewId === 'interactions') loadInteractions();
    if(viewId === 'emails') loadEmails();
    if(viewId === 'sessions') loadSessions();
}"""
        content = content.replace(old_switch_js, new_switch_js)

        # Update showPage JS
        old_showpage = """  if (page === 'calendar')     loadCalendar();
  if (page === 'emails')       loadEmails();
  if (page === 'sessions')     loadSessions();
  if (page === 'settings')     loadSettings();"""
        new_showpage = """  if (page === 'calendar')     loadCalendar();
  if (page === 'settings')     loadSettings();"""
        content = content.replace(old_showpage, new_showpage)

        # Cleanup stray comments
        content = content.replace('<!-- EMAILS PAGE -->', '')
        content = content.replace('<!-- SESSIONS PAGE -->', '')

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(content)

        print("Refactored admin.html successfully!")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
