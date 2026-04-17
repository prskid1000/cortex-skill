"""claw pdf crop — crop pages to a rectangle."""
from __future__ import annotations

from pathlib import Path

import click

from claw.common import PageSelector, common_output_options, die, emit_json, safe_write


BOX_TYPES = ("media", "crop", "trim", "bleed", "art")


@click.command(name="crop")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--pages", default=None, help="Page range.")
@click.option("--page", "page", default=None,
              help="Page spec (same syntax as --pages; sets the page selection).")
@click.option("--box", "box_spec", required=True,
              help="Crop rectangle x0,y0,x1,y1 in PDF points.")
@click.option("--box-type", type=click.Choice(BOX_TYPES), default="crop",
              help="Which page box to modify.")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True)
@common_output_options
def crop(src: Path, pages: str | None, page: str | None, box_spec: str, box_type: str,
         out: Path | None, in_place: bool,
         force: bool, backup: bool, as_json: bool, dry_run: bool,
         quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Crop pages of <SRC> to --box x0,y0,x1,y1."""
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import RectangleObject
    except ImportError:
        die("pypdf not installed; install: pip install 'claw[pdf]'")

    if not (out or in_place):
        die("pass --out FILE or --in-place", code=2)
    target = src if in_place else Path(out) if out else None
    assert target is not None

    coords = [float(x) for x in box_spec.split(",")]
    if len(coords) != 4:
        die("--box must be x0,y0,x1,y1", code=2)

    page_spec = page or pages or "all"

    reader = PdfReader(str(src))
    total = len(reader.pages)
    targets = set(PageSelector(page_spec).resolve(total))

    writer = PdfWriter()
    for i, page in enumerate(reader.pages, start=1):
        if i in targets:
            rect = RectangleObject(coords)
            attr = f"{box_type}box"
            try:
                setattr(page, attr, rect)
            except AttributeError:
                page.cropbox = rect
        writer.add_page(page)

    if dry_run:
        click.echo(f"would crop {len(targets)} of {total} pages to {coords} → {target}")
        return

    safe_write(target, lambda f: writer.write(f),
               force=force or in_place, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(target), "pages_cropped": len(targets),
                   "box": coords, "box_type": box_type})
    elif not quiet:
        click.echo(f"cropped {len(targets)} pages → {target}")
