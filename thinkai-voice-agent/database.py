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
from datetime import datetime
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
        """)
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

def get_stats(days: int = 30) -> dict:
    """Return aggregated stats for the admin dashboard."""
    with get_db() as conn:
        total_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        total_interactions = conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
        total_emails = conn.execute("SELECT COUNT(*) FROM email_logs").fetchone()[0]
        total_bookings = conn.execute(
            "SELECT COUNT(*) FROM interactions WHERE type = 'foglalás'"
        ).fetchone()[0]
        open_tasks = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE completed = 0"
        ).fetchone()[0]

        # Interactions by type
        type_rows = conn.execute(
            "SELECT type, COUNT(*) as cnt FROM interactions GROUP BY type ORDER BY cnt DESC"
        ).fetchall()

        # Sessions per day (last N days)
        daily_rows = conn.execute(
            """SELECT DATE(started_at) as day, COUNT(*) as cnt
               FROM sessions
               WHERE started_at >= datetime('now', ?)
               GROUP BY day ORDER BY day ASC""",
            (f"-{days} days",)
        ).fetchall()

        # Avg session duration
        avg_dur = conn.execute(
            "SELECT AVG(duration_seconds) FROM sessions WHERE duration_seconds IS NOT NULL"
        ).fetchone()[0]

    return {
        "total_sessions": total_sessions,
        "total_interactions": total_interactions,
        "total_emails": total_emails,
        "total_bookings": total_bookings,
        "open_tasks": open_tasks,
        "avg_session_duration": round(avg_dur or 0),
        "interactions_by_type": [{"type": r["type"], "count": r["cnt"]} for r in type_rows],
        "sessions_per_day": [{"day": r["day"], "count": r["cnt"]} for r in daily_rows],
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

