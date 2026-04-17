"""claw pdf from-html — HTML → PDF via PyMuPDF Story API."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, safe_write


PAGE_SIZES = {
    "Letter": (612, 792),
    "Legal":  (612, 1008),
    "A4":     (595, 842),
    "A3":     (842, 1191),
}


def _inline_linked_css(html: str, base_dir: Path, fetch_remote: bool,
                      quiet: bool) -> tuple[str, str]:
    """Strip <link rel="stylesheet"> tags from html; return (cleaned_html, collected_css).

    Local hrefs are read from disk relative to base_dir. Remote (http/https)
    hrefs are skipped with a stderr warning unless fetch_remote is True, in
    which case they are fetched via urllib.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        die("beautifulsoup4 not installed; install: pip install 'claw[pdf]'")

    soup = BeautifulSoup(html, "html.parser")
    css_parts: list[str] = []
    for link in list(soup.find_all("link")):
        rel = link.get("rel") or []
        if isinstance(rel, str):
            rel = [rel]
        if "stylesheet" not in [r.lower() for r in rel]:
            continue
        href = link.get("href")
        if not href:
            link.decompose()
            continue
        if href.startswith(("http://", "https://")):
            if fetch_remote:
                try:
                    import urllib.request
                    with urllib.request.urlopen(href, timeout=10) as resp:
                        css_parts.append(resp.read().decode("utf-8", errors="replace"))
                except Exception as e:
                    if not quiet:
                        click.echo(f"warning: failed to fetch {href}: {e}", err=True)
            else:
                if not quiet:
                    click.echo(f"warning: skipping remote stylesheet {href} "
                               f"(pass --fetch-remote-css to include)", err=True)
            link.decompose()
            continue
        path = (base_dir / href).resolve()
        try:
            css_parts.append(path.read_text(encoding="utf-8"))
        except OSError as e:
            if not quiet:
                click.echo(f"warning: could not read {path}: {e}", err=True)
        link.decompose()

    for style in soup.find_all("style"):
        if style.string:
            css_parts.append(style.string)

    return str(soup), "\n\n".join(css_parts)


@click.command(name="from-html")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("out", type=click.Path(path_type=Path))
@click.option("--page-size", default="Letter", type=click.Choice(list(PAGE_SIZES)))
@click.option("--rect", default=None, help='Content rect "x0,y0,x1,y1" in points.')
@click.option("--css", "css_file", type=click.Path(exists=True, dir_okay=False, path_type=Path),
              default=None)
@click.option("--fetch-remote-css", is_flag=True,
              help="Fetch http(s) stylesheets referenced by <link>; otherwise skipped with warning.")
@common_output_options
def from_html(src: Path, out: Path, page_size: str, rect: str | None, css_file: Path | None,
              fetch_remote_css: bool,
              force: bool, backup: bool, as_json: bool, dry_run: bool,
              quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Convert HTML <SRC> to PDF <OUT> via PyMuPDF Story."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    html = src.read_text(encoding="utf-8")
    html, linked_css = _inline_linked_css(html, src.parent, fetch_remote_css, quiet)

    user_css_parts: list[str] = []
    if linked_css:
        user_css_parts.append(linked_css)
    if css_file:
        user_css_parts.append(css_file.read_text(encoding="utf-8"))
    css = "\n\n".join(user_css_parts) if user_css_parts else None

    w, h = PAGE_SIZES[page_size]
    if rect:
        coords = [float(x) for x in rect.split(",")]
        if len(coords) != 4:
            die("--rect must be x0,y0,x1,y1", code=2)
        content_rect = fitz.Rect(*coords)
    else:
        content_rect = fitz.Rect(72, 72, w - 72, h - 72)

    if dry_run:
        click.echo(f"would render {src} → {out} ({page_size})")
        return

    story = fitz.Story(html=html, user_css=css) if css else fitz.Story(html=html)
    writer = fitz.DocumentWriter(str(out))
    more = True
    pages = 0
    while more:
        device = writer.begin_page(fitz.Rect(0, 0, w, h))
        more, _ = story.place(content_rect)
        story.draw(device)
        writer.end_page()
        pages += 1
        if pages > 10000:
            die("runaway page generation (>10000)")
    writer.close()

    if as_json:
        emit_json({"out": str(out), "pages": pages, "page_size": page_size})
    elif not quiet:
        click.echo(f"wrote {out} ({pages} pages)")
