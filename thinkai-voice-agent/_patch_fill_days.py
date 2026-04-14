"""Patch database.py: fill missing days with 0 in sessions_per_day."""
from pathlib import Path
from datetime import date, timedelta
import calendar as cal_mod

f = Path(__file__).parent / "database.py"
content = f.read_text(encoding="utf-8")

# We replace the return dict's sessions_per_day line and add gap-fill logic before the return
old_return = (
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

new_return = (
        "    # ── Fill missing days with 0 so the chart has no gaps ───────────────\n"
        "    raw_days = {r[\"day\"]: r[\"cnt\"] for r in chart_rows}\n"
        "    today = datetime.utcnow().date()\n"
        "    if period == \"week\":\n"
        "        # current Mon..today\n"
        "        week_start = today - timedelta(days=today.weekday())\n"
        "        all_keys = [(week_start + timedelta(days=i)).isoformat() for i in range((today - week_start).days + 1)]\n"
        "    elif period == \"month\":\n"
        "        # 1st of month..today\n"
        "        month_start = today.replace(day=1)\n"
        "        all_keys = [(month_start + timedelta(days=i)).isoformat() for i in range((today - month_start).days + 1)]\n"
        "    else:  # year — monthly buckets\n"
        "        all_keys = []\n"
        "        d = today.replace(day=1)\n"
        "        for _ in range(12):\n"
        "            all_keys.insert(0, d.strftime(\"%Y-%m\"))\n"
        "            # go back one month\n"
        "            d = (d - timedelta(days=1)).replace(day=1)\n"
        "    filled_days = [{\"day\": k, \"count\": raw_days.get(k, 0)} for k in all_keys]\n"
        "\n"
        "    return {\n"
        "        \"total_sessions\":       total_sessions,\n"
        "        \"total_interactions\":   total_interactions,\n"
        "        \"total_emails\":         total_emails,\n"
        "        \"total_bookings\":       total_bookings,\n"
        "        \"open_tasks\":           open_tasks,\n"
        "        \"avg_session_duration\": round(avg_dur or 0),\n"
        "        \"interactions_by_type\": [{\"type\": r[\"type\"], \"count\": r[\"cnt\"]} for r in type_rows],\n"
        "        \"sessions_per_day\":     filled_days,\n"
        "        \"previous_period\": {\n"
        "            \"total_sessions\":       prev_total_sessions,\n"
        "            \"total_interactions\":   prev_total_interactions,\n"
        "            \"total_emails\":         prev_total_emails,\n"
        "            \"total_bookings\":       prev_total_bookings,\n"
        "            \"avg_session_duration\": round(prev_avg_dur or 0),\n"
        "        },\n"
        "    }\n"
)

assert old_return in content, "ERROR: return block not found!"
content = content.replace(old_return, new_return, 1)
f.write_text(content, encoding="utf-8")
print("OK — sessions_per_day gap-fill patched")
