"""Use the agent subfolder's voice-widget.html (ThinkAI branded version) and fix ev.start_dt field."""
from pathlib import Path

src_file = Path(__file__).parent / "ezt kellene felhasználni" / "agent" / "voice-widget.html"
dst_file = Path(__file__).parent / "thinkai-voice-agent" / "voice-widget.html"

src = src_file.read_text(encoding="utf-8")

# Fix calendar date field: ev.start → ev.start_dt (our API returns start_dt)
src = src.replace(
    "const d = new Date(ev.start);",
    "const d = new Date(ev.start_dt || ev.start);"
)
src = src.replace(
    "} catch (e) { dateStr = ev.start; }",
    "} catch (e) { dateStr = ev.start_dt || ev.start || ''; }"
)

dst_file.write_text(src, encoding="utf-8")
lines = len(src.splitlines())
print(f"OK — agent widget deployed ({lines} lines), calendar field fixed")
