"""claw xlsx from-json — build a workbook from a JSON array of rows."""

from __future__ import annotations

import json
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, common_output_options, die, emit_json, read_text, safe_write,
)


@click.command(name="from-json")
@click.argument("out", type=click.Path(path_type=Path))
@click.option("--data", "data_src", required=True, help="JSON file or - for stdin.")
@click.option("-s", "--sheet", default="Data",
              help="Sheet name to write the rows into.")
@click.option("--flatten", is_flag=True, help="Flatten nested objects using dot notation.")
@common_output_options
def from_json(out: Path, data_src: str, sheet: str, flatten: bool,
              force: bool, backup: bool, as_json: bool, dry_run: bool,
              quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Build a workbook from a JSON array of row objects."""
    try:
        from openpyxl import Workbook
    except ImportError:
        die("openpyxl not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[xlsx]'", as_json=as_json)

    data = json.loads(read_text(data_src))
    if isinstance(data, dict):
        data = [data]

    if flatten:
        data = [_flatten(r) for r in data]

    if dry_run:
        click.echo(f"would write {out} with {len(data)} rows")
        return

    keys: list[str] = []
    for r in data:
        for k in r:
            if k not in keys:
                keys.append(k)

    wb = Workbook()
    ws = wb.active
    ws.title = sheet
    if keys:
        ws.append(keys)
        for r in data:
            ws.append([r.get(k) for k in keys])

    def _save(f):
        wb.save(f)

    safe_write(out, _save, force=force, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(out), "sheet": sheet, "rows": len(data), "cols": len(keys)})
    elif not quiet:
        click.echo(f"wrote {out} ({len(data)} rows, {len(keys)} cols)")


def _flatten(obj, prefix: str = "") -> dict:
    out: dict = {}
    for k, v in obj.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = v
    return out
