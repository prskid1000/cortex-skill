"""claw xlsx table — register an Excel Table (structured reference) over a range."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


@click.command(name="table")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--sheet", required=True)
@click.option("--range", "a1_range", required=True)
@click.option("--name", "table_name", required=True,
              help="Excel Table display name (no spaces).")
@click.option("--style", "style_name", default="TableStyleMedium9")
@click.option("--totals", is_flag=True, help="Enable totals row.")
@common_output_options
def table(src: Path, sheet: str, a1_range: str, table_name: str,
          style_name: str, totals: bool,
          force: bool, backup: bool, as_json: bool, dry_run: bool,
          quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Register an Excel Table over a range and apply a TableStyle."""
    try:
        from openpyxl import load_workbook
        from openpyxl.worksheet.table import Table, TableStyleInfo
    except ImportError:
        die("openpyxl not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[xlsx]'", as_json=as_json)

    if dry_run:
        click.echo(f"would add table {table_name!r} over {sheet}!{a1_range}")
        return

    wb = load_workbook(src)
    ws = wb[sheet]

    tbl = Table(displayName=table_name, ref=a1_range, totalsRowShown=totals)
    tbl.tableStyleInfo = TableStyleInfo(
        name=style_name, showFirstColumn=False, showLastColumn=False,
        showRowStripes=True, showColumnStripes=False,
    )
    ws.add_table(tbl)

    def _save(f):
        wb.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "sheet": sheet, "range": a1_range,
                   "name": table_name, "style": style_name})
    elif not quiet:
        click.echo(f"added table {table_name} on {sheet}!{a1_range}")
