import sqlite3, json
conn = sqlite3.connect('thinkai.db')
conn.row_factory = sqlite3.Row
clients = conn.execute("SELECT custom_data FROM clients WHERE custom_data LIKE '%Nagy%'").fetchall()
for c in clients:
    cd = json.loads(c['custom_data'])
    name = cd.get('Név') or cd.get('nev') or cd.get('name')
    print(f"Client: {name}")
    print(f"Log: {cd.get('beszelgetes_naplo')}")
