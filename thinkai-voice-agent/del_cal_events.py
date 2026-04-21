import sqlite3
import os

db_path = 'thinkai.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM calendar_events WHERE attendee LIKE '%Nagy Dániel%'")
    conn.execute("DELETE FROM calendar_events WHERE attendee LIKE '%Dániel Nagy%'")
    conn.execute("DELETE FROM calendar_events WHERE attendee_email LIKE '%nagyd965%'")
    conn.commit()
    conn.close()
    print('Deleted remaining events for Nagy Dániel')
