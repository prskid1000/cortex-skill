"""claw xlsx print-setup — configure print area, titles, fit-to-page."""

from __future__ import annotations

import re
from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


@click.command(name="print-setup")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--sheet", required=True)
@click.option("--area", "print_area", default=None,
              help='Print area e.g. "A1:F1000".')
@click.option("--print-area", "print_area_alias", default=None,
              help='A1-range string to set as the sheet\'s print area (e.g. "A1:F1000").')
@click.option("--repeat-rows", "repeat_rows", default=None,
              help='Rows to repeat, e.g. "1:3" or "1:1".')
@click.option("--repeat-cols", "repeat_cols", default=None,
              help='Columns to repeat, e.g. "A:B".')
@click.option("--print-titles", "print_titles", default=None,
              help='Shorthand "rows:1:1" or "cols:A:A".')
@click.option("--fit-to", "fit_to", default=None,
              help='"WxH" pages, e.g. "1x999" for fit-to-1-wide.')
@click.option("--fit-width", "fit_width", default=None, type=int)
@click.option("--fit-height", "fit_height", default=None, type=int)
@click.option("--orientation", default=None,
              type=click.Choice(["portrait", "landscape"]))
@click.option("--paper-size", "paper_size", default=None,
              type=click.Choice(["A4", "Letter", "Legal", "A3"]))
@common_output_options
def print_setup(src: Path, sheet: str, print_area: str | None,
                print_area_alias: str | None,
                repeat_rows: str | None, repeat_cols: str | None,
                print_titles: str | None, fit_to: str | None,
                fit_width: int | None, fit_height: int | None,
                orientation: str | None, paper_size: str | None,
                force: bool, backup: bool, as_json: bool, dry_run: bool,
                quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Set print area, repeat titles, fit-to-page, orientation, paper size."""
    try:
        from openpyxl import load_workbook
    except ImportError:
        die("openpyxl not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[xlsx]'", as_json=as_json)

    if print_area_alias and not print_area:
        print_area = print_area_alias

    if fit_to:
        m = re.match(r"^(\d+)x(\d+)$", fit_to)
        if not m:
            die(f"invalid --fit-to: {fit_to!r}", code=EXIT_INPUT, as_json=as_json)
        fit_width = int(m.group(1))
        fit_height = int(m.group(2))

    if print_titles:
        kind, _, rng = print_titles.partition(":")
        if kind == "rows":
            repeat_rows = repeat_rows or rng
        elif kind == "cols":
            repeat_cols = repeat_cols or rng
        else:
            die(f"--print-titles must start with 'rows:' or 'cols:'",
                code=EXIT_INPUT, as_json=as_json)

    if dry_run:
        click.echo(f"would configure print on {sheet}")
        return

    wb = load_workbook(src)
    ws = wb[sheet]

    if print_area:
        ws.print_area = print_area
    if repeat_rows:
        ws.print_title_rows = repeat_rows
    if repeat_cols:
        ws.print_title_cols = repeat_cols
    if fit_width is not None or fit_height is not None:
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        if fit_width is not None:
            ws.page_setup.fitToWidth = fit_width
        if fit_height is not None:
            ws.page_setup.fitToHeight = fit_height
    if orientation:
        ws.page_setup.orientation = orientation
    if paper_size:
        paper_map = {"Letter": 1, "Legal": 5, "A4": 9, "A3": 8}
        ws.page_setup.paperSize = paper_map[paper_size]

    def _save(f):
        wb.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    info = {"path": str(src), "sheet": sheet, "area": print_area,
            "repeat_rows": repeat_rows, "repeat_cols": repeat_cols,
            "fit": (fit_width, fit_height), "orientation": orientation,
            "paper_size": paper_size}
    if as_json:
        emit_json(info)
    elif not quiet:
        click.echo(f"configured print on {sheet}")
