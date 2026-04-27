import re

with open('admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

# I need to find the block starting with <!-- PRAXISINFORMÁCIÓ TAB --> and ending with <!-- end szabalyok content -->
praxis_szabalyok_pattern = re.compile(r'(<!-- PRAXISINFORMÁCIÓ TAB -->.*?<!-- end szabalyok content -->\n)', re.DOTALL)
match = praxis_szabalyok_pattern.search(html)
if match:
    ps_content = match.group(1)
    # Remove it from current location
    html = html.replace(ps_content, '')
    
    # Remove the wrongly placed </div><!-- end settings-view-agent --> and any extra </div>
    # The structure right now is:
    # </div>
    # </div>
    # </div><!-- end settings-view-agent -->
    
    # We want it to be:
    # </div>
    # </div><!-- end settings-view-agent -->
    # <praxis and szabalyok>
    # </div> <!-- closes #page-settings -->
    
    # Find the end of workflow textarea
    workflow_end_pattern = re.compile(r'(<textarea.*?id="setting-workflow".*?</textarea>\s*</div>)\s*</div>\s*</div><!-- end settings-view-agent -->', re.DOTALL)
    
    replacement = r'\1\n</div><!-- end settings-view-agent -->\n' + ps_content + '</div>\n'
    
    html = workflow_end_pattern.sub(replacement, html)
    
    with open('admin.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("DOM fixed.")
else:
    print("Could not find praxis and szabalyok content.")
