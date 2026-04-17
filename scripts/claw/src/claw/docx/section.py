"""claw docx section — add a new section with custom page layout."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


PAPER_SIZES = {
    "Letter": (8.5, 11.0),
    "Legal":  (8.5, 14.0),
    "A4":     (8.27, 11.69),
    "A3":     (11.69, 16.54),
}


@click.group(name="section")
def section() -> None:
    """Section operations."""


@section.command(name="add")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--orientation", default=None,
              type=click.Choice(["portrait", "landscape"]))
@click.option("--columns", "columns", default=None, type=int,
              help="Column count for the section body.")
@click.option("--cols", "cols_alias", default=None, type=int, hidden=True)
@click.option("--margin-top", "margin_top", default=None, type=float)
@click.option("--margin-bottom", "margin_bottom", default=None, type=float)
@click.option("--margin-left", "margin_left", default=None, type=float)
@click.option("--margin-right", "margin_right", default=None, type=float)
@click.option("--page-size", "page_size", default=None,
              type=click.Choice(list(PAPER_SIZES.keys())))
@click.option("--start-type", "start_type", default=None,
              type=click.Choice(["continuous", "new-page", "odd-page", "even-page"]))
@common_output_options
def section_add(src: Path, orientation: str | None, columns: int | None,
                cols_alias: int | None,
                margin_top: float | None, margin_bottom: float | None,
                margin_left: float | None, margin_right: float | None,
                page_size: str | None, start_type: str | None,
                force: bool, backup: bool, as_json: bool, dry_run: bool,
                quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Append a new section to the document."""
    try:
        from docx import Document
        from docx.enum.section import WD_ORIENT, WD_SECTION
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.shared import Inches
    except ImportError:
        die("python-docx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[docx]'", as_json=as_json)

    col_count = columns if columns is not None else cols_alias

    if dry_run:
        click.echo(f"would add section (orientation={orientation}, cols={col_count})")
        return

    doc = Document(str(src))
    start_map = {
        "continuous": WD_SECTION.CONTINUOUS,
        "new-page": WD_SECTION.NEW_PAGE,
        "odd-page": WD_SECTION.ODD_PAGE,
        "even-page": WD_SECTION.EVEN_PAGE,
    }
    wd_start = start_map.get(start_type, WD_SECTION.NEW_PAGE)
    sec = doc.add_section(wd_start)

    if orientation:
        sec.orientation = (WD_ORIENT.LANDSCAPE if orientation == "landscape"
                           else WD_ORIENT.PORTRAIT)
        if orientation == "landscape":
            sec.page_width, sec.page_height = sec.page_height, sec.page_width

    if page_size:
        w_in, h_in = PAPER_SIZES[page_size]
        if sec.orientation and orientation == "landscape":
            w_in, h_in = h_in, w_in
        sec.page_width = Inches(w_in)
        sec.page_height = Inches(h_in)

    if margin_top is not None:
        sec.top_margin = Inches(margin_top)
    if margin_bottom is not None:
        sec.bottom_margin = Inches(margin_bottom)
    if margin_left is not None:
        sec.left_margin = Inches(margin_left)
    if margin_right is not None:
        sec.right_margin = Inches(margin_right)

    if col_count and col_count > 1:
        sect_pr = sec._sectPr
        cols_el = sect_pr.find(qn("w:cols"))
        if cols_el is None:
            cols_el = OxmlElement("w:cols")
            sect_pr.append(cols_el)
        cols_el.set(qn("w:num"), str(col_count))
        cols_el.set(qn("w:space"), "720")

    def _save(f):
        doc.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "orientation": orientation,
                   "columns": col_count, "page_size": page_size,
                   "start_type": start_type})
    elif not quiet:
        click.echo(f"added section (orientation={orientation}, cols={col_count})")
