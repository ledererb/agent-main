import os
import email
import imaplib
import json
import asyncio
from email.header import decode_header
from pathlib import Path
from datetime import datetime, timedelta

import httpx
from dotenv import load_dotenv
from loguru import logger
from anthropic import AsyncAnthropic

import database as db

THIS_DIR = Path(__file__).resolve().parent
load_dotenv(THIS_DIR / ".env")

SYSTEM_PROMPT_FILE = THIS_DIR / "system_prompt.md"
KNOWLEDGE_JSON = THIS_DIR / "knowledge.json"
KNOWLEDGE_MD = THIS_DIR / "knowledge.md"
SETTINGS_FILE = THIS_DIR / "agent_settings.json"

def _read_knowledge() -> str:
    # Try reading settings to see if it's md or json formatted knowledge
    fmt = "json"
    if SETTINGS_FILE.exists():
        try:
            settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            fmt = settings.get("knowledge_format", "json")
        except Exception:
            pass
    if fmt == "md" and KNOWLEDGE_MD.exists():
        return KNOWLEDGE_MD.read_text(encoding="utf-8")
    elif KNOWLEDGE_JSON.exists():
        return KNOWLEDGE_JSON.read_text(encoding="utf-8")
    return ""

def decode_mime_words(s):
    if not s:
        return ""
    return "".join(
        word.decode(encoding or "utf8", errors="replace") if isinstance(word, bytes) else word
        for word, encoding in decode_header(s)
    )

