import re

def main():
    try:
        with open('admin.html', 'r', encoding='utf-8') as f:
            html = f.read()

        # We will use regex to find the exact line and replace it
        # Pattern:
        # if (f.id === 'beszelgetes_naplo') {\n                return `<td>${val ? `<button onclick="openLogModal('${esc(btoa(encodeURIComponent(val)))}')" ... </td>`;\n            }
        
        pattern = re.compile(r"if \(f\.id === 'beszelgetes_naplo'\) \{\s*return `<td>\$\{val \? `<button onclick=\"openLogModal\('\$\{esc\(btoa\(encodeURIComponent\(val\)\)\)\}'\)\"(.*?)</td>`;\s*\}", re.DOTALL)
        
        replacement = r"""if (f.id === 'beszelgetes_naplo') {
                const safeName = esc(customObj.nev || customObj['név'] || customObj.name || 'Ismeretlen').replace(/'/g, "\\'");
                const safeDate = esc(fmtDt(c.created_at));
                return `<td>${val ? `<button onclick="openLogModal('${esc(btoa(encodeURIComponent(val)))}', '${safeName}', '${esc(csatorna)}', '${safeDate}')"\1</td>`;
            }"""
        
        new_html = pattern.sub(replacement, html)
        
        if new_html != html:
            with open('admin.html', 'w', encoding='utf-8') as f:
                f.write(new_html)
            print("Successfully updated openLogModal call!")
        else:
            print("Pattern not found!")
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
