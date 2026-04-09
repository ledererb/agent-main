import sqlite3
from datetime import datetime, timedelta, timezone
import random
import math

conn = sqlite3.connect('thinkai.db')

# Torlom a regi demo adatokat
conn.execute("DELETE FROM sessions WHERE participant='demo'")
conn.commit()

now = datetime.now(timezone.utc).replace(tzinfo=None)

def insert_day(day, count, prefix):
    for i in range(count):
        start_h = random.randint(8, 18)
        start_m = random.randint(0, 59)
        started = day.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
        duration = random.randint(60, 600)
        ended = started + timedelta(seconds=duration)
        sid = prefix + day.strftime("%m%d") + "-" + str(i + 1).zfill(2)
        conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, room_name, started_at, ended_at, duration_seconds, participant) VALUES (?,?,?,?,?,?)",
            (sid, sid, started.isoformat(), ended.isoformat(), duration, "demo")
        )

# --- 30-90 nap: lassú növekedés (korai szakasz, kevés user)
for day_offset in range(60, 0, -1):  # 90..31 nap regen
    day = now - timedelta(days=day_offset + 30)
    day = day.replace(hour=0, minute=0, second=0, microsecond=0)
    t = (60 - day_offset) / 60.0  # 0..1
    # Gyenge, lassan novekvos trend: 1-3 session/nap
    count = max(1, int(1 + 2 * t + random.uniform(-0.5, 0.5)))
    insert_day(day, count, "demo-old-")

# --- 0-30 nap: U-alaku (elobb csokken, majd novekvos)
for day_offset in range(30, 0, -1):
    day = now - timedelta(days=day_offset)
    day = day.replace(hour=0, minute=0, second=0, microsecond=0)
    t = (30 - day_offset) / 29.0  # 0..1
    # U-gorbe: magas -> alacsony -> magas
    count = max(1, int(round(4 + 5 * (math.cos(math.pi * t)) ** 2 + random.uniform(-0.5, 0.5))))
    insert_day(day, count, "demo-")

conn.commit()

# Ellenorzes
for period, label in [(30, "Elmuolt 30 nap"), (90, "Elmuolt 90 nap")]:
    rows = conn.execute(
        "SELECT DATE(started_at) d, COUNT(*) cnt FROM sessions WHERE participant='demo' AND started_at >= datetime('now', ?) GROUP BY d ORDER BY d",
        (f"-{period} days",)
    ).fetchall()
    total = sum(r[1] for r in rows)
    print(f"{label}: {len(rows)} nap, {total} session ossz")

conn.close()
print("Kesz!")
