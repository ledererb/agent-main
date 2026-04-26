import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            content = f.read()

        old_js = """  sessions.forEach(s => {
    const sessionDate = s.started_at || '';
    const channel = s.channel || 'Telefon';
    (s.interactions || []).forEach(r => {
      _allInteractionRows.push({
        date: r.created_at || sessionDate,
        channel: channel,
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
        type: 'session',
        topic: '-',
        summary: s.summary || '-',
        result: '',
      });
    }
  });"""
        
        new_js = """  sessions.forEach(s => {
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
  });"""
        
        if old_js in content:
            content = content.replace(old_js, new_js)
            with open('admin.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("Mapping fixed!")
        else:
            print("Could not find block")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
