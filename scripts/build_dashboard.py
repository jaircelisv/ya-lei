#!/usr/bin/env python3
"""ya-lei — assemble digests/*.md into a single local HTML dashboard.

The dashboard is a self-contained file (dashboard/index.html): no CDNs, no
tracking, nothing leaves your machine. Open it in any browser.

Requires: Python 3 stdlib only.
"""

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIGESTS = ROOT / "digests"
OUT = ROOT / "dashboard" / "index.html"


def md_to_html(md: str) -> str:
    """Tiny markdown subset: headers, bold, italics, lists, hr, paragraphs."""
    out, in_list = [], False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for line in md.splitlines():
        s = line.rstrip()
        esc = html.escape(s, quote=False)
        esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)
        esc = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<em>\1</em>", esc)
        if s.startswith("### "):
            close_list(); out.append(f"<h4>{esc[4:]}</h4>")
        elif s.startswith("## "):
            close_list(); out.append(f"<h3>{esc[3:]}</h3>")
        elif s.startswith("# "):
            close_list(); out.append(f"<h2>{esc[2:]}</h2>")
        elif s.startswith(("- ", "* ")):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{esc[2:]}</li>")
        elif s.strip() in ("---", "***"):
            close_list(); out.append("<hr>")
        elif not s.strip():
            close_list()
        else:
            close_list(); out.append(f"<p>{esc}</p>")
    close_list()
    return "\n".join(out)


CSS = """
:root{--bg:#efeae2;--card:#fff;--ink:#111b21;--muted:#667781;--brand:#075e54;
--accent:#25d366;--check:#53bdeb;--bubble:#dcf8c6;--border:#e4ded4}
@media(prefers-color-scheme:dark){:root{--bg:#0b141a;--card:#111b21;--ink:#e9edef;
--muted:#8696a0;--brand:#00a884;--bubble:#005c4b;--border:#222e35}}
*{box-sizing:border-box;margin:0}
body{font:16px/1.6 -apple-system,'Segoe UI',Roboto,sans-serif;background:var(--bg);
color:var(--ink);padding:0 0 4rem}
header{background:var(--brand);color:#fff;padding:1.4rem 1.2rem;position:sticky;
top:0;z-index:2;display:flex;align-items:baseline;gap:.7rem;flex-wrap:wrap}
header h1{font-size:1.5rem;letter-spacing:-.02em}
header .checks{color:var(--check);font-weight:700}
header p{opacity:.85;font-size:.9rem}
main{max-width:860px;margin:1.5rem auto;padding:0 1rem;display:grid;gap:1.2rem}
nav{display:flex;gap:.5rem;flex-wrap:wrap}
nav a{background:var(--card);border:1px solid var(--border);color:var(--ink);
text-decoration:none;padding:.3rem .8rem;border-radius:999px;font-size:.85rem}
nav a:hover{border-color:var(--accent)}
article{background:var(--card);border:1px solid var(--border);border-radius:14px;
padding:1.4rem 1.6rem;overflow-x:auto}
article h2{color:var(--brand);font-size:1.2rem;margin-bottom:.6rem}
article h3{margin:1.1rem 0 .4rem;font-size:1.05rem;padding:.35rem .7rem;
background:var(--bubble);border-radius:9px;display:inline-block}
article h4{margin:.8rem 0 .3rem;color:var(--muted)}
article ul{padding-left:1.3rem;display:grid;gap:.25rem}
article p{margin:.5rem 0}
article em{color:var(--muted)}
article hr{border:0;border-top:1px solid var(--border);margin:1rem 0}
footer{text-align:center;color:var(--muted);font-size:.85rem;margin-top:2.5rem}
footer a{color:var(--brand)}
"""


def build():
    files = sorted(DIGESTS.glob("*.md"), reverse=True)
    if not files:
        print("ya-lei: no digests in digests/ yet — dashboard not built.", file=sys.stderr)
        sys.exit(0)

    nav = "".join(
        f'<a href="#{f.stem}">{f.stem}</a>' for f in files
    )
    articles = "".join(
        f'<article id="{f.stem}">{md_to_html(f.read_text(encoding="utf-8"))}</article>'
        for f in files
    )
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        "<!doctype html><html lang='es'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Ya Leí ✓✓</title><style>{CSS}</style></head><body>"
        "<header><h1><span class='checks'>✓✓</span> Ya Leí</h1>"
        "<p>tus grupos, ya leídos · your groups, already read</p></header>"
        f"<main><nav>{nav}</nav>{articles}"
        "<footer>Generado localmente por <a href='https://github.com/jaircelisv/ya-lei'>"
        "ya-lei</a> — nada de esto salió de tu máquina.</footer></main></body></html>",
        encoding="utf-8",
    )
    print(f"ya-lei: dashboard built → {OUT} ({len(files)} digest(s))", file=sys.stderr)


if __name__ == "__main__":
    build()
