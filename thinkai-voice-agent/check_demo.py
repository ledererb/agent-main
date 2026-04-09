import sqlite3
conn = sqlite3.connect('thinkai.db')
rows = conn.execute("SELECT DATE(started_at) d, COUNT(*) cnt FROM sessions WHERE participant='demo' GROUP BY d ORDER BY d").fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]:2d} {'#' * r[1]}")
print(f"Total: {sum(r[1] for r in rows)}")
conn.close()
