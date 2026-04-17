"""claw docx table fit — switch table width between autofit and fixed."""

from __future__ import annotations

import re
from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


@click.group(name="table")
def table() -> None:
    """Table layout operations."""


@table.command(name="fit")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--index", "table_index", default=None, type=int,
              help="0-based table index.")
@click.option("--at", "anchor", default=None,
              help='Anchor text like "Table 1" to locate the table by neighbouring caption.')
@click.option("--mode", required=True, type=click.Choice(["autofit", "fixed"]))
@click.option("--widths", default=None,
              help='Comma-separated column widths (applies only in --mode fixed), e.g. "1in,3in,1in".')
@common_output_options
def table_fit(src: Path, table_index: int | None, anchor: str | None,
              mode: str, widths: str | None,
              force: bool, backup: bool, as_json: bool, dry_run: bool,
              quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Toggle autofit / fixed width on a table, optionally setting column widths."""
    try:
        from docx import Document
        from docx.shared import Cm, Emu, Inches, Pt
    except ImportError:
        die("python-docx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[docx]'", as_json=as_json)

    if table_index is None and anchor is None:
        die("pass --index or --at", code=EXIT_INPUT, as_json=as_json)

    if dry_run:
        click.echo(f"would set table fit={mode}")
        return

    doc = Document(str(src))
    tables = doc.tables

    idx = table_index
    if idx is None:
        # Anchor: find paragraph mentioning the anchor text; pick the next table after it.
        anchor_idx = None
        for i, para in enumerate(doc.paragraphs):
            if anchor and anchor in para.text:
                anchor_idx = i
                break
        if anchor_idx is None:
            die(f"anchor not found: {anchor!r}", code=EXIT_INPUT, as_json=as_json)
        # python-docx tables are in doc.tables in document order, so use Nth after anchor:
        m = re.search(r"(\d+)", anchor or "")
        idx = (int(m.group(1)) - 1) if m else 0

    if idx < 0 or idx >= len(tables):
        die(f"table index {idx} out of range (0..{len(tables) - 1})",
            code=EXIT_INPUT, as_json=as_json)
    tbl = tables[idx]
    tbl.autofit = (mode == "autofit")

    if mode == "fixed" and widths:
        parsed = [_parse_width(w) for w in widths.split(",")]
        for row in tbl.rows:
            for ci, cell in enumerate(row.cells):
                if ci < len(parsed) and parsed[ci] is not None:
                    cell.width = parsed[ci]

    def _save(f):
        doc.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "index": idx, "mode": mode,
                   "widths": widths})
    elif not quiet:
        click.echo(f"set table #{idx} fit={mode}")


def _parse_width(spec: str):
    from docx.shared import Cm, Emu, Inches, Pt

    s = spec.strip().lower()
    if s.endswith("in"):
        return Inches(float(s[:-2]))
    if s.endswith("cm"):
        return Cm(float(s[:-2]))
    if s.endswith("pt"):
        return Pt(float(s[:-2]))
    if not s:
        return None
    return Emu(int(s))
