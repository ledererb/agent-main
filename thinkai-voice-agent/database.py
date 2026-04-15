"""
ThinkAI Voice Agent — SQLite Database Layer
All persistent data: calendar, emails, tasks, sessions, interactions, admin users.
DB path is configurable via DB_PATH env var for Docker volume compatibility.
"""

import os
import sqlite3
import hashlib
import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

# ── DB path — configurable for Docker volume mounts ──────────────────────────
THIS_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DB_PATH", str(THIS_DIR / "thinkai.db")))


# ── Connection context manager ────────────────────────────────────────────────
@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # safe for concurrent reads
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMA INIT
# ═══════════════════════════════════════════════════════════════════════════════

def init_db():
    """Create all tables if they don't exist."""
    with get_db() as conn:
        conn.executescript("""
            -- Admin users (multi-user, bcrypt hashed passwords)
            CREATE TABLE IF NOT EXISTS admin_users (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT    NOT NULL UNIQUE,
                email     TEXT,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            -- Voice agent sessions (every LiveKit room connection)
            CREATE TABLE IF NOT EXISTS sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT    NOT NULL UNIQUE,
                room_name   TEXT,
                started_at  TEXT    NOT NULL,
                ended_at    TEXT,
                duration_seconds INTEGER,
                participant TEXT
            );

            -- Interactions (tool calls + conversation events within a session)
            CREATE TABLE IF NOT EXISTS interactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT,
                type        TEXT NOT NULL,  -- 'bejövő', 'kimenő', 'foglalás', 'email', 'utánkövetés', 'kérdés'
                topic       TEXT,
                summary     TEXT,
                result      TEXT,
                tool_name   TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );

            -- Calendar events
            CREATE TABLE IF NOT EXISTS calendar_events (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                title            TEXT NOT NULL,
                start_dt         TEXT NOT NULL,
                end_dt           TEXT,
                duration_minutes INTEGER DEFAULT 30,
                attendee         TEXT,
                attendee_email   TEXT,
                created_at       TEXT NOT NULL DEFAULT (datetime('now'))
            );

            -- Email logs
            CREATE TABLE IF NOT EXISTS email_logs (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                to_name    TEXT NOT NULL,
                to_email   TEXT NOT NULL,
                subject    TEXT,
                message    TEXT,
                sent_at    TEXT NOT NULL DEFAULT (datetime('now')),
                status     TEXT DEFAULT 'sent',
                error      TEXT,
                session_id TEXT
            );

            -- Tasks / notes
            CREATE TABLE IF NOT EXISTS tasks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                text       TEXT NOT NULL,
                priority   TEXT DEFAULT 'normal',
                due_date   TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                completed  INTEGER DEFAULT 0,
                session_id TEXT
            );

            -- Clients for Kanban
            CREATE TABLE IF NOT EXISTS clients (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                email      TEXT,
                phone      TEXT,
                status     TEXT DEFAULT 'uj',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            -- Kanban columns (editable statuses)
            CREATE TABLE IF NOT EXISTS kanban_columns (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                order_index INTEGER NOT NULL
            );
            -- Client fields (dynamic form fields)
            CREATE TABLE IF NOT EXISTS client_fields (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                order_index INTEGER NOT NULL
            );
        """)

        try:
            conn.execute("ALTER TABLE clients ADD COLUMN custom_data TEXT DEFAULT '{}'")
        except sqlite3.OperationalError:
            pass # Already exists
            
        import json
        count_fields = conn.execute("SELECT COUNT(*) FROM client_fields").fetchone()[0]
        if count_fields == 0:
            conn.executemany(
                "INSERT INTO client_fields (id, name, order_index) VALUES (?, ?, ?)",
                [
                    ("name", "Név", 1),
                    ("email", "Email", 2),
                    ("phone", "Telefonszám", 3)
                ]
            )
            # Safe JSON migration for custom_data
            rows = conn.execute("SELECT id, name, email, phone FROM clients WHERE custom_data = '{}' OR custom_data IS NULL").fetchall()
            for r in rows:
                c_data = json.dumps({"name": r["name"], "email": r["email"] or "", "phone": r["phone"] or ""})
                conn.execute("UPDATE clients SET custom_data = ? WHERE id = ?", (c_data, r["id"]))
        
        # Ensure beszelgetes_naplo always exists
        try:
            conn.execute("INSERT OR IGNORE INTO client_fields (id, name, order_index) VALUES ('beszelgetes_naplo', 'Beszélgetés napló', 4)")
        except Exception:
            pass


        # Seed initial kanban columns if empty
        count = conn.execute("SELECT COUNT(*) FROM kanban_columns").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO kanban_columns (id, name, order_index) VALUES (?, ?, ?)",
                [
                    ("uj", "Új", 1),
                    ("kapcsolatfelvetel", "Kapcsolatfelvétel", 2),
                    ("targyalas", "Tárgyalás", 3),
                    ("szerzodott", "Szerződött", 4)
                ]
            )

    logger.info(f"Database initialized at: {DB_PATH}")


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN USERS
# ═══════════════════════════════════════════════════════════════════════════════

