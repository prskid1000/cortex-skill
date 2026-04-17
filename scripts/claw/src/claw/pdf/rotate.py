"""claw pdf rotate — rotate pages."""
from __future__ import annotations

from pathlib import Path

import click

from claw.common import PageSelector, common_output_options, die, emit_json, safe_write


@click.command(name="rotate")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--pages", default="all", help="Page range.")
@click.option("--by", "angle", type=click.Choice(["90", "-90", "180", "270"]),
              required=True, help="Rotation angle in degrees.")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True, help="Write back to <SRC>.")
@click.option("--journal", "journal_name", default=None,
              help="Name of an open journal session; emits a log entry describing this rotate op.")
@common_output_options
def rotate(src: Path, pages: str, angle: str, out: Path | None, in_place: bool,
           journal_name: str | None,
           force: bool, backup: bool, as_json: bool, dry_run: bool,
           quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Rotate pages of <SRC> by --by degrees."""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        die("pypdf not installed; install: pip install 'claw[pdf]'")

    if not (out or in_place):
        die("pass --out FILE or --in-place", code=2)
    target = src if in_place else Path(out) if out else None
    assert target is not None

    reader = PdfReader(str(src))
    total = len(reader.pages)
    targets = set(PageSelector(pages).resolve(total))
    by = int(angle)

    writer = PdfWriter()
    for i, page in enumerate(reader.pages, start=1):
        if i in targets:
            page.rotate(by)
        writer.add_page(page)

    if dry_run:
        click.echo(f"would rotate {len(targets)} of {total} pages by {by}° → {target}")
        return

    safe_write(target, lambda f: writer.write(f),
               force=force or in_place, backup=backup, mkdir=mkdir)
    if journal_name:
        from claw.pdf.journal import append_entry as _journal_append
        _journal_append(journal_name, {
            "verb": "rotate", "src": str(src), "out": str(target),
            "pages": pages, "angle": by, "pages_rotated": len(targets),
            "summary": f"rotated {len(targets)} page(s) by {by}°",
        })
    if as_json:
        emit_json({"out": str(target), "pages_rotated": len(targets), "angle": by})
    elif not quiet:
        click.echo(f"rotated {len(targets)} pages by {by}° → {target}")
