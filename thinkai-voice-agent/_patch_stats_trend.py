"""Patch database.py: extend get_stats with previous_period block."""
from pathlib import Path

db_file = Path(__file__).parent / "database.py"
content = db_file.read_text(encoding="utf-8")

# ── Find & replace the get_stats function body ────────────────────────────────
# We inject the previous-period WHERE clauses and extra queries at the right spots.

# 1. Add prev_* WHERE clauses after each period's current WHERE clauses
old_week_block = (
    "    if period == \"week\":\n"
    "        sess_where  = \"DATE(started_at) >= DATE('now', 'weekday 1', '-7 days')\"\n"
    "        inter_where = \"DATE(created_at)  >= DATE('now', 'weekday 1', '-7 days')\"\n"
    "        email_where = \"DATE(sent_at)     >= DATE('now', 'weekday 1', '-7 days')\"\n"
    "        cal_where   = \"DATE(start_dt)    >= DATE('now', 'weekday 1', '-7 days')\"\n"
    "    elif period == \"month\":\n"
    "        sess_where  = \"strftime('%Y-%m', started_at) = strftime('%Y-%m', 'now')\"\n"
    "        inter_where = \"strftime('%Y-%m', created_at)  = strftime('%Y-%m', 'now')\"\n"
    "        email_where = \"strftime('%Y-%m', sent_at)     = strftime('%Y-%m', 'now')\"\n"
    "        cal_where   = \"strftime('%Y-%m', start_dt)    = strftime('%Y-%m', 'now')\"\n"
    "    else:  # year\n"
    "        sess_where  = \"started_at >= datetime('now', '-12 months')\"\n"
    "        inter_where = \"created_at  >= datetime('now', '-12 months')\"\n"
    "        email_where = \"sent_at     >= datetime('now', '-12 months')\"\n"
    "        cal_where   = \"start_dt    >= datetime('now', '-12 months')\"\n"
)

new_week_block = (
    "    if period == \"week\":\n"
    "        sess_where  = \"DATE(started_at) >= DATE('now', 'weekday 1', '-7 days')\"\n"
    "        inter_where = \"DATE(created_at)  >= DATE('now', 'weekday 1', '-7 days')\"\n"
    "        email_where = \"DATE(sent_at)     >= DATE('now', 'weekday 1', '-7 days')\"\n"
    "        cal_where   = \"DATE(start_dt)    >= DATE('now', 'weekday 1', '-7 days')\"\n"
    "        prev_sess   = \"DATE(started_at) >= DATE('now','weekday 1','-14 days') AND DATE(started_at) < DATE('now','weekday 1','-7 days')\"\n"
    "        prev_inter  = \"DATE(created_at)  >= DATE('now','weekday 1','-14 days') AND DATE(created_at)  < DATE('now','weekday 1','-7 days')\"\n"
    "        prev_email  = \"DATE(sent_at)     >= DATE('now','weekday 1','-14 days') AND DATE(sent_at)     < DATE('now','weekday 1','-7 days')\"\n"
    "        prev_cal    = \"DATE(start_dt)    >= DATE('now','weekday 1','-14 days') AND DATE(start_dt)    < DATE('now','weekday 1','-7 days')\"\n"
    "    elif period == \"month\":\n"
    "        sess_where  = \"strftime('%Y-%m', started_at) = strftime('%Y-%m', 'now')\"\n"
    "        inter_where = \"strftime('%Y-%m', created_at)  = strftime('%Y-%m', 'now')\"\n"
    "        email_where = \"strftime('%Y-%m', sent_at)     = strftime('%Y-%m', 'now')\"\n"
    "        cal_where   = \"strftime('%Y-%m', start_dt)    = strftime('%Y-%m', 'now')\"\n"
    "        prev_sess   = \"strftime('%Y-%m', started_at) = strftime('%Y-%m', 'now', '-1 month')\"\n"
    "        prev_inter  = \"strftime('%Y-%m', created_at)  = strftime('%Y-%m', 'now', '-1 month')\"\n"
    "        prev_email  = \"strftime('%Y-%m', sent_at)     = strftime('%Y-%m', 'now', '-1 month')\"\n"
    "        prev_cal    = \"strftime('%Y-%m', start_dt)    = strftime('%Y-%m', 'now', '-1 month')\"\n"
    "    else:  # year\n"
    "        sess_where  = \"started_at >= datetime('now', '-12 months')\"\n"
    "        inter_where = \"created_at  >= datetime('now', '-12 months')\"\n"
    "        email_where = \"sent_at     >= datetime('now', '-12 months')\"\n"
    "        cal_where   = \"start_dt    >= datetime('now', '-12 months')\"\n"
    "        prev_sess   = \"started_at >= datetime('now','-24 months') AND started_at < datetime('now','-12 months')\"\n"
    "        prev_inter  = \"created_at  >= datetime('now','-24 months') AND created_at  < datetime('now','-12 months')\"\n"
    "        prev_email  = \"sent_at     >= datetime('now','-24 months') AND sent_at     < datetime('now','-12 months')\"\n"
    "        prev_cal    = \"start_dt    >= datetime('now','-24 months') AND start_dt    < datetime('now','-12 months')\"\n"
)

