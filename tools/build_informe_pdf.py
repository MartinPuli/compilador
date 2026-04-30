"""Render docs/informe.md to docs/informe.pdf.

Pure-Python pipeline (no LaTeX / WeasyPrint / wkhtmltopdf needed):
    1. Read the markdown file.
    2. Convert to HTML with the `markdown` library (with table + fenced
       code support).
    3. Wrap it in a print-friendly HTML/CSS document.
    4. Render to PDF with `xhtml2pdf` (which is built on reportlab and
       runs anywhere Python runs).

Usage:
    py -3.12 tools/build_informe_pdf.py

Both `markdown` and `xhtml2pdf` are installed on demand (pip).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MD = REPO / "docs" / "informe.md"
PDF = REPO / "docs" / "informe.pdf"


def _ensure(pkg: str) -> None:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])


def _wrap_html(body_html: str) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Informe — MorseLang</title>
<style>
@page {{
    size: A4;
    margin: 2cm 2.2cm;
    @frame footer {{
        -pdf-frame-content: footer-content;
        bottom: 1cm;
        margin-left: 2cm;
        margin-right: 2cm;
        height: 1cm;
    }}
}}
body {{
    font-family: "Times New Roman", Georgia, serif;
    font-size: 11pt;
    line-height: 1.45;
    color: #1f1a14;
}}
h1 {{
    font-size: 22pt;
    color: #1f1a14;
    border-bottom: 2px solid #1f1a14;
    padding-bottom: 4pt;
    margin: 0 0 14pt;
}}
h2 {{
    font-size: 15pt;
    color: #b56200;
    margin: 22pt 0 8pt;
    border-bottom: 1px solid #d8c8a8;
    padding-bottom: 3pt;
}}
h3 {{
    font-size: 12.5pt;
    color: #1f1a14;
    margin: 16pt 0 4pt;
}}
p {{ margin: 0 0 9pt; }}
ul, ol {{ margin: 0 0 9pt 18pt; padding: 0; }}
li {{ margin: 0 0 3pt; }}
code {{
    font-family: "Consolas", "Courier New", monospace;
    font-size: 9.5pt;
    background: #faf5ec;
    padding: 1pt 3pt;
    border: 1px solid #e4d6bb;
}}
pre {{
    font-family: "Consolas", "Courier New", monospace;
    font-size: 9pt;
    background: #faf5ec;
    padding: 8pt 10pt;
    border-left: 3px solid #ff9500;
    border-radius: 0;
    margin: 6pt 0 12pt;
    white-space: pre;
}}
pre code {{
    background: transparent;
    border: 0;
    padding: 0;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 6pt 0 14pt;
    font-size: 9.5pt;
}}
th, td {{
    border: 1px solid #c9b48b;
    padding: 4pt 7pt;
    text-align: left;
    vertical-align: top;
}}
th {{
    background: #f1e4c8;
    font-weight: bold;
}}
blockquote {{
    border-left: 3px solid #ff9500;
    padding: 0 12pt;
    color: #4a3c2a;
    font-style: italic;
    margin: 0 0 9pt;
}}
em {{ font-style: italic; }}
strong {{ font-weight: bold; }}
hr {{
    border: 0;
    border-top: 1px solid #c9b48b;
    margin: 14pt 0;
}}
.footer {{
    font-size: 8pt;
    color: #8a7d68;
    text-align: center;
}}
</style>
</head>
<body>
{body_html}
<div id="footer-content" class="footer">
    Informe MorseLang — TP integrador, Lenguajes Formales y Compiladores
</div>
</body>
</html>"""


def main() -> int:
    _ensure("markdown")
    _ensure("xhtml2pdf")

    import markdown
    from xhtml2pdf import pisa

    if not MD.is_file():
        print(f"error: no se encontró {MD}", file=sys.stderr)
        return 1

    md_text = MD.read_text(encoding="utf-8")
    body_html = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists"],
    )
    full = _wrap_html(body_html)

    PDF.parent.mkdir(parents=True, exist_ok=True)
    with open(PDF, "wb") as f:
        result = pisa.CreatePDF(full, dest=f, encoding="utf-8")

    if result.err:
        print(f"error: {result.err} errores al renderizar", file=sys.stderr)
        return 1
    print(f"PDF escrito en {PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