def _hash_password(password: str) -> str:
    """Simple SHA-256 + salt hash (no bcrypt dep needed)."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, hashed = stored_hash.split(":", 1)
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed
    except Exception:
        return False


def create_admin_user(username: str, password: str, email: str = "") -> bool:
    """Create an admin user. Returns False if username already exists."""
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO admin_users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, _hash_password(password))
            )
        logger.info(f"Admin user created: {username}")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"Admin user already exists: {username}")
        return False


def verify_admin_user(username: str, password: str) -> dict | None:
    """Verify admin credentials. Returns user dict or None."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM admin_users WHERE username = ?", (username,)
        ).fetchone()
    if row and _verify_password(password, row["password_hash"]):
        return {"id": row["id"], "username": row["username"], "email": row["email"]}
    return None


def seed_admin_from_env():
    """Seed admin user from ADMIN_USERNAME / ADMIN_PASSWORD env vars on first run."""
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "thinkai2026")
    email = os.getenv("ADMIN_EMAIL", "")
    created = create_admin_user(username, password, email)
    if created:
        logger.info(f"Seeded admin user from env: {username}")


# ═══════════════════════════════════════════════════════════════════════════════
# SESSIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_session(session_id: str, room_name: str, participant: str = "") -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, room_name, started_at, participant) VALUES (?, ?, ?, ?)",
            (session_id, room_name, datetime.utcnow().isoformat(), participant)
        )


def close_session(session_id: str) -> None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT started_at FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row:
            started = datetime.fromisoformat(row["started_at"])
            duration = int((datetime.utcnow() - started).total_seconds())
            conn.execute(
                "UPDATE sessions SET ended_at = ?, duration_seconds = ? WHERE session_id = ?",
                (datetime.utcnow().isoformat(), duration, session_id)
            )


