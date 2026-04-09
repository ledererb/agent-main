import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Re-use the existing get_db from database module
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Quick test of the new logic
def _test():
    db_path = Path(__file__).parent / "thinkai.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    for period in ("week", "month", "year"):
        if period == "week":
            where = "DATE(started_at) >= DATE('now', 'weekday 1', '-7 days')"
        elif period == "month":
            where = "strftime('%Y-%m', started_at) = strftime('%Y-%m', 'now')"
        else:
            where = "started_at >= datetime('now', '-12 months')"
        
        cnt = conn.execute(f"SELECT COUNT(*) FROM sessions WHERE {where}").fetchone()[0]
        print(f"  {period}: {cnt} session")
    
    conn.close()

_test()
