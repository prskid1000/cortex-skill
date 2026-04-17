"""claw pdf toc — read / write the document outline."""
from __future__ import annotations

import json
from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, safe_write


@click.group(name="toc")
def toc() -> None:
    """Read / write the table of contents (outline)."""


@toc.command(name="get")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
def toc_get(src: Path, as_json: bool) -> None:
    """Print the current outline as a JSON array."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    doc = fitz.open(str(src))
    try:
        entries = doc.get_toc(simple=False)
    finally:
        doc.close()

    if as_json:
        emit_json(entries)
        return
    click.echo(json.dumps(entries, ensure_ascii=False, indent=2, default=str))


@toc.command(name="set")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--json", "json_path", required=True,
              type=click.Path(exists=True, dir_okay=False, path_type=Path),
              help="Path to JSON array matching doc.set_toc(...).")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True)
@common_output_options
def toc_set(src: Path, json_path: Path, out: Path | None, in_place: bool,
            force: bool, backup: bool, as_json: bool, dry_run: bool,
            quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Overwrite the outline of <SRC> from --json FILE."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    if not (out or in_place):
        die("pass --out FILE or --in-place", code=2)
    target = src if in_place else out
    assert target is not None

    entries = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        die("--json must contain a JSON array", code=2)

    doc = fitz.open(str(src))
    try:
        doc.set_toc(entries)
        if dry_run:
            click.echo(f"would write {len(entries)} TOC entries → {target}")
            return
        data = doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()

    safe_write(target, lambda f: f.write(data),
               force=force or in_place, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(target), "entries": len(entries)})
    elif not quiet:
        click.echo(f"wrote {len(entries)} TOC entries → {target}")
