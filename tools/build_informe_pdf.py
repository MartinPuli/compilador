"""Render docs/informe.md to docs/informe.pdf with the MORSE.LAB branding.

Uses headless Chromium (via Playwright) so the actual web fonts that the
site uses — Fraunces italic serif + JetBrains Mono — are loaded from
Google Fonts and the PDF visually matches the demo. The CSS is a
print-adapted version of the website palette: warm cream paper, deep
ink text, amber accents, magazine-style numbered sections.

Usage:
    py -3.12 tools/build_informe_pdf.py

On first run it auto-installs `markdown` and `playwright` from PyPI and
fetches the Chromium binary via `playwright install chromium`.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MD = REPO / "docs" / "informe.md"
PDF = REPO / "docs" / "informe.pdf"


def _ensure(pkg: str, importname: str | None = None) -> None:
    try:
        __import__(importname or pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])


def _ensure_chromium() -> None:
    try:
        subprocess.check_call(
            [sys.executable, "-m", "playwright", "install", "chromium"]
        )
    except subprocess.CalledProcessError:
        pass  # chromium may already be installed by another tool


def _wrap_html(body_html: str) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Informe — MorseLang</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;1,9..144,400;1,9..144,600&family=JetBrains+Mono:wght@300;400;500;700&display=swap">
<style>
:root {{
  --paper:    #fbf6e9;
  --paper-2:  #f5edd8;
  --ink:      #1f1a14;
  --ink-dim:  #4a3c2a;
  --ink-faint:#8a7d68;
  --amber:    #b56a00;
  --amber-2:  #ff9500;
  --line:     #c9b48b;
  --line-soft:#e4d6bb;
  --code-bg:  #f5edd8;
}}

@page {{
  size: A4;
  margin: 0;
}}

* {{ box-sizing: border-box; }}

html, body {{
  margin: 0;
  padding: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: 'Fraunces', Georgia, serif;
  font-size: 10.5pt;
  line-height: 1.55;
}}

body {{
  counter-reset: section;
}}

/* ===== COVER ===== */

.cover {{
  page-break-after: always;
  page: cover;
  height: 297mm;
  padding: 30mm 24mm 18mm;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  text-align: center;
  position: relative;
  border-top: 6px solid var(--amber);
  background:
    radial-gradient(60% 50% at 50% 35%, rgba(255, 149, 0, 0.06), transparent 70%),
    var(--paper);
}}

.cover-stamp {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 8pt;
  letter-spacing: 0.42em;
  color: var(--ink-dim);
  text-transform: uppercase;
  border: 1px solid var(--line);
  padding: 6pt 18pt;
  border-radius: 999px;
  background: rgba(245, 237, 216, 0.4);
}}

.cover-mid {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14pt;
}}

.cover-overline {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 9pt;
  letter-spacing: 0.42em;
  color: var(--amber);
  text-transform: uppercase;
}}

.cover-title {{
  font-family: 'Fraunces', serif;
  font-style: italic;
  font-weight: 400;
  font-size: 110pt;
  line-height: 0.92;
  letter-spacing: -0.02em;
  margin: 0;
  color: var(--ink);
}}

.cover-title .dot {{
  font-style: normal;
  font-family: 'JetBrains Mono', monospace;
  color: var(--amber);
  font-size: 0.4em;
  vertical-align: 0.35em;
  margin: 0 0.04em;
  font-weight: 700;
}}

.cover-sub {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5pt;
  letter-spacing: 0.22em;
  color: var(--ink-dim);
  text-transform: uppercase;
}}

.cover-sub .op {{ color: var(--amber); }}

.cover-meta {{
  font-family: 'Fraunces', serif;
  font-size: 13pt;
  color: var(--ink);
  text-align: center;
}}

.cover-meta .lead {{
  font-style: italic;
  font-size: 16pt;
  color: var(--amber);
  display: block;
  margin-bottom: 4pt;
}}

.cover-foot {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 8pt;
  letter-spacing: 0.18em;
  color: var(--ink-faint);
  text-transform: uppercase;
  display: flex;
  flex-direction: column;
  gap: 4pt;
}}

.cover-foot a {{
  color: var(--ink-dim);
  text-decoration: none;
}}

.cover-foot .op {{ color: var(--amber); margin: 0 8pt; }}

.cover-mark {{
  width: 56pt;
  height: 56pt;
  color: var(--amber);
}}

/* ===== BODY PAGES ===== */

@page body-page {{
  size: A4;
  margin: 16mm 14mm 18mm 14mm;
  @bottom-left {{
    content: 'MorseLang · Informe';
    font-family: 'JetBrains Mono', monospace;
    font-size: 8pt;
    color: var(--ink-faint);
    letter-spacing: 0.22em;
    text-transform: uppercase;
  }}
  @bottom-right {{
    content: counter(page);
    font-family: 'JetBrains Mono', monospace;
    font-size: 8pt;
    color: var(--ink-faint);
  }}
}}

article {{
  page: body-page;
}}

h1 {{
  font-family: 'Fraunces', serif;
  font-style: italic;
  font-weight: 400;
  font-size: 28pt;
  line-height: 1;
  color: var(--ink);
  border-bottom: 1px solid var(--line);
  padding-bottom: 8pt;
  margin: 0 0 18pt;
  letter-spacing: -0.01em;
}}

h2 {{
  font-family: 'Fraunces', serif;
  font-weight: 400;
  font-size: 18pt;
  margin: 32pt 0 10pt;
  color: var(--ink);
  position: relative;
  padding-left: 64pt;
  page-break-after: avoid;
  page-break-before: auto;
  counter-increment: section;
  border-top: 1px solid var(--line-soft);
  padding-top: 22pt;
  letter-spacing: -0.005em;
}}

h2:first-of-type {{
  border-top: 0;
  padding-top: 8pt;
  margin-top: 14pt;
}}

h2::before {{
  content: counter(section, decimal-leading-zero);
  position: absolute;
  left: 0;
  top: 18pt;
  font-family: 'Fraunces', serif;
  font-style: italic;
  font-size: 40pt;
  color: var(--amber);
  line-height: 1;
  letter-spacing: -0.02em;
}}

h2 em {{
  font-style: italic;
  color: var(--amber);
}}

h3 {{
  font-family: 'Fraunces', serif;
  font-style: italic;
  font-weight: 400;
  font-size: 13pt;
  color: var(--amber);
  margin: 18pt 0 6pt;
  page-break-after: avoid;
  letter-spacing: 0;
}}

h4 {{
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 9pt;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--ink-dim);
  margin: 14pt 0 6pt;
}}

p {{ margin: 0 0 9pt; }}

ul, ol {{
  margin: 0 0 12pt 18pt;
  padding: 0;
}}

li {{ margin: 0 0 4pt; }}

strong {{ font-weight: 600; color: var(--ink); }}
em     {{ font-style: italic; }}

a {{
  color: var(--amber);
  text-decoration: none;
  border-bottom: 1px dotted var(--line);
}}

code {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 9pt;
  background: var(--code-bg);
  padding: 1pt 5pt;
  border: 1px solid var(--line-soft);
  border-radius: 3pt;
  color: var(--ink);
}}

pre {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 8.5pt;
  background: var(--code-bg);
  padding: 12pt 16pt;
  border-left: 3px solid var(--amber);
  border-radius: 0;
  margin: 8pt 0 14pt;
  white-space: pre;
  overflow: visible;
  page-break-inside: avoid;
  line-height: 1.6;
  color: var(--ink);
}}

pre code {{
  background: transparent;
  border: 0;
  padding: 0;
  font-size: inherit;
  color: inherit;
}}

table {{
  border-collapse: collapse;
  width: 100%;
  margin: 8pt 0 14pt;
  font-size: 9.5pt;
  page-break-inside: avoid;
}}

th, td {{
  border: 1px solid var(--line);
  padding: 6pt 10pt;
  text-align: left;
  vertical-align: top;
}}

th {{
  background: rgba(181, 106, 0, 0.10);
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 8.5pt;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink);
}}

td code, th code {{ font-size: 8.5pt; padding: 0 3pt; }}

blockquote {{
  border-left: 3px solid var(--amber);
  padding: 4pt 14pt;
  color: var(--ink-dim);
  font-family: 'Fraunces', serif;
  font-style: italic;
  margin: 9pt 0 12pt;
  background: rgba(245, 237, 216, 0.5);
}}

hr {{
  border: 0;
  border-top: 1px solid var(--line-soft);
  margin: 18pt 0;
}}

</style>
</head>
<body>

<!-- ============== COVER ============== -->
<section class="cover">
  <div class="cover-stamp">EST. 2026 · BUENOS AIRES · v1.0</div>

  <div class="cover-mid">
    <div class="cover-overline">— UN COMPILADOR EN CÓDIGO MORSE —</div>
    <h1 class="cover-title">Morse<span class="dot">·</span><i>Lab</i></h1>
    <div class="cover-sub">
      <span class="op">/</span> léxico
      <span class="op">·</span> sintáctico
      <span class="op">·</span> semántico
      <span class="op">·</span> intérprete
      <span class="op">·</span> tts
      <span class="op">/</span>
    </div>
    <svg class="cover-mark" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
      <rect x="3" y="3" width="58" height="58" rx="8" fill="none" stroke="currentColor" stroke-width="1.5" stroke-opacity="0.35"/>
      <rect x="12" y="14" width="22" height="4" fill="currentColor"/>
      <rect x="12" y="22" width="22" height="4" fill="currentColor"/>
      <circle cx="14" cy="44" r="2.5" fill="currentColor"/>
      <rect x="20" y="42" width="14" height="4" fill="currentColor"/>
      <circle cx="40" cy="44" r="2.5" fill="currentColor"/>
      <circle cx="48" cy="44" r="2.5" fill="currentColor"/>
      <circle cx="52" cy="14" r="3" fill="currentColor"/>
    </svg>
    <div class="cover-meta">
      <span class="lead">Informe del TP integrador</span>
      Lenguajes Formales y Compiladores<br/>
      Python 3.12 · 74 tests · todo a mano
    </div>
  </div>

  <div class="cover-foot">
    <span>github.com/MartinPuli/compilador <span class="op">·</span> compilador-swart.vercel.app</span>
  </div>
</section>

<!-- ============== BODY ============== -->
<article>
{body_html}
</article>

</body>
</html>"""


def _strip_section_numbers(body_html: str) -> str:
    """Strip leading 'N. ' from h2 headings — CSS counter renders the number."""
    return re.sub(r"<h2>\s*\d+\.\s+", "<h2>", body_html)


def _drop_top_h1(body_html: str) -> str:
    """Remove the document-level H1 from the body since the cover already
    shows the title."""
    return re.sub(r"<h1>.*?</h1>", "", body_html, count=1, flags=re.DOTALL)


def main() -> int:
    _ensure("markdown")
    _ensure("playwright")
    _ensure_chromium()

    import markdown
    from playwright.sync_api import sync_playwright

    if not MD.is_file():
        print(f"error: no se encontró {MD}", file=sys.stderr)
        return 1

    md_text = MD.read_text(encoding="utf-8")
    body_html = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
    )
    body_html = _drop_top_h1(body_html)
    body_html = _strip_section_numbers(body_html)
    full = _wrap_html(body_html)

    PDF.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(full, wait_until="networkidle")
        page.emulate_media(media="print")
        page.pdf(
            path=str(PDF),
            format="A4",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        browser.close()

    print(f"PDF escrito en {PDF} ({PDF.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
