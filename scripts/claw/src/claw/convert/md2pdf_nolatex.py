"""claw convert md2pdf-nolatex — Markdown → PDF via pandoc HTML + PyMuPDF Story."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, EXIT_SYSTEM, common_output_options, die, emit_json, require, run, safe_write,
)


PAGE_SIZES = {
    "a4":     (595, 842),
    "letter": (612, 792),
    "legal":  (612, 1008),
    "a5":     (420, 595),
}


def _css_len_to_pts(spec: str) -> float:
    s = spec.strip().lower()
    if s.endswith("pt"):  return float(s[:-2])
    if s.endswith("mm"):  return float(s[:-2]) * 2.8346
    if s.endswith("cm"):  return float(s[:-2]) * 28.3464
    if s.endswith("in"):  return float(s[:-2]) * 72
    if s.endswith("px"):  return float(s[:-2]) * 0.75
    return float(s)


DEFAULT_CSS = """
body { font-family: %(font)s; font-size: 11pt; line-height: 1.45; color: #222; }
h1, h2, h3, h4 { color: #111; margin-top: 1.2em; }
h1 { font-size: 20pt; } h2 { font-size: 16pt; } h3 { font-size: 13pt; }
p  { margin: 0 0 0.7em 0; }
code, pre { font-family: monospace; background: #f5f5f5; }
pre { padding: 8px; border-radius: 4px; }
blockquote { border-left: 3px solid #ccc; padding-left: 12px; color: #555; }
table { border-collapse: collapse; }
th, td { border: 1px solid #bbb; padding: 4px 8px; }
"""


@click.command(name="md2pdf-nolatex")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.argument("dst", type=click.Path(path_type=Path))
@click.option("--css", "css_file", default=None, type=click.Path(exists=True, path_type=Path))
@click.option("--page-size", default="a4", type=click.Choice(list(PAGE_SIZES)))
@click.option("--margin", default="2cm")
@click.option("--font-family", "font_family", default="Helvetica,Arial,sans-serif")
@common_output_options
def md2pdf_nolatex(src: Path, dst: Path, css_file: Path | None, page_size: str,
                   margin: str, font_family: str,
                   force: bool, backup: bool, as_json: bool, dry_run: bool,
                   quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Render a Markdown file to PDF without needing LaTeX."""
    try:
        require("pandoc")
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, hint="winget install JohnMacFarlane.Pandoc", as_json=as_json)
    try:
        import fitz
    except ImportError:
        die("PyMuPDF (fitz) not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[pdf]'", as_json=as_json)

    if dry_run:
        click.echo(f"would render {src} -> {dst} (pandoc html + PyMuPDF)")
        return

    css = css_file.read_text(encoding="utf-8") if css_file else DEFAULT_CSS % {"font": font_family}

    with tempfile.TemporaryDirectory(prefix="claw-") as td:
        html_file = Path(td) / "body.html"
        try:
            run("pandoc", str(src), "-t", "html5", "-o", str(html_file))
        except Exception as e:
            die(f"pandoc failed: {e}", code=EXIT_SYSTEM, as_json=as_json)

        body_html = html_file.read_text(encoding="utf-8")
        full_html = f"<html><head><style>{css}</style></head><body>{body_html}</body></html>"

        w, h = PAGE_SIZES[page_size]
        m = _css_len_to_pts(margin)
        rect = fitz.Rect(m, m, w - m, h - m)

        # Render straight to a BytesIO — writing to a file inside `td` and
        # reading it back leaks an mmap on Windows that blocks TemporaryDirectory
        # cleanup. PyMuPDF's DocumentWriter accepts any file-like object.
        story = fitz.Story(html=full_html)
        buf = io.BytesIO()
        writer = fitz.DocumentWriter(buf)
        more = 1
        while more:
            dev = writer.begin_page(fitz.Rect(0, 0, w, h))
            more, _ = story.place(rect)
            story.draw(dev)
            writer.end_page()
        writer.close()
        data = buf.getvalue()

    safe_write(dst, lambda f: f.write(data), force=force, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"src": str(src), "dst": str(dst), "page_size": page_size})
    elif not quiet:
        click.echo(f"wrote {dst}")
