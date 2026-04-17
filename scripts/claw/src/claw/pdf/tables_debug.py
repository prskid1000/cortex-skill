"""claw pdf tables-debug — overlay pdfplumber's table detection onto a rendered page."""
from __future__ import annotations

import io
from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, safe_write


STRATEGIES = ("lines", "lines_strict", "text", "explicit")


def _parse_floats(spec: str | None) -> list[float] | None:
    if not spec:
        return None
    return [float(x) for x in spec.split(",") if x.strip()]


@click.command(name="tables-debug")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--page", "page_num", type=int, required=True, help="1-indexed page.")
@click.option("-o", "--out", required=True, type=click.Path(path_type=Path),
              help="PNG output path.")
@click.option("--strategy", type=click.Choice(STRATEGIES), default="lines")
@click.option("--vlines", help="Explicit vertical split x-coords, comma-separated.")
@click.option("--hlines", help="Explicit horizontal split y-coords, comma-separated.")
@click.option("--snap-tol", type=float, default=3.0)
@click.option("--resolution", type=int, default=150,
              help="DPI for the rendered debug overlay.")
@common_output_options
def tables_debug(src: Path, page_num: int, out: Path, strategy: str,
                 vlines: str | None, hlines: str | None,
                 snap_tol: float, resolution: int,
                 force: bool, backup: bool, as_json: bool, dry_run: bool,
                 quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Render page with pdfplumber's table-detection edges drawn."""
    try:
        import pdfplumber
    except ImportError:
        die("pdfplumber not installed; install: pip install 'claw[pdf]'")

    settings: dict = {
        "vertical_strategy": strategy,
        "horizontal_strategy": strategy,
        "snap_tolerance": snap_tol,
    }
    ev = _parse_floats(vlines)
    eh = _parse_floats(hlines)
    if strategy == "explicit":
        if not ev or not eh:
            die("--strategy explicit requires both --vlines and --hlines", code=2)
        settings["explicit_vertical_lines"] = ev
        settings["explicit_horizontal_lines"] = eh

    buf = io.BytesIO()
    with pdfplumber.open(str(src)) as pdf:
        if not 1 <= page_num <= len(pdf.pages):
            die(f"--page {page_num} out of range (1..{len(pdf.pages)})")
        page = pdf.pages[page_num - 1]
        im = page.to_image(resolution=resolution)
        im.debug_tablefinder(table_settings=settings)
        im.save(buf, format="PNG")
    data = buf.getvalue()

    if dry_run:
        click.echo(f"would write debug image → {out} ({len(data)} bytes)")
        return

    safe_write(out, lambda f: f.write(data), force=force, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(out), "page": page_num, "strategy": strategy,
                   "bytes": len(data)})
    elif not quiet:
        click.echo(f"wrote {out} ({len(data)} bytes)")
