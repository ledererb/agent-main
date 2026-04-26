import sys
import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            html = f.read()

        # Update the openLogModal function definition
        old_func = """function openLogModal(encodedText) {
    let t = '';
    try { t = decodeURIComponent(atob(encodedText)); } catch(e){}
    document.getElementById('log-modal-content').value = t;
    document.getElementById('log-modal').style.display = 'flex';
}"""
        new_func = """function openLogModal(encodedText, name, channel, date) {
    let t = '';
    try { t = decodeURIComponent(atob(encodedText)); } catch(e){}
    document.getElementById('log-modal-content').value = t;
    if(name) document.getElementById('log-modal-title-name').textContent = name;
    if(channel) document.getElementById('log-modal-channel').textContent = channel;
    if(date) document.getElementById('log-modal-date').textContent = date;
    document.getElementById('log-modal-topic').textContent = 'Beszélgetés napló';
    document.getElementById('log-modal').style.display = 'flex';
}"""
        html = html.replace(old_func, new_func)

        # Update the caller in loadClientsTable
        # Original caller line:
        # return `<td>${val ? `<button onclick="openLogModal('${esc(btoa(encodeURIComponent(val)))}')" style="background:rgba(0,212,200,0.1);border:1px solid var(--accent);color:var(--accent);border-radius:4px;cursor:pointer;padding:4px 8px;font-size:11px;">Megtekintés</button>` : '<span style="color:var(--text-muted)">-</span>'}</td>`;
        
        # We need to find the specific block:
        # if (f.id === 'beszelgetes_naplo') {
        #     return `<td>${val ? `<button onclick="openLogModal('${esc(btoa(encodeURIComponent(val)))}')" style=...
        
        pattern = r"(if \(f\.id === 'beszelgetes_naplo'\) \{\s*return `<td>\$\{val \? `<button onclick=\"openLogModal\('\$\{esc\(btoa\(encodeURIComponent\(val\)\)\)\}'\)\" )(style=\"background:rgba\(0,212,200,0\.1\);border:1px solid var\(--accent\);color:var\(--accent\);border-radius:4px;cursor:pointer;padding:4px 8px;font-size:11px;\">Megtekintés</button>` : '<span style=\"color:var\(--text-muted\)\">-</span>'\}</td>`;\s*\})"
        
        replacement = r"if (f.id === 'beszelgetes_naplo') {\n                const safeName = esc(customObj.nev || customObj['név'] || customObj.name || 'Ismeretlen').replace(/'/g, \"\\\\'\");\n                const safeDate = esc(fmtDt(c.created_at));\n                return `<td>${val ? `<button onclick=\"openLogModal('${esc(btoa(encodeURIComponent(val)))}', '${safeName}', '${esc(csatorna)}', '${safeDate}')\" \2"

        # Instead of regex, let's use string replace for safety
        
        old_caller = """            if (f.id === 'beszelgetes_naplo') {
                return `<td>${val ? `<button onclick="openLogModal('${esc(btoa(encodeURIComponent(val)))}')" style="background:rgba(0,212,200,0.1);border:1px solid var(--accent);color:var(--accent);border-radius:4px;cursor:pointer;padding:4px 8px;font-size:11px;">Megtekintés</button>` : '<span style="color:var(--text-muted)">-</span>'}</td>`;
            }"""
        
        new_caller = """            if (f.id === 'beszelgetes_naplo') {
                const safeName = esc(customObj.nev || customObj['név'] || customObj.name || 'Ismeretlen').replace(/'/g, "\\\\'");
                const safeDate = esc(fmtDt(c.created_at));
                return `<td>${val ? `<button onclick="openLogModal('${esc(btoa(encodeURIComponent(val)))}', '${safeName}', '${esc(csatorna)}', '${safeDate}')" style="background:rgba(0,212,200,0.1);border:1px solid var(--accent);color:var(--accent);border-radius:4px;cursor:pointer;padding:4px 8px;font-size:11px;">Megtekintés</button>` : '<span style="color:var(--text-muted)">-</span>'}</td>`;
            }"""
        
        if old_caller in html:
            html = html.replace(old_caller, new_caller)
        else:
            print("Could not find the exact old caller string. Let's try searching manually.")

        with open('admin.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Updated log modal to use dynamic data!")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
