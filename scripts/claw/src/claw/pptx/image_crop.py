"""claw pptx image-crop — fractional crop on a picture shape."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


@click.command(name="image-crop")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--slide", required=True, type=int,
              help="1-based slide number.")
@click.option("--shape", "shape_idx", default=None, type=int,
              help="0-based index into slide.shapes (picture shapes only).")
@click.option("--shape-name", "shape_name", default=None,
              help="Match by shape.name instead of index.")
@click.option("--left", default=0.0, type=float, show_default=True,
              help="Fractional crop 0.0-1.0.")
@click.option("--right", default=0.0, type=float, show_default=True)
@click.option("--top", default=0.0, type=float, show_default=True)
@click.option("--bottom", default=0.0, type=float, show_default=True)
@common_output_options
def image_crop(src: Path, slide: int, shape_idx: int | None, shape_name: str | None,
               left: float, right: float, top: float, bottom: float,
               force: bool, backup: bool, as_json: bool, dry_run: bool,
               quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Crop a picture shape by fractional left/right/top/bottom (0.0 to 1.0)."""
    try:
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except ImportError:
        die("python-pptx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[pptx]'", as_json=as_json)

    if shape_idx is None and not shape_name:
        die("pass --shape IDX or --shape-name NAME", code=EXIT_INPUT, as_json=as_json)

    for name, val in (("left", left), ("right", right), ("top", top), ("bottom", bottom)):
        if val < 0.0 or val >= 1.0:
            die(f"--{name} must be in [0.0, 1.0), got {val}",
                code=EXIT_INPUT, as_json=as_json)
    if left + right >= 1.0 or top + bottom >= 1.0:
        die("opposing crops sum to >= 1.0", code=EXIT_INPUT, as_json=as_json)

    prs = Presentation(str(src))
    if slide < 1 or slide > len(prs.slides):
        die(f"slide {slide} out of range (1..{len(prs.slides)})",
            code=EXIT_INPUT, as_json=as_json)
    target = prs.slides[slide - 1]

    picture = None
    if shape_idx is not None:
        if shape_idx < 0 or shape_idx >= len(target.shapes):
            die(f"shape {shape_idx} out of range (0..{len(target.shapes) - 1})",
                code=EXIT_INPUT, as_json=as_json)
        picture = target.shapes[shape_idx]
    else:
        for shp in target.shapes:
            if shp.name == shape_name:
                picture = shp
                break
        if picture is None:
            die(f"no shape named {shape_name!r} on slide {slide}",
                code=EXIT_INPUT, as_json=as_json)

    if picture.shape_type != MSO_SHAPE_TYPE.PICTURE:
        die(f"shape is not a picture (type={picture.shape_type})",
            code=EXIT_INPUT, as_json=as_json)

    if dry_run:
        click.echo(f"would crop slide {slide} shape {picture.name} "
                   f"L={left} R={right} T={top} B={bottom}")
        return

    picture.crop_left = left
    picture.crop_right = right
    picture.crop_top = top
    picture.crop_bottom = bottom

    def _save(f):
        prs.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "slide": slide, "shape": picture.name,
                   "left": left, "right": right, "top": top, "bottom": bottom})
    elif not quiet:
        click.echo(f"cropped {picture.name} on slide {slide}")
