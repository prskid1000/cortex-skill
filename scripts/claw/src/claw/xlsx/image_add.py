"""claw xlsx image add — embed a PNG / JPEG anchored to a cell."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


@click.group(name="image")
def image() -> None:
    """Image operations on a workbook."""


@image.command(name="add")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--sheet", required=True)
@click.option("--at", "at_cell", required=True, help="Anchor cell, e.g. B2.")
@click.option("--image", "image_path", required=True,
              type=click.Path(exists=True, path_type=Path))
@click.option("--width", "width_px", default=None, type=int,
              help="Resize to this width in pixels (preserves aspect if --keep-aspect).")
@click.option("--height", "height_px", default=None, type=int)
@click.option("--keep-aspect", "keep_aspect", is_flag=True)
@common_output_options
def image_add(src: Path, sheet: str, at_cell: str, image_path: Path,
              width_px: int | None, height_px: int | None, keep_aspect: bool,
              force: bool, backup: bool, as_json: bool, dry_run: bool,
              quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Embed an image and anchor it at --at."""
    try:
        from openpyxl import load_workbook
        from openpyxl.drawing.image import Image
    except ImportError:
        die("openpyxl not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[xlsx]'", as_json=as_json)

    if dry_run:
        click.echo(f"would add {image_path} at {sheet}!{at_cell}")
        return

    wb = load_workbook(src)
    ws = wb[sheet]

    img = Image(str(image_path))
    if width_px or height_px:
        orig_w = img.width
        orig_h = img.height
        if keep_aspect:
            if width_px and not height_px:
                img.width = width_px
                img.height = int(orig_h * width_px / orig_w)
            elif height_px and not width_px:
                img.height = height_px
                img.width = int(orig_w * height_px / orig_h)
            else:
                scale = min(width_px / orig_w, height_px / orig_h)
                img.width = int(orig_w * scale)
                img.height = int(orig_h * scale)
        else:
            if width_px:
                img.width = width_px
            if height_px:
                img.height = height_px

    img.anchor = at_cell
    ws.add_image(img)

    def _save(f):
        wb.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "sheet": sheet, "at": at_cell,
                   "image": str(image_path)})
    elif not quiet:
        click.echo(f"added image to {sheet}!{at_cell}")
