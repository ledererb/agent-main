import database as db
db.init_db()

# Delete duplicate calendar events - keep only first occurrence of each title+start_dt
with db.get_db() as conn:
    rows = conn.execute('SELECT id, title, start_dt FROM calendar_events ORDER BY id ASC').fetchall()
    print(f'Before cleanup: {len(rows)} events')

    seen = set()
    to_delete = []
    for r in rows:
        key = (r['title'], r['start_dt'])
        if key in seen:
            to_delete.append(r['id'])
        else:
            seen.add(key)

    if to_delete:
        placeholders = ','.join(['?'] * len(to_delete))
        conn.execute(f'DELETE FROM calendar_events WHERE id IN ({placeholders})', to_delete)
        print(f'Deleted {len(to_delete)} duplicates')

    remaining = conn.execute('SELECT COUNT(*) FROM calendar_events').fetchone()[0]
    print(f'After cleanup: {remaining} events')

# Mark migration as done
with db.get_db() as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT)')
    conn.execute("INSERT OR REPLACE INTO _meta (key, value) VALUES ('json_migrated', '2026-04-09')")
    print('Migration flag set - no more duplicates on restart')
