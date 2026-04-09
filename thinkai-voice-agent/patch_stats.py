"""Patch database.py: replace get_stats with period-filtered version."""
import re

with open('database.py', encoding='utf-8') as f:
    content = f.read()

new_func = '''def get_stats(period: str = "month") -> dict:
    """Return aggregated stats filtered by period.

    period: 'week'  = current calendar week (Mon-Sun)
            'month' = current calendar month
            'year'  = last 12 months
    """
    if period == "week":
        sess_where  = "DATE(started_at) >= DATE('now', 'weekday 1', '-7 days')"
        inter_where = "DATE(created_at)  >= DATE('now', 'weekday 1', '-7 days')"
        email_where = "DATE(sent_at)     >= DATE('now', 'weekday 1', '-7 days')"
        cal_where   = "DATE(start_dt)    >= DATE('now', 'weekday 1', '-7 days')"
    elif period == "month":
        sess_where  = "strftime('%Y-%m', started_at) = strftime('%Y-%m', 'now')"
        inter_where = "strftime('%Y-%m', created_at)  = strftime('%Y-%m', 'now')"
        email_where = "strftime('%Y-%m', sent_at)     = strftime('%Y-%m', 'now')"
        cal_where   = "strftime('%Y-%m', start_dt)    = strftime('%Y-%m', 'now')"
    else:  # year
        sess_where  = "started_at >= datetime('now', '-12 months')"
        inter_where = "created_at  >= datetime('now', '-12 months')"
        email_where = "sent_at     >= datetime('now', '-12 months')"
        cal_where   = "start_dt    >= datetime('now', '-12 months')"

    with get_db() as conn:
        total_sessions = conn.execute(
            f"SELECT COUNT(*) FROM sessions WHERE {sess_where}"
        ).fetchone()[0]

        total_interactions = conn.execute(
            f"SELECT COUNT(*) FROM interactions WHERE {inter_where}"
        ).fetchone()[0]

        total_emails = conn.execute(
            f"SELECT COUNT(*) FROM email_logs WHERE {email_where}"
        ).fetchone()[0]

        total_bookings = conn.execute(
            f"SELECT COUNT(*) FROM calendar_events WHERE {cal_where}"
        ).fetchone()[0]

        open_tasks = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE completed = 0"
        ).fetchone()[0]

        type_rows = conn.execute(
            f"SELECT type, COUNT(*) as cnt FROM interactions WHERE {inter_where} GROUP BY type ORDER BY cnt DESC"
        ).fetchall()

        if period == "year":
            chart_rows = conn.execute(
                f"""SELECT strftime('%Y-%m', started_at) as day, COUNT(*) as cnt
                    FROM sessions WHERE {sess_where}
                    GROUP BY day ORDER BY day ASC"""
            ).fetchall()
        else:
            chart_rows = conn.execute(
                f"""SELECT DATE(started_at) as day, COUNT(*) as cnt
                    FROM sessions WHERE {sess_where}
                    GROUP BY day ORDER BY day ASC"""
            ).fetchall()

        avg_dur = conn.execute(
            f"SELECT AVG(duration_seconds) FROM sessions WHERE duration_seconds IS NOT NULL AND {sess_where}"
        ).fetchone()[0]

    return {
        "total_sessions":       total_sessions,
        "total_interactions":   total_interactions,
        "total_emails":         total_emails,
        "total_bookings":       total_bookings,
        "open_tasks":           open_tasks,
        "avg_session_duration": round(avg_dur or 0),
        "interactions_by_type": [{"type": r["type"], "count": r["cnt"]} for r in type_rows],
        "sessions_per_day":     [{"day": r["day"],  "count": r["cnt"]} for r in chart_rows],
    }
'''

# Replace the entire get_stats function
pattern = r'def get_stats\(period.*?(?=\ndef |\nclass |\Z)'
new_content = re.sub(pattern, new_func.strip() + '\n', content, flags=re.DOTALL)

if 'def get_stats' not in new_content:
    print("ERROR: replacement failed!")
else:
    with open('database.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("OK: get_stats updated")
    # Quick verify
    import sqlite3
    conn = sqlite3.connect('thinkai.db')
    conn.row_factory = sqlite3.Row
    for p, w in [("week", "DATE(started_at) >= DATE('now', 'weekday 1', '-7 days')"),
                 ("month", "strftime('%Y-%m', started_at) = strftime('%Y-%m', 'now')"),
                 ("year",  "started_at >= datetime('now', '-12 months')")]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM sessions WHERE {w}").fetchone()[0]
        print(f"  {p}: {cnt} session")
    conn.close()
