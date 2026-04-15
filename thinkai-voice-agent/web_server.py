"""
ThinkAI Voice Agent — Web Server
Serves the voice widget, generates LiveKit tokens,
and provides a JWT-protected admin API with analytics.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt as pyjwt

from livekit.api import AccessToken, VideoGrants, RoomConfiguration, RoomAgentDispatch
import asyncio

import database as db
import email_processor

THIS_DIR = Path(__file__).resolve().parent
load_dotenv(THIS_DIR / ".env")

# ── JWT config ────────────────────────────────────────────────────────────────
JWT_SECRET  = os.getenv("JWT_SECRET", "thinkai-admin-secret-change-me")
JWT_ALGO    = "HS256"
JWT_EXPIRES = 60 * 60 * 8  # 8 hours

# ── Init DB on startup ────────────────────────────────────────────────────────
db.init_db()
db.seed_admin_from_env()
db.migrate_from_json()   # one-time migration from legacy JSON files

app = FastAPI(title="ThinkAI Voice Agent")

background_tasks = set()

@app.on_event("startup")
async def startup_event():
    # Elindítjuk az email worker loopot a háttérben
    task = asyncio.create_task(email_processor.email_worker_loop())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://thinkai.hu",
        "https://www.thinkai.hu",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth helpers ──────────────────────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)


def create_jwt(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRES),
        "iat": datetime.utcnow(),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nincs token")
    try:
        payload = pyjwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload["sub"]
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token lejárt")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Érvénytelen token")


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def index():
    return FileResponse(THIS_DIR / "voice-widget.html")

@app.get("/widget")
async def widget():
    return FileResponse(THIS_DIR / "voice-widget.html")

@app.get("/admin")
async def admin_page():
    return FileResponse(THIS_DIR / "admin.html")

@app.get("/thinkai-logo.png")
async def logo():
    return FileResponse(THIS_DIR / "thinkai-logo.png", media_type="image/png")

@app.get("/api/token")
async def get_token():
    """Generate a LiveKit room token for a new user."""
    api_key    = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    if not api_key or not api_secret:
        return JSONResponse({"error": "LiveKit credentials not configured"}, status_code=500)

    room_name        = f"thinkai-{uuid.uuid4().hex[:8]}"
    participant_name = f"user-{uuid.uuid4().hex[:6]}"

    token = (
        AccessToken(api_key, api_secret)
        .with_identity(participant_name)
        .with_name("Visitor")
        .with_grants(VideoGrants(room_join=True, room=room_name))
        .with_room_config(
            RoomConfiguration(
                agents=[RoomAgentDispatch(agent_name="thinkai-dobozos-local")]
            )
        )
    )
    return JSONResponse({
        "token": token.to_jwt(),
        "url": os.getenv("LIVEKIT_URL"),
        "room": room_name,
    })

@app.get("/api/health")
async def health():
    return {"status": "ok", "agent": "thinkai-voice-agent"}


@app.post("/api/session/end")
async def session_end(request: Request):
    """Called by the widget on disconnect to record session duration."""
    try:
        body = await request.json()
        session_id = body.get("session_id", "")
        if session_id:
            db.close_session(session_id)
    except Exception:
        pass
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN AUTH
# ═══════════════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/admin/login")
async def admin_login(req: LoginRequest):
    """Admin login — returns JWT token."""
    user = db.verify_admin_user(req.username, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hibás felhasználónév vagy jelszó"
        )
    token = create_jwt(user["username"])
    return {"token": token, "username": user["username"]}


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN API — protected routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/admin/api/stats")
async def admin_stats(period: str = "month", username: str = Depends(verify_jwt)):
    """Analytics summary stats."""
    return db.get_stats(period=period)


@app.get("/admin/api/interactions")
async def admin_interactions(
    limit: int = 100,
    type: str = "",
    username: str = Depends(verify_jwt)
):
    """Interaction list, newest first."""
    return {"interactions": db.get_interactions(limit=limit, type_filter=type)}


@app.get("/admin/api/calendar")
async def admin_calendar(username: str = Depends(verify_jwt)):
    """Calendar events, sorted by start time."""
    return {"events": db.get_calendar_events()}


@app.get("/admin/api/emails")
async def admin_emails(limit: int = 100, username: str = Depends(verify_jwt)):
    """Email logs, newest first."""
    return {"emails": db.get_email_logs(limit=limit)}


@app.get("/admin/api/tasks")
async def admin_tasks(completed: str = "all", username: str = Depends(verify_jwt)):
    """Task list."""
    comp = None if completed == "all" else (completed == "true")
    return {"tasks": db.get_tasks(completed=comp)}


@app.patch("/admin/api/tasks/{task_id}/complete")
async def admin_task_complete(task_id: int, username: str = Depends(verify_jwt)):
    """Toggle task completed status."""
    with db.get_db() as conn:
        row = conn.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        new_val = 0 if row["completed"] else 1
        conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (new_val, task_id))
    return {"ok": True, "completed": bool(new_val)}


@app.delete("/admin/api/tasks/{task_id}")
async def admin_task_delete(task_id: int, username: str = Depends(verify_jwt)):
    """Delete a task."""
    with db.get_db() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return {"ok": True}


@app.get("/admin/api/sessions")
async def admin_sessions(limit: int = 50, username: str = Depends(verify_jwt)):
    """Recent sessions."""
    with db.get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return {"sessions": [dict(r) for r in rows]}


@app.get("/admin/api/sessions/summary")
async def admin_sessions_summary(limit: int = 50, username: str = Depends(verify_jwt)):
    """Sessions enriched with interaction summaries."""
    return {"sessions": db.get_sessions_with_summary(limit=limit)}


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENTS (KANBAN) API
# ═══════════════════════════════════════════════════════════════════════════════

class ClientCreateRequest(BaseModel):
    custom_data: dict

class ClientStatusUpdateRequest(BaseModel):
    status: str

@app.get("/admin/api/clients")
async def admin_clients(username: str = Depends(verify_jwt)):
    """List all clients for Kanban."""
    return {"clients": db.get_clients()}

@app.post("/admin/api/clients")
async def admin_add_client(req: ClientCreateRequest, username: str = Depends(verify_jwt)):
    """Add a new client."""
    client_id = db.add_client(req.custom_data, "uj")
    return {"ok": True, "id": client_id}

@app.patch("/admin/api/clients/{client_id}/status")
async def admin_update_client_status(client_id: int, req: ClientStatusUpdateRequest, username: str = Depends(verify_jwt)):
    """Update client status (drag & drop)."""
    db.update_client_status(client_id, req.status)
    return {"ok": True}

@app.delete("/admin/api/clients/{client_id}")
async def admin_delete_client(client_id: int, username: str = Depends(verify_jwt)):
    """Delete client."""
    db.delete_client(client_id)
    return {"ok": True}

@app.put("/admin/api/clients/{client_id}")
async def admin_update_client_details(client_id: int, req: ClientCreateRequest, username: str = Depends(verify_jwt)):
    """Update client basic details."""
    db.edit_client_details(client_id, req.custom_data)
    return {"ok": True}

class ClientFieldCreateRequest(BaseModel):
    id: str
    name: str
    order_index: int

class ClientFieldUpdateRequest(BaseModel):
    name: str

@app.get("/admin/api/client_fields")
async def admin_get_client_fields(username: str = Depends(verify_jwt)):
    return {"fields": db.get_client_fields()}

@app.post("/admin/api/client_fields")
async def admin_add_client_field(req: ClientFieldCreateRequest, username: str = Depends(verify_jwt)):
    success = db.add_client_field(req.id, req.name, req.order_index)
    if not success:
        raise HTTPException(status_code=400, detail="Field ID already exists")
    return {"ok": True}

@app.put("/admin/api/client_fields/{field_id}")
async def admin_update_client_field(field_id: str, req: ClientFieldUpdateRequest, username: str = Depends(verify_jwt)):
    db.update_client_field(field_id, req.name)
    return {"ok": True}

@app.delete("/admin/api/client_fields/{field_id}")
async def admin_delete_client_field(field_id: str, username: str = Depends(verify_jwt)):
    db.delete_client_field(field_id)
    return {"ok": True}

class KanbanColumnCreateRequest(BaseModel):
    id: str
    name: str
    order_index: int

class KanbanColumnUpdateRequest(BaseModel):
    name: str

@app.get("/admin/api/kanban_columns")
async def admin_get_kanban_columns(username: str = Depends(verify_jwt)):
    return {"columns": db.get_kanban_columns()}

@app.post("/admin/api/kanban_columns")
async def admin_add_kanban_column(req: KanbanColumnCreateRequest, username: str = Depends(verify_jwt)):
    success = db.add_kanban_column(req.id, req.name, req.order_index)
    if not success:
        raise HTTPException(status_code=400, detail="Column ID already exists")
    return {"ok": True}

@app.put("/admin/api/kanban_columns/{col_id}")
async def admin_update_kanban_column(col_id: str, req: KanbanColumnUpdateRequest, username: str = Depends(verify_jwt)):
    db.update_kanban_column(col_id, req.name)
    return {"ok": True}

@app.delete("/admin/api/kanban_columns/{col_id}")
async def admin_delete_kanban_column(col_id: str, username: str = Depends(verify_jwt)):
    try:
        db.delete_kanban_column(col_id)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Legacy public API (for backward compat with voice-widget.html) ────────────
@app.get("/api/calendar")
async def get_calendar():
    events = db.get_calendar_events()
    return JSONResponse({"events": events})

@app.get("/api/emails")
async def get_emails():
    return JSONResponse({"emails": db.get_email_logs()})


# ═══════════════════════════════════════════════════════════════════════════════
SETTINGS_FILE  = THIS_DIR / "agent_settings.json"
KNOWLEDGE_JSON = THIS_DIR / "knowledge.json"
KNOWLEDGE_MD   = THIS_DIR / "knowledge.md"
SYSTEM_PROMPT_FILE = THIS_DIR / "system_prompt.md"
WORKFLOW_FILE      = THIS_DIR / "workflow.md"

DEFAULT_SETTINGS = {
    "voice_id": os.getenv("CARTESIA_VOICE_ID", "93896c4f-aa00-4c17-a360-fec55579d7fa"),
    "tone": "professional_friendly",
    "tone_custom": "",
    "knowledge_format": "json",
    "business_hours": {
        "monday":    {"open": "09:00", "close": "18:00", "enabled": True},
        "tuesday":   {"open": "09:00", "close": "18:00", "enabled": True},
        "wednesday": {"open": "09:00", "close": "18:00", "enabled": True},
        "thursday":  {"open": "09:00", "close": "18:00", "enabled": True},
        "friday":    {"open": "09:00", "close": "16:00", "enabled": True},
        "saturday":  {"open": None,    "close": None,    "enabled": False},
        "sunday":    {"open": None,    "close": None,    "enabled": False},
    },
}


def _read_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)


def _read_knowledge() -> dict:
    """Read knowledge content and format from disk."""
    settings = _read_settings()
    fmt = settings.get("knowledge_format", "json")
    if fmt == "md":
        content = KNOWLEDGE_MD.read_text(encoding="utf-8") if KNOWLEDGE_MD.exists() else ""
    else:
        content = KNOWLEDGE_JSON.read_text(encoding="utf-8") if KNOWLEDGE_JSON.exists() else "{}"
    return {"format": fmt, "content": content}


@app.get("/admin/api/settings")
async def get_settings(username: str = Depends(verify_jwt)):
    """Return current agent settings + knowledge base content."""
    s = _read_settings()
    k = _read_knowledge()
    return {**s, "knowledge_content": k["content"]}


class SettingsSaveRequest(BaseModel):
    voice_id: str = ""
    tone: str = "professional_friendly"
    tone_custom: str = ""
    knowledge_format: str = "json"
    knowledge_content: str = ""
    greeting: str = ""
    business_hours: dict = {}


class TextFileRequest(BaseModel):
    content: str = ""


@app.post("/admin/api/settings")
async def save_settings(payload: SettingsSaveRequest, username: str = Depends(verify_jwt)):
    """Save agent settings and knowledge base to disk."""
    # Save settings (without knowledge content)
    settings = {
        "voice_id":        payload.voice_id,
        "tone":            payload.tone,
        "tone_custom":     payload.tone_custom,
        "knowledge_format": payload.knowledge_format,
        "greeting":        payload.greeting,
        "business_hours":  payload.business_hours,
    }
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")

    # Save knowledge to appropriate file
    if payload.knowledge_format == "md":
        KNOWLEDGE_MD.write_text(payload.knowledge_content, encoding="utf-8")
    else:
        try:
            parsed = json.loads(payload.knowledge_content)
            KNOWLEDGE_JSON.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Hibás JSON formátum: {e}")

    return {"ok": True, "message": "Beállítások elmentve. Az agent újraindítása szükséges a változtatások érvényesítéséhez."}


# ── System Prompt ─────────────────────────────────────────────────────────────

@app.get("/admin/api/system-prompt")
async def get_system_prompt(username: str = Depends(verify_jwt)):
    """Return the current system prompt (system_prompt.md)."""
    content = SYSTEM_PROMPT_FILE.read_text(encoding="utf-8") if SYSTEM_PROMPT_FILE.exists() else ""
    return {"content": content}


@app.post("/admin/api/system-prompt")
async def save_system_prompt(payload: TextFileRequest, username: str = Depends(verify_jwt)):
    """Overwrite system_prompt.md."""
    SYSTEM_PROMPT_FILE.write_text(payload.content, encoding="utf-8")
    return {"ok": True, "message": "System prompt elmentve."}


# ── Workflow ───────────────────────────────────────────────────────────────────

@app.get("/admin/api/workflow")
async def get_workflow(username: str = Depends(verify_jwt)):
    """Return the current workflow definition (workflow.md)."""
    content = WORKFLOW_FILE.read_text(encoding="utf-8") if WORKFLOW_FILE.exists() else ""
    return {"content": content}


@app.post("/admin/api/workflow")
async def save_workflow(payload: TextFileRequest, username: str = Depends(verify_jwt)):
    """Overwrite workflow.md."""
    WORKFLOW_FILE.write_text(payload.content, encoding="utf-8")
    return {"ok": True, "message": "Workflow elmentve."}


@app.get("/admin/api/cartesia/voices")
async def cartesia_voices(username: str = Depends(verify_jwt)):
    """Proxy: list available Cartesia voices."""
    api_key = os.getenv("CARTESIA_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="CARTESIA_API_KEY nincs beállítva")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.cartesia.ai/voices",
                headers={"X-API-Key": api_key, "Cartesia-Version": "2024-06-10"}
            )
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Cartesia API hiba: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
