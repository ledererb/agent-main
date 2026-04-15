import sqlite3
conn = sqlite3.connect("C:/Users/dani pc xd/Desktop/agent-main/thinkai-voice-agent/thinkai.db")
fields = conn.execute("SELECT id, name FROM client_fields").fetchall()
print(fields)
conn.close()
