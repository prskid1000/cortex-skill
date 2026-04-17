"""claw xlsx protect — password-protect a sheet or the workbook structure."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


ALLOWABLE = {
    "select-locked": "selectLockedCells", "select-unlocked": "selectUnlockedCells",
    "format-cells": "formatCells", "format-columns": "formatColumns",
    "format-rows": "formatRows", "insert-columns": "insertColumns",
    "insert-rows": "insertRows", "insert-hyperlinks": "insertHyperlinks",
    "delete-columns": "deleteColumns", "delete-rows": "deleteRows",
    "sort": "sort", "auto-filter": "autoFilter", "pivot-tables": "pivotTables",
    "objects": "objects", "scenarios": "scenarios",
}


@click.command(name="protect")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--scope", required=True,
              type=click.Choice(["sheet", "workbook", "both"]))
@click.option("--sheet", default=None)
@click.option("--password", default=None)
@click.option("--allow", default="", help="Comma-separated actions to permit.")
@click.option("--lock-structure", "lock_structure", is_flag=True,
              help="Workbook scope: prevent sheet add/delete/reorder/rename.")
@click.option("--lock-windows", "lock_windows", is_flag=True,
              help="Workbook scope: prevent window resize/move.")
@click.option("--clear", is_flag=True, help="Remove protection instead of applying it.")
@common_output_options
def protect(src: Path, scope: str, sheet: str | None, password: str | None,
            allow: str, lock_structure: bool, lock_windows: bool, clear: bool,
            force: bool, backup: bool, as_json: bool, dry_run: bool,
            quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Apply or clear sheet/workbook password protection."""
    try:
        from openpyxl import load_workbook
        from openpyxl.workbook.protection import WorkbookProtection
        from openpyxl.utils.protection import hash_password
    except ImportError:
        die("openpyxl not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[xlsx]'", as_json=as_json)

    if not clear and not password:
        die("--password required unless --clear is given",
            code=EXIT_INPUT, as_json=as_json)

    if dry_run:
        click.echo(f"would {'clear' if clear else 'apply'} {scope} protection on {src}")
        return

    wb = load_workbook(src)
    allowed = {ALLOWABLE[a.strip()] for a in allow.split(",") if a.strip() in ALLOWABLE}

    scopes = {"sheet", "workbook"} if scope == "both" else {scope}

    if "sheet" in scopes:
        if not sheet:
            die("--sheet required for sheet scope", code=EXIT_INPUT, as_json=as_json)
        ws = wb[sheet]
        if clear:
            ws.protection.sheet = False
            ws.protection.password = None
        else:
            ws.protection.sheet = True
            ws.protection.password = password
            for key in ALLOWABLE.values():
                if hasattr(ws.protection, key):
                    setattr(ws.protection, key, key in allowed)

    if "workbook" in scopes:
        if clear:
            wb.security = None
        else:
            hashed = hash_password(password)
            structure = lock_structure or not lock_windows
            prot = WorkbookProtection(
                lockStructure=structure,
                lockWindows=bool(lock_windows),
            )
            prot.set_workbook_password(hashed, already_hashed=True)
            wb.security = prot

    def _save(f):
        wb.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "scope": scope, "cleared": clear,
                   "sheet": sheet, "lock_structure": lock_structure,
                   "lock_windows": lock_windows})
    elif not quiet:
        click.echo(f"{'cleared' if clear else 'applied'} {scope} protection")
