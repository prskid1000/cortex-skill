"""claw xlsx from-html — extract HTML tables into a multi-sheet workbook."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, read_text, safe_write


@click.command(name="from-html")
@click.argument("out", type=click.Path(path_type=Path))
@click.option("--data", "data_src", required=True,
              help="Path to HTML file, a URL, or '-' for stdin.")
@click.option("--select", "css_select", default="table",
              help="CSS selector for tables (default 'table').")
@click.option("--sheet-from", "sheet_from", default="index",
              type=click.Choice(["caption", "h2", "index"]),
              help="How to name each sheet.")
@common_output_options
def from_html(out: Path, data_src: str, css_select: str, sheet_from: str,
              force: bool, backup: bool, as_json: bool, dry_run: bool,
              quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Parse HTML tables and write each as a sheet in <out>."""
    try:
        from bs4 import BeautifulSoup
        from openpyxl import Workbook
    except ImportError:
        die("openpyxl and beautifulsoup4 required", code=EXIT_INPUT,
            hint="uv tool install 'claw[xlsx,html]'", as_json=as_json)

    if data_src.startswith(("http://", "https://")):
        try:
            import urllib.request
            with urllib.request.urlopen(data_src) as resp:
                html = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            die(f"failed to fetch {data_src}: {e}", code=EXIT_INPUT, as_json=as_json)
    else:
        html = read_text(data_src)

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.select(css_select)
    if not tables:
        die(f"no tables matched {css_select!r}", code=EXIT_INPUT, as_json=as_json)

    if dry_run:
        click.echo(f"would write {out} with {len(tables)} sheet(s)")
        return

    wb = Workbook()
    wb.remove(wb.active)

    sheets: list[str] = []
    seen: set[str] = set()
    for idx, tbl in enumerate(tables, start=1):
        name = None
        if sheet_from == "caption":
            cap = tbl.find("caption")
            if cap and cap.get_text(strip=True):
                name = cap.get_text(strip=True)
        elif sheet_from == "h2":
            prev = tbl.find_previous(["h1", "h2", "h3"])
            if prev and prev.get_text(strip=True):
                name = prev.get_text(strip=True)
        if not name:
            name = f"Table{idx}"
        name = name[:31].strip() or f"Table{idx}"
        base = name
        n = 2
        while name in seen:
            suffix = f" ({n})"
            name = (base[:31 - len(suffix)] + suffix)
            n += 1
        seen.add(name)

        ws = wb.create_sheet(title=name)
        for tr in tbl.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            ws.append([c.get_text(" ", strip=True) for c in cells])
        sheets.append(name)

    def _save(f):
        wb.save(f)

    safe_write(out, _save, force=force, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(out), "sheets": sheets})
    elif not quiet:
        click.echo(f"wrote {out} with sheets: {', '.join(sheets)}")