assert old_week_block in content, "ERROR: old_week_block not found!"
content = content.replace(old_week_block, new_week_block, 1)

# 2. Add prev queries before the return statement and extend the return dict
old_avg = (
    "        avg_dur = conn.execute(\n"
    "            f\"SELECT AVG(duration_seconds) FROM sessions WHERE duration_seconds IS NOT NULL AND {sess_where}\"\n"
    "        ).fetchone()[0]\n"
    "\n"
    "    return {\n"
    "        \"total_sessions\":       total_sessions,\n"
    "        \"total_interactions\":   total_interactions,\n"
    "        \"total_emails\":         total_emails,\n"
    "        \"total_bookings\":       total_bookings,\n"
    "        \"open_tasks\":           open_tasks,\n"
    "        \"avg_session_duration\": round(avg_dur or 0),\n"
    "        \"interactions_by_type\": [{\"type\": r[\"type\"], \"count\": r[\"cnt\"]} for r in type_rows],\n"
    "        \"sessions_per_day\":     [{\"day\": r[\"day\"],  \"count\": r[\"cnt\"]} for r in chart_rows],\n"
    "    }\n"
)

new_avg = (
    "        avg_dur = conn.execute(\n"
    "            f\"SELECT AVG(duration_seconds) FROM sessions WHERE duration_seconds IS NOT NULL AND {sess_where}\"\n"
    "        ).fetchone()[0]\n"
    "\n"
    "        # ── Previous period totals (for trend indicators) ─────────────────\n"
    "        prev_total_sessions = conn.execute(\n"
    "            f\"SELECT COUNT(*) FROM sessions WHERE {prev_sess}\"\n"
    "        ).fetchone()[0]\n"
    "        prev_total_interactions = conn.execute(\n"
    "            f\"SELECT COUNT(*) FROM interactions WHERE {prev_inter}\"\n"
    "        ).fetchone()[0]\n"
    "        prev_total_emails = conn.execute(\n"
    "            f\"SELECT COUNT(*) FROM email_logs WHERE {prev_email}\"\n"
    "        ).fetchone()[0]\n"
    "        prev_total_bookings = conn.execute(\n"
    "            f\"SELECT COUNT(*) FROM calendar_events WHERE {prev_cal}\"\n"
    "        ).fetchone()[0]\n"
    "        prev_avg_dur = conn.execute(\n"
    "            f\"SELECT AVG(duration_seconds) FROM sessions WHERE duration_seconds IS NOT NULL AND {prev_sess}\"\n"
    "        ).fetchone()[0]\n"
    "\n"
    "    return {\n"
    "        \"total_sessions\":       total_sessions,\n"
    "        \"total_interactions\":   total_interactions,\n"
    "        \"total_emails\":         total_emails,\n"
    "        \"total_bookings\":       total_bookings,\n"
    "        \"open_tasks\":           open_tasks,\n"
    "        \"avg_session_duration\": round(avg_dur or 0),\n"
    "        \"interactions_by_type\": [{\"type\": r[\"type\"], \"count\": r[\"cnt\"]} for r in type_rows],\n"
    "        \"sessions_per_day\":     [{\"day\": r[\"day\"],  \"count\": r[\"cnt\"]} for r in chart_rows],\n"
    "        \"previous_period\": {\n"
    "            \"total_sessions\":       prev_total_sessions,\n"
    "            \"total_interactions\":   prev_total_interactions,\n"
    "            \"total_emails\":         prev_total_emails,\n"
    "            \"total_bookings\":       prev_total_bookings,\n"
    "            \"avg_session_duration\": round(prev_avg_dur or 0),\n"
    "        },\n"
    "    }\n"
)

assert old_avg in content, "ERROR: old_avg block not found!"
content = content.replace(old_avg, new_avg, 1)

db_file.write_text(content, encoding="utf-8")
print("OK — database.py patched successfully")