async def process_single_email(from_email: str, from_name: str, subject: str, text_content: str):
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        logger.error("Nincs ANTHROPIC_API_KEY beállítva. E-mail feldolgozás megszakítva.")
        return

    sys_prompt = SYSTEM_PROMPT_FILE.read_text(encoding="utf-8") if SYSTEM_PROMPT_FILE.exists() else "Te egy ügyfélszolgálati asszisztens vagy."
    knowledge = _read_knowledge()

    # Utasítás a strukturált JSON outputra
    json_instruction = """
TE FELADATOD:
Értékeld a beérkezett e-mailt a Tudásbázis és a Rendszer Prompt alapján.
A kimeneted KIZÁRÓLAG egyetlen valid JSON objektum legyen, minden további markdown formázás (pl. ```json) NÉLKÜL.
A válaszlevélt (email_reply) te fogalmazod meg, barátságos, segítőkész hangnemben. Ha releváns autókról vagy projektből van szó, mentsd el a Kanban adatokat is.

JSON STRUKTÚRA:
{
    "is_relevant": true|false,
    "email_reply": "A pontos válaszlevél szövege, HTML sortörésekkel (<br>)",
    "beszelgetes_naplobejegyzes": "A bejövő levél és a válaszod tömör összefoglalója 1 mondatban (későbbi kontextushoz).",
    "kanban_data": {
        "name": "Ügyfél neve (ha tudod, különben az e-mailből)",
        "email": "Ügyfél e-mailje",
        "phone": "Telefonszám (ha megadta, különben üres string)",
        "jarmu_tipusa": "autó / hajó / motor / stb. (opcionális)",
        "jarmu_modell": "pontos modell (opcionális)"
    },
    "meeting": {
        "title": "Találkozó címe (ha az email egyértelműen időpontot kér/foglal)",
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "duration_minutes": 30
    }
}
Ha nem kérnek egyértelműen időpontot, a "meeting" értéke legyen null.
"""
    client = AsyncAnthropic(api_key=anthropic_key)
    
    user_content = f"--- BEJÖVŐ E-MAIL ---\nFeladó: {from_name} <{from_email}>\nTárgy: {subject}\nÜzenet:\n{text_content}\n"
    
    if knowledge:
        sys_prompt += f"\n\n--- TUDÁSBÁZIS ---\n{knowledge}"
    sys_prompt += f"\n\n--- JSON UTASÍTÁS ---\n{json_instruction}"

    logger.info(f"Claude 3.5 Sonnet elemzi az e-mailt: {from_email} - {subject}")
    try:
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2048,
            system=sys_prompt,
            messages=[{"role": "user", "content": user_content}],
            temperature=0.2
        )
        ai_text = response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Anthropic API hiba: {e}")
        # Mivel a levél már Seen állapotba került, de hiba volt,
        # éles rendszerben vissza lehetne állítani Unseen-re.
        return

    # Eltávolítjuk a markdown json blockokat ha esetleg mégis beletenné
    if ai_text.startswith("```json"):
        ai_text = ai_text[7:]
    if ai_text.startswith("```"):
        ai_text = ai_text[3:]
    if ai_text.endswith("```"):
        ai_text = ai_text[:-3]
    ai_text = ai_text.strip()

    try:
        data = json.loads(ai_text)
    except json.JSONDecodeError as e:
        logger.error(f"Hibás JSON válasz az AI-tól: {e}\nNyers AI válasz:\n{ai_text}")
        return

    is_relevant = data.get("is_relevant", False)
    email_reply = data.get("email_reply", "")
    kanban = data.get("kanban_data", {})
    beszelgetes = data.get("beszelgetes_naplobejegyzes", "")
    meeting = data.get("meeting")
    
    log_szoveg = f"{beszelgetes}\n- Bejövő e-mail (Tárgy: {subject}): {text_content}"

    # Ha releváns lead, felvesszük a Kanbanba
    if is_relevant and kanban:
        name = kanban.get("name", from_name) or "Névtelen E-mail lead"
        details = {
            "name": name,
            "email": kanban.get("email", from_email) or from_email,
            "phone": kanban.get("phone", ""),
            "forras_csatorna": "E-mail",
        }
        if kanban.get("jarmu_tipusa"):
            details["jarmu_tipusa"] = kanban["jarmu_tipusa"]
        if kanban.get("jarmu_modell"):
            details["jarmu_modell"] = kanban["jarmu_modell"]
        
        # Mentsük Kanban "uj" oszlopba
        cols = db.get_kanban_columns()
        first_col = cols[0]["id"] if cols else "uj"
        db.upsert_client(custom_data=details, additional_log=log_szoveg, status=first_col)
        logger.info(f"Ügyfél mentve/frissítve a Kanban táblában: {name}")
        
    if meeting:
        try:
            date_str = meeting.get("date")
            time_str = meeting.get("time")
            dur = meeting.get("duration_minutes", 30)
            title = meeting.get("title", f"Megbeszélés: {from_name}")
            
            if date_str and time_str:
                start_dt = datetime.fromisoformat(f"{date_str}T{time_str}:00")
                end_dt = start_dt + timedelta(minutes=dur)
                db.add_calendar_event(
                    title=title,
                    start_dt=start_dt.isoformat(),
                    end_dt=end_dt.isoformat(),
                    duration_minutes=dur,
                    attendee=from_name,
                    attendee_email=from_email
                )
                logger.info(f"Naptár esemény sikeresen létrehozva: {title} {start_dt}")
        except Exception as e:
            logger.error(f"Hiba a naptáresemény hozzáadásakor: {e}")

    if email_reply:
        # Email küldés Brevo API-n
        brevo_key = os.getenv("BREVO_API_KEY", "")
        api_key = brevo_key
        if brevo_key and not brevo_key.startswith("xkeysib-"):
            try:
                import base64 as b64module
                decoded = b64module.b64decode(brevo_key).decode()
                parsed = json.loads(decoded)
                api_key = parsed.get("api_key", brevo_key)
            except Exception:
                pass
                
        sent_ok = False
        error_msg = ""
        try:
            async with httpx.AsyncClient() as http_client:
                resp = await http_client.post(
                    "https://api.brevo.com/v3/smtp/email",
                    headers={"api-key": api_key, "Content-Type": "application/json"},
                    json={
                        "sender": {"name": "Bégé Design Kft.", "email": "bege@thinkai.hu"},
                        "to": [{"email": from_email, "name": from_name}],
                        "subject": f"Re: {subject}",
                        "htmlContent": f'<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">{email_reply}</div>',
                    },
                    timeout=20,
                )
                resp.raise_for_status()
                sent_ok = True
                logger.info(f"Válasz e-mail elküldve neki: {from_email}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Hiba a válaszlevél küldésekor: {e}")

        # Naplózás
        db.add_email_log(
            to_name=from_name,
            to_email=from_email,
            subject=f"Re: {subject}",
            message=email_reply,
            status="sent" if sent_ok else f"failed ({error_msg})",
            session_id=""
        )
        db.log_interaction(
            type="email",
            topic="Email AI válasz",
            summary=f"Bejövő e-mail {from_email} címről",
            result="Sikeres válasz" if sent_ok else "Hibás küldés",
            tool_name="imap_worker_ai",
            session_id=""
        )


