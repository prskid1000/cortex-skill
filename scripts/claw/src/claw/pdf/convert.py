"""claw pdf convert — EPUB / XPS / CBZ / txt → PDF via PyMuPDF."""
from __future__ import annotations

from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, safe_write


SUPPORTED = {".epub", ".xps", ".oxps", ".cbz", ".cbr", ".fb2", ".txt", ".mobi", ".svg"}


@click.command(name="convert")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("out", type=click.Path(path_type=Path))
@click.option("--page-size", default=None, help="Override page size (e.g. A4).")
@common_output_options
def convert(src: Path, out: Path, page_size: str | None,
            force: bool, backup: bool, as_json: bool, dry_run: bool,
            quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Convert <SRC> (EPUB/XPS/CBZ/...) to PDF at <OUT>."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    suffix = src.suffix.lower()
    if suffix not in SUPPORTED:
        die(f"unsupported input type: {suffix}", code=2,
            hint=f"supported: {', '.join(sorted(SUPPORTED))}")

    doc = fitz.open(str(src))
    try:
        try:
            pdf_bytes = doc.convert_to_pdf()
        except Exception as e:
            die(f"convert_to_pdf failed: {e}", code=1)
    finally:
        doc.close()

    if dry_run:
        click.echo(f"would convert {src} → {out} ({len(pdf_bytes)} bytes)")
        return

    safe_write(out, lambda f: f.write(pdf_bytes),
               force=force, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(out), "src": str(src), "bytes": len(pdf_bytes)})
    elif not quiet:
        click.echo(f"converted {src} → {out} ({len(pdf_bytes)} bytes)")
