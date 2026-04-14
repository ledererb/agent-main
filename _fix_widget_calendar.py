"""Fix voice-widget.html: ev.start → ev.start_dt for calendar rendering."""
from pathlib import Path

f = Path(__file__).parent / "thinkai-voice-agent" / "voice-widget.html"
src = f.read_text(encoding="utf-8")

# Fix 1: calendar date field name
src = src.replace(
    "                    const d = new Date(ev.start);\n"
    "                    const months = ['jan', 'feb', 'már', 'ápr', 'máj', 'jún', 'júl', 'aug', 'szep', 'okt', 'nov', 'dec'];\n"
    "                    dateStr = `${months[d.getMonth()]} ${d.getDate()}. ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;\n"
    "                } catch (e) { dateStr = ev.start; }",
    "                    const d = new Date(ev.start_dt || ev.start);\n"
    "                    const months = ['jan', 'feb', 'már', 'ápr', 'máj', 'jún', 'júl', 'aug', 'szep', 'okt', 'nov', 'dec'];\n"
    "                    dateStr = `${months[d.getMonth()]} ${d.getDate()}. ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;\n"
    "                } catch (e) { dateStr = ev.start_dt || ev.start || ''; }"
)

f.write_text(src, encoding="utf-8")
print("OK — calendar field fixed")