def check_imap_sync():
    """Szinkron IMAP lekérdezés, amit egy threadpoolban futtatunk."""
    server = os.getenv("IMAP_SERVER")
    user = os.getenv("IMAP_USER")
    pwd = os.getenv("IMAP_PASS")

    if not server or not user or not pwd:
        # Ha nincsenek meg az adatok, csendben kilép
        return []

    emails_to_process = []
    
    try:
        # Port 993 az alapértelmezett IMAP SSL
        mail = imaplib.IMAP4_SSL(server, port=993)
        mail.login(user, pwd)
        mail.select("inbox")

        # Csak az olvasatlan (UNSEEN) leveleket kérdezzük le
        status, messages = mail.search(None, "UNSEEN")
        if status == "OK" and messages[0]:
            msg_ids = messages[0].split()
            for msg_id in msg_ids:
                res, msg_data = mail.fetch(msg_id, "(RFC822)")
                if res == "OK":
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    subject = decode_mime_words(msg.get("Subject", ""))
                    from_header = decode_mime_words(msg.get("From", ""))
                    
                    from_name = from_header
                    from_email = from_header
                    if "<" in from_header and ">" in from_header:
                        parts = from_header.split("<")
                        from_name = parts[0].strip() or "Névtelen E-mail"
                        from_email = parts[1].replace(">", "").strip()

                    text_content = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                text_content = part.get_payload(decode=True).decode("utf-8", errors="replace")
                                break
                            elif content_type == "text/html" and "attachment" not in content_disposition:
                                # Fallback, ha nincs text/plain, de van html (később megtisztíthatnánk bs4-el, 
                                # de a Claude HTML-ből is megérti a szöveget)
                                text_content = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    else:
                        text_content = msg.get_payload(decode=True).decode("utf-8", errors="replace")

                    emails_to_process.append((msg_id, from_email, from_name, subject, text_content))
        
        # A feldolgozott üzeneteket megjelöljük egyelőre olvasottként ("Seen") beolvasáskor,
        # hogy ha kilép a program a kiexpediálás előtt, ne olvassa be még egyszer
        for item in emails_to_process:
            mail.store(item[0], "+FLAGS", "\\Seen")

        mail.close()
        mail.logout()
    except Exception as e:
        logger.error(f"IMAP csatlakozási hiba: {e}")
        
    return emails_to_process

async def email_worker_loop():
    """Háttérfolyamat, ami percenként hívja az IMAP-et és feldolgozza azt."""
    server = os.getenv("IMAP_SERVER")
    if not server:
        logger.info("Nincs IMAP_SERVER beállítva. Az e-mail háttérfolyamat nem indul el.")
        return
        
    logger.info("E-mail figyelő worker elindítva.")
    while True:
        try:
            # Futtatjuk a blokkoló IMAP műveletet thread-ben
            emails = await asyncio.to_thread(check_imap_sync)
            
            for msg_id, from_email, from_name, subject, text_content in emails:
                await process_single_email(from_email, from_name, subject, text_content)
                
        except asyncio.CancelledError:
            logger.info("E-mail figyelő worker megszakítva.")
            break
        except Exception as e:
            logger.error(f"E-mail worker hiba: {e}")
            
        # Várakozás a következő lekérdezésig (pl. 60 másodperc)
        await asyncio.sleep(60)