# ═══════════════════════════════════════════════════════════════════════════════
# INTERACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def log_interaction(
    type: str,
    topic: str = "",
    summary: str = "",
    result: str = "",
    tool_name: str = "",
    session_id: str = "",
) -> None:
    with get_db() as conn:
        conn.execute(
            """INSERT INTO interactions (session_id, type, topic, summary, result, tool_name)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id or None, type, topic, summary, result, tool_name or None)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CALENDAR
# ═══════════════════════════════════════════════════════════════════════════════

def get_calendar_events() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM calendar_events ORDER BY start_dt ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def add_calendar_event(title, start_dt, end_dt, duration_minutes, attendee="", attendee_email="") -> int:
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO calendar_events (title, start_dt, end_dt, duration_minutes, attendee, attendee_email)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, start_dt, end_dt, duration_minutes, attendee, attendee_email)
        )
        return cur.lastrowid


def update_calendar_event(event_id: int, **fields) -> bool:
    allowed = {"title", "start_dt", "end_dt", "duration_minutes", "attendee", "attendee_email"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    with get_db() as conn:
        conn.execute(
            f"UPDATE calendar_events SET {set_clause} WHERE id = ?",
            (*updates.values(), event_id)
        )
    return True


def delete_calendar_event(event_id: int) -> bool:
    with get_db() as conn:
        conn.execute("DELETE FROM calendar_events WHERE id = ?", (event_id,))
    return True


def find_calendar_event_by_title(title_fragment: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM calendar_events WHERE LOWER(title) LIKE ? ORDER BY start_dt ASC LIMIT 1",
            (f"%{title_fragment.lower()}%",)
        ).fetchone()
    return dict(row) if row else None


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL LOGS
# ═══════════════════════════════════════════════════════════════════════════════

def add_email_log(to_name, to_email, subject, message, status, error="", session_id="") -> int:
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO email_logs (to_name, to_email, subject, message, status, error, session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (to_name, to_email, subject, message, status, error or None, session_id or None)
        )
        return cur.lastrowid


def get_email_logs(limit: int = 100) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# TASKS
# ═══════════════════════════════════════════════════════════════════════════════

def add_task(text, priority="normal", due_date="", session_id="") -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (text, priority, due_date, session_id) VALUES (?, ?, ?, ?)",
            (text, priority, due_date or None, session_id or None)
        )
        return cur.lastrowid


def get_tasks(completed: bool | None = None, limit: int = 100) -> list[dict]:
    with get_db() as conn:
        if completed is None:
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE completed = ? ORDER BY created_at DESC LIMIT ?",
                (1 if completed else 0, limit)
            ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

def get_stats(period: str = "month") -> dict:
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
        prev_sess   = "DATE(started_at) >= DATE('now','weekday 1','-14 days') AND DATE(started_at) < DATE('now','weekday 1','-7 days')"
        prev_inter  = "DATE(created_at)  >= DATE('now','weekday 1','-14 days') AND DATE(created_at)  < DATE('now','weekday 1','-7 days')"
        prev_email  = "DATE(sent_at)     >= DATE('now','weekday 1','-14 days') AND DATE(sent_at)     < DATE('now','weekday 1','-7 days')"
        prev_cal    = "DATE(start_dt)    >= DATE('now','weekday 1','-14 days') AND DATE(start_dt)    < DATE('now','weekday 1','-7 days')"
    elif period == "month":
        sess_where  = "strftime('%Y-%m', started_at) = strftime('%Y-%m', 'now')"
        inter_where = "strftime('%Y-%m', created_at)  = strftime('%Y-%m', 'now')"
        email_where = "strftime('%Y-%m', sent_at)     = strftime('%Y-%m', 'now')"
        cal_where   = "strftime('%Y-%m', start_dt)    = strftime('%Y-%m', 'now')"
        prev_sess   = "strftime('%Y-%m', started_at) = strftime('%Y-%m', 'now', '-1 month')"
        prev_inter  = "strftime('%Y-%m', created_at)  = strftime('%Y-%m', 'now', '-1 month')"
        prev_email  = "strftime('%Y-%m', sent_at)     = strftime('%Y-%m', 'now', '-1 month')"
        prev_cal    = "strftime('%Y-%m', start_dt)    = strftime('%Y-%m', 'now', '-1 month')"
    else:  # year
        sess_where  = "started_at >= datetime('now', '-12 months')"
        inter_where = "created_at  >= datetime('now', '-12 months')"
        email_where = "sent_at     >= datetime('now', '-12 months')"
        cal_where   = "start_dt    >= datetime('now', '-12 months')"
        prev_sess   = "started_at >= datetime('now','-24 months') AND started_at < datetime('now','-12 months')"
        prev_inter  = "created_at  >= datetime('now','-24 months') AND created_at  < datetime('now','-12 months')"
        prev_email  = "sent_at     >= datetime('now','-24 months') AND sent_at     < datetime('now','-12 months')"
        prev_cal    = "start_dt    >= datetime('now','-24 months') AND start_dt    < datetime('now','-12 months')"

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

        # ── Previous period totals (for trend indicators) ─────────────────
        prev_total_sessions = conn.execute(
            f"SELECT COUNT(*) FROM sessions WHERE {prev_sess}"
        ).fetchone()[0]
        prev_total_interactions = conn.execute(
            f"SELECT COUNT(*) FROM interactions WHERE {prev_inter}"
        ).fetchone()[0]
        prev_total_emails = conn.execute(
            f"SELECT COUNT(*) FROM email_logs WHERE {prev_email}"
        ).fetchone()[0]
        prev_total_bookings = conn.execute(
            f"SELECT COUNT(*) FROM calendar_events WHERE {prev_cal}"
        ).fetchone()[0]
        prev_avg_dur = conn.execute(
            f"SELECT AVG(duration_seconds) FROM sessions WHERE duration_seconds IS NOT NULL AND {prev_sess}"
        ).fetchone()[0]

    # ── Fill missing days with 0 so the chart has no gaps ───────────────
    raw_days = {r["day"]: r["cnt"] for r in chart_rows}
    today = datetime.utcnow().date()
    if period == "week":
        # current Mon..today
        week_start = today - timedelta(days=today.weekday())
        all_keys = [(week_start + timedelta(days=i)).isoformat() for i in range((today - week_start).days + 1)]
    elif period == "month":
        # 1st of month..today
        month_start = today.replace(day=1)
        all_keys = [(month_start + timedelta(days=i)).isoformat() for i in range((today - month_start).days + 1)]
    else:  # year — monthly buckets
        all_keys = []
        d = today.replace(day=1)
        for _ in range(12):
            all_keys.insert(0, d.strftime("%Y-%m"))
            # go back one month
            d = (d - timedelta(days=1)).replace(day=1)
    filled_days = [{"day": k, "count": raw_days.get(k, 0)} for k in all_keys]

    return {
        "total_sessions":       total_sessions,
        "total_interactions":   total_interactions,
        "total_emails":         total_emails,
        "total_bookings":       total_bookings,
        "open_tasks":           open_tasks,
        "avg_session_duration": round(avg_dur or 0),
        "interactions_by_type": [{"type": r["type"], "count": r["cnt"]} for r in type_rows],
        "sessions_per_day":     filled_days,
        "previous_period": {
            "total_sessions":       prev_total_sessions,
            "total_interactions":   prev_total_interactions,
            "total_emails":         prev_total_emails,
            "total_bookings":       prev_total_bookings,
            "avg_session_duration": round(prev_avg_dur or 0),
        },
    }

def get_interactions(limit: int = 100, type_filter: str = "") -> list[dict]:
    with get_db() as conn:
        if type_filter:
            rows = conn.execute(
                "SELECT * FROM interactions WHERE type = ? ORDER BY created_at DESC LIMIT ?",
                (type_filter, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM interactions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(r) for r in rows]


def _build_session_summary(interactions: list[dict]) -> str:
    """Generate a short natural-language summary from a session's interactions."""
    if not interactions:
        return "Nincs rögzített interakció ebben a sessionben."

    type_counts: dict[str, int] = {}
    topics: list[str] = []
    for i in interactions:
        t = i.get("type", "")
        if t:
            type_counts[t] = type_counts.get(t, 0) + 1
        topic = i.get("topic", "")
        if topic and topic not in topics:
            topics.append(topic)

    parts = []
    label_map = {
        "email":    "email küldés",
        "foglalás": "időpontfoglalás",
        "feladat":  "feladat rögzítés",
        "kérdés":   "kérdés / tudásbázis",
        "időjárás": "időjárás lekérdezés",
    }
    for typ, cnt in type_counts.items():
        label = label_map.get(typ, typ)
        parts.append(f"{cnt}× {label}")

    summary = "A session során: " + ", ".join(parts) + "." if parts else "Általános beszélgetés."

    # Add up to 3 specific topics
    specific = [t for t in topics if t not in ("Email küldés", "Időpontfoglalás", "Feladat rögzítés")][:3]
    if specific:
        summary += " Témák: " + "; ".join(specific) + "."

    return summary


def get_sessions_with_summary(limit: int = 50) -> list[dict]:
    """Return sessions enriched with interaction count and auto-generated summary."""
    with get_db() as conn:
        sessions = conn.execute(
            "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        sessions = [dict(s) for s in sessions]

        for sess in sessions:
            sid = sess["session_id"]
            rows = conn.execute(
                "SELECT * FROM interactions WHERE session_id = ? ORDER BY created_at ASC",
                (sid,)
            ).fetchall()
            interactions = [dict(r) for r in rows]
            sess["interaction_count"] = len(interactions)
            sess["interactions"] = interactions
            sess["summary"] = _build_session_summary(interactions)

    return sessions


# ═══════════════════════════════════════════════════════════════════════════════
# JSON MIGRATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def migrate_from_json():
    """One-time migration: import existing JSON data into SQLite.
    Safe to call multiple times — uses a metadata flag to skip if already done."""
    import json

    # Check if migration was already done
    with get_db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT)"
        )
        done = conn.execute(
            "SELECT value FROM _meta WHERE key = 'json_migrated'"
        ).fetchone()
    if done:
        return 0

    # calendar.json
    cal_file = THIS_DIR / "calendar.json"
    if cal_file.exists():
        try:
            events = json.loads(cal_file.read_text(encoding="utf-8"))
            for ev in events:
                start = ev.get("start", "")
                from datetime import timedelta
                dur = ev.get("duration_minutes", 30)
                try:
                    end = (datetime.fromisoformat(start) + timedelta(minutes=dur)).isoformat()
                except Exception:
                    end = start
                add_calendar_event(
                    title=ev.get("title", ""),
                    start_dt=start,
                    end_dt=end,
                    duration_minutes=dur,
                    attendee=ev.get("attendee", ""),
                    attendee_email=ev.get("attendee_email", "")
                )
                migrated += 1
            logger.info(f"Migrated {len(events)} calendar events from JSON")
        except Exception as e:
            logger.warning(f"Calendar JSON migration failed: {e}")

    # emails.json
    emails_file = THIS_DIR / "emails.json"
    if emails_file.exists():
        try:
            emails = json.loads(emails_file.read_text(encoding="utf-8"))
            for em in emails:
                add_email_log(
                    to_name=em.get("to_name", ""),
                    to_email=em.get("to_email", ""),
                    subject=em.get("subject", ""),
                    message=em.get("message", ""),
                    status=em.get("status", "sent"),
                    error=em.get("error", "") or "",
                )
                migrated += 1
            logger.info(f"Migrated {len(emails)} emails from JSON")
        except Exception as e:
            logger.warning(f"Emails JSON migration failed: {e}")

    # tasks.json
    tasks_file = THIS_DIR / "tasks.json"
    if tasks_file.exists():
        try:
            tasks = json.loads(tasks_file.read_text(encoding="utf-8"))
            for t in tasks:
                add_task(
                    text=t.get("text", ""),
                    priority=t.get("priority", "normal"),
                    due_date=t.get("due_date", ""),
                )
                migrated += 1
            logger.info(f"Migrated {len(tasks)} tasks from JSON")
        except Exception as e:
            logger.warning(f"Tasks JSON migration failed: {e}")

    # Mark migration as done
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO _meta (key, value) VALUES ('json_migrated', ?)",
            (datetime.utcnow().isoformat(),)
        )
    logger.info(f"JSON migration complete. Total migrated: {migrated}")
    return migrated


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENTS (KANBAN)
# ═══════════════════════════════════════════════════════════════════════════════

