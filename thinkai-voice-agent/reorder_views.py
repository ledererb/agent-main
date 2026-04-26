import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            content = f.read()

        old_buttons = r"""<div class="view-switcher-container">
          <button class="view-btn active" onclick="switchCustomerView\('interactions', this\)">.*?</button>
          <button class="view-btn" onclick="switchCustomerView\('kanban', this\)">Kanban</button>
          <button class="view-btn" onclick="switchCustomerView\('clients', this\)">.*?</button>
                  <button class="view-btn" onclick="switchCustomerView\('emails', this\)">E-mailek</button>
          <button class="view-btn" onclick="switchCustomerView\('sessions', this\)">Sessionok</button>
        </div>"""
        
        # In actual HTML, there's whitespace differences, let's just use string replace on the whole block
        # Or even better, a regex that captures everything inside the container
        container_pattern = r'(<div class="view-switcher-container">)(.*?)(</div>)'
        
        match = re.search(container_pattern, content, re.DOTALL)
        if match:
            new_buttons = """
          <button class="view-btn active" onclick="switchCustomerView('clients', this)">Ügyfelek adatbázisa</button>
          <button class="view-btn" onclick="switchCustomerView('kanban', this)">Kanban</button>
          <button class="view-btn" onclick="switchCustomerView('interactions', this)">Interakciós lista</button>
          <button class="view-btn" onclick="switchCustomerView('emails', this)">E-mailek</button>
          <button class="view-btn" onclick="switchCustomerView('sessions', this)">Sessionok</button>
        """
            content = content.replace(match.group(0), match.group(1) + new_buttons + match.group(3))
        else:
            print("Could not find view-switcher-container")
            return
            
        # Change default active view variable
        content = content.replace("let lastActiveCustomerView = 'interactions';", "let lastActiveCustomerView = 'clients';")
        
        # Change default visible div for the views
        # view-interactions is block, view-clients is none
        content = content.replace('<div class="customer-view" id="view-interactions" style="display:block;">', '<div class="customer-view" id="view-interactions" style="display:none;">')
        content = content.replace('<div class="customer-view" id="view-clients" style="display:none;">', '<div class="customer-view" id="view-clients" style="display:block;">')

        # Also, in enterApp(), it loads loadInteractions(). Since clients is default, it should also loadClientsTable()
        content = content.replace("  loadInteractions();\n}", "  loadClientsTable();\n}")

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(content)

        print("Reordered successfully!")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
