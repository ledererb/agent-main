import json
from datetime import datetime
from pathlib import Path
from loguru import logger

THIS_DIR = Path(__file__).resolve().parent
PROMPT_FILE      = THIS_DIR / "system_prompt.md"
PRAXISINFO_FILE  = THIS_DIR / "praxisinfo.json"
SETTINGS_FILE    = THIS_DIR / "agent_settings.json"

def load_agent_settings() -> dict:
    """Load agent_settings.json — override .env values at runtime."""
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Could not read agent_settings.json: {e}")
    return {}

def _load_praxisinfo() -> dict:
    """Load praxisinfo.json — practice metadata managed from admin UI."""
    if PRAXISINFO_FILE.exists():
        try:
            return json.loads(PRAXISINFO_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Could not read praxisinfo.json: {e}")
    return {}

def _format_doctors(doctors: list) -> str:
    if not doctors:
        return "Nincs megadva"
    lines = []
    for d in doctors:
        name = d.get("nev", "")
        spec = d.get("szak", "")
        svc  = d.get("svc", "")
        line = name
        if spec: line += f" ({spec})"
        if svc:  line += f" – {svc}"
        if line: lines.append(line)
    return "\n".join(f"- {l}" for l in lines) if lines else "Nincs megadva"

def _format_campaigns(campaigns: list) -> str:
    active = [c.get("text", "").strip() for c in campaigns if c.get("active") and c.get("text")]
    return "\n".join(f"- {t}" for t in active) if active else "Nincs aktív kampány"

def _format_exceptions(exceptions: list) -> str:
    valid_exc = [e.strip() for e in exceptions if e.strip()]
    return "\n".join(f"- {e}" for e in valid_exc) if valid_exc else "Nincs megadva kivétel"

def _format_knowledge(raw: str) -> str:
    """Convert knowledge JSON (Q&A dict) to readable K:/V: pairs for the prompt."""
    try:
        pairs = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(pairs, dict) and pairs:
            return "\n\n".join(f"K: {q}\nV: {a}" for q, a in pairs.items())
    except Exception:
        pass
    return raw or ""

def _format_cancellation_policy(pi: dict) -> str:
    rules = []
    
    # Módosítás
    if pi.get("modositas_eng", "igen") == "igen":
        rules.append("Amikor sikeresen lefoglalsz egy időpontot, TÁJÉKOZTASD az ügyfelet a válaszodban: 'Időpont módosítására az időpont előtti 48 órával van lehetőség.'")
        
    # Lemondás (24 órán belül)
    lem_24h = pi.get("lemondas_24h", "figyelmeztetoSzoveggel")
    figy_txt = pi.get("figyelmezteto_szoveg", "")
    
    if lem_24h == "elfogadhato":
        rules.append("Amikor sikeresen lefoglalsz egy időpontot, TÁJÉKOZTASD az ügyfelet a válaszodban, hogy 24 órán belül lemondhatja az időpontot.")
    elif lem_24h == "figyelmeztetoSzoveggel" and figy_txt:
        rules.append(f"Amikor sikeresen lefoglalsz egy időpontot, TÁJÉKOZTASD az ügyfelet ezzel a szöveggel a válaszodban: '{figy_txt}'")
    elif lem_24h == "eloAtadas":
        rules.append("SZIGORÚ SZABÁLY: Amint az ügyfél egy időpont lemondásáról beszél (lemondásról van szó), AZONNAL adja át a beszélgetést egy élő munkatársnak! Ne próbáld te törölni. Kérj emberi átadást a handover_reason vagy report_alert('urgent') segítségével.")

    return "\n".join(f"- {r}" for r in rules) if rules else "Nincs külön lemondási/módosítási szabály."

def get_system_prompt() -> str:
    """Load system prompt from system_prompt.md and inject runtime variables."""
    if not PROMPT_FILE.exists():
        return "Te egy segítőkész AI vagy."
        
    template = PROMPT_FILE.read_text(encoding="utf-8")
    pi       = _load_praxisinfo()
    settings = load_agent_settings()

    variables = {
        "today":          datetime.now().strftime("%Y-%m-%d (%A)"),
        "practice_name":  pi.get("practice_name", ""),
        "address":        pi.get("address", ""),
        "markanev":       pi.get("markanev", ""),
        "szakterulet":    pi.get("szakterulet", ""),
        "kulcsszavak":    pi.get("kulcsszavak", ""),
        "megkozelites":   pi.get("megkozelites", ""),
        "price_list":     pi.get("price_list", ""),
        "doctors":        _format_doctors(pi.get("doctors", [])),
        "campaigns":      _format_campaigns(pi.get("campaigns", [])),
        "exceptions":     _format_exceptions(pi.get("exceptions", [])),
        "cancellation_policy": _format_cancellation_policy(pi),
        "knowledge":      _format_knowledge(settings.get("knowledge_content", "")),
        "tone":           settings.get("tone", ""),
    }

    try:
        return template.format(**variables)
    except KeyError as e:
        # Unknown variable in template — replace only the known ones to avoid crash
        logger.warning(f"Unknown variable in system prompt template: {e}")
        result = template
        for key, val in variables.items():
            result = result.replace("{" + key + "}", str(val))
        return result