def add_client(custom_data: dict, status: str = "uj") -> int:
    import json
    # SQL req: name is NOT NULL
    sql_name = custom_data.get("name", "Névtelen") if custom_data.get("name", "").strip() else "Névtelen"
    sql_email = custom_data.get("email", "")
    sql_phone = custom_data.get("phone", "")
    
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO clients (name, email, phone, status, custom_data) VALUES (?, ?, ?, ?, ?)",
            (sql_name, sql_email or None, sql_phone or None, status, json.dumps(custom_data))
        )
        return cur.lastrowid

def find_client_by_contact(email: str = "", phone: str = "") -> dict | None:
    if not email and not phone:
        return None
    with get_db() as conn:
        if email and phone:
            row = conn.execute("SELECT * FROM clients WHERE email = ? OR phone = ? ORDER BY id DESC LIMIT 1", (email, phone)).fetchone()
        elif email:
            row = conn.execute("SELECT * FROM clients WHERE email = ? ORDER BY id DESC LIMIT 1", (email,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM clients WHERE phone = ? ORDER BY id DESC LIMIT 1", (phone,)).fetchone()
    return dict(row) if row else None

def upsert_client(custom_data: dict, additional_log: str = "", status: str = "uj") -> int:
    import json
    email = custom_data.get("email", "").strip()
    phone = custom_data.get("phone", "").strip()
    
    existing = find_client_by_contact(email, phone)
    
    if existing:
        try:
            curr_data = json.loads(existing["custom_data"] or "{}")
        except:
            curr_data = {}
        
        # Merge new fields into existing
        for k, v in custom_data.items():
            if v and str(v).strip():
                curr_data[k] = v
                
        if additional_log:
            old_log = curr_data.get("beszelgetes_naplo", "")
            from datetime import datetime
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_entry = f"[{now_str}]\n{additional_log}\n"
            curr_data["beszelgetes_naplo"] = (old_log + "\n" + new_entry).strip()
            
        edit_client_details(existing["id"], curr_data)
        logger.info(f"Updated existing client (ID: {existing['id']})")
        return existing["id"]
    else:
        if additional_log:
            from datetime import datetime
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            custom_data["beszelgetes_naplo"] = f"[{now_str}]\n{additional_log}"
            
        return add_client(custom_data, status)


def get_clients(limit: int = 500) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM clients ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def update_client_status(client_id: int, status: str) -> bool:
    with get_db() as conn:
        conn.execute(
            "UPDATE clients SET status = ? WHERE id = ?",
            (status, client_id)
        )
    return True


def delete_client(client_id: int) -> bool:
    with get_db() as conn:
        conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    return True


def edit_client_details(client_id: int, custom_data: dict) -> bool:
    import json
    sql_name = custom_data.get("name", "Névtelen") if custom_data.get("name", "").strip() else "Névtelen"
    sql_email = custom_data.get("email", "")
    sql_phone = custom_data.get("phone", "")
    with get_db() as conn:
        conn.execute(
            "UPDATE clients SET name = ?, email = ?, phone = ?, custom_data = ? WHERE id = ?",
            (sql_name, sql_email or None, sql_phone or None, json.dumps(custom_data), client_id)
        )
    return True

def get_client_fields() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM client_fields ORDER BY order_index ASC").fetchall()
    return [dict(r) for r in rows]

def add_client_field(field_id: str, name: str, order_index: int) -> bool:
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO client_fields (id, name, order_index) VALUES (?, ?, ?)",
                (field_id, name, order_index)
            )
            return True
        except sqlite3.IntegrityError:
            return False

def update_client_field(field_id: str, name: str) -> bool:
    with get_db() as conn:
        conn.execute("UPDATE client_fields SET name = ? WHERE id = ?", (name, field_id))
    return True

def delete_client_field(field_id: str) -> bool:
    with get_db() as conn:
        conn.execute("DELETE FROM client_fields WHERE id = ?", (field_id,))
    return True


def get_kanban_columns() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM kanban_columns ORDER BY order_index ASC").fetchall()
    return [dict(r) for r in rows]

def add_kanban_column(col_id: str, name: str, order_index: int) -> bool:
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO kanban_columns (id, name, order_index) VALUES (?, ?, ?)",
                (col_id, name, order_index)
            )
            return True
        except sqlite3.IntegrityError:
            return False

def update_kanban_column(col_id: str, name: str) -> bool:
    with get_db() as conn:
        conn.execute("UPDATE kanban_columns SET name = ? WHERE id = ?", (name, col_id))
    return True

def delete_kanban_column(col_id: str) -> bool:
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM clients WHERE status = ?", (col_id,)).fetchone()[0]
        if count > 0:
            raise ValueError(f"Nem törölheted: a(z) '{col_id}' oszlopban {count} ügyfél található.")
        conn.execute("DELETE FROM kanban_columns WHERE id = ?", (col_id,))
    return True
