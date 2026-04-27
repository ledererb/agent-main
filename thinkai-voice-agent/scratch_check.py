import sqlite3, json
conn = sqlite3.connect('thinkai.db')
conn.row_factory = sqlite3.Row
clients = conn.execute("SELECT custom_data FROM clients").fetchall()
for c in clients:
    cd = json.loads(c['custom_data'])
    name = cd.get('Név') or cd.get('nev') or cd.get('name')
    print(f"Client: {name}")
    print(f"Has beszelgetes_naplo: {'beszelgetes_naplo' in cd}")
