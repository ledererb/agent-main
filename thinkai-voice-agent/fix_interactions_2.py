import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the function body
        pattern = r'function buildFlatInteractionRows\(sessions\)\s*\{\s*// Flatten all interactions from all sessions into one list\s*_allInteractionRows = \[\];\s*sessions\.forEach\(s => \{(.*?)\}\);\s*// Sort newest first'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            new_js = """
    const sessionDate = s.started_at || '';
    const isEmail = s.room_name && s.room_name.toLowerCase().includes('email');
    const channel = isEmail ? 'Email' : (s.channel || 'Telefon');
    const clientName = s.participant || s.client_name || 'Ismeretlen';
    
    (s.interactions || []).forEach(r => {
      _allInteractionRows.push({
        date: r.created_at || sessionDate,
        channel: channel,
        client: clientName,
        type: r.type || '-',
        topic: r.topic || '-',
        summary: r.summary || '-',
        result: r.result || '',
      });
    });
    // If session has no sub-interactions but has a summary, show it as one row
    if (!s.interactions || s.interactions.length === 0) {
      _allInteractionRows.push({
        date: sessionDate,
        channel: channel,
        client: clientName,
        type: 'session',
        topic: '-',
        summary: s.summary || '-',
        result: '',
      });
    }
  """
            replacement = 'function buildFlatInteractionRows(sessions) {\n  // Flatten all interactions from all sessions into one list\n  _allInteractionRows = [];\n  sessions.forEach(s => {' + new_js + '});\n\n  // Sort newest first'
            content = content.replace(match.group(0), replacement)
            print("Mapping fixed!")
        else:
            print("Could not find block")
            
        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(content)

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
