import sqlite3, json
conn = sqlite3.connect('thinkai.db')
conn.row_factory = sqlite3.Row
clients = conn.execute("SELECT id, custom_data FROM clients").fetchall()
for c in clients:
    cd = json.loads(c['custom_data'])
    name = cd.get('name') or cd.get('nev') or cd.get('Név')
    if name == 'Dániel Nagy':
        print(f"ID: {c['id']}, Log exists: {'beszelgetes_naplo' in cd}")
