"""claw img exif — read / strip / auto-rotate EXIF, as flags on one verb.

Previously a click group with an `invoke_without_command=True` + positional SRC;
Click greedily parsed the subcommand NAME (`strip`, `auto-rotate`) as SRC, leaving
the subcommands unreachable. Flag-based mode solves it cleanly.
"""

from __future__ import annotations

import io
from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


@click.command(name="exif")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--out", "dst", default=None, type=click.Path(path_type=Path),
              help="Output path (required with --strip or --auto-rotate).")
@click.option("--strip", "do_strip", is_flag=True, help="Remove EXIF; preserves ICC unless --strip-icc.")
@click.option("--strip-icc", is_flag=True, help="Also remove the ICC colour profile.")
@click.option("--auto-rotate", "do_rotate", is_flag=True,
              help="Bake EXIF orientation into pixels; result has Orientation=1.")
@common_output_options
def exif(src: Path, dst: Path | None, do_strip: bool, strip_icc: bool, do_rotate: bool,
         force: bool, backup: bool, as_json: bool, dry_run: bool,
         quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Read (default), strip, or auto-rotate EXIF metadata on an image."""
    try:
        from PIL import Image, ExifTags, ImageOps
    except ImportError:
        die("Pillow not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[img]'", as_json=as_json)
        return  # unreachable — die exits, helps type-checker

    img = Image.open(src)

    if do_strip or do_rotate:
        if dst is None:
            die("--out is required with --strip or --auto-rotate", code=EXIT_INPUT, as_json=as_json)
            return
        if do_rotate:
            img = ImageOps.exif_transpose(img)
        if do_strip:
            data = list(img.getdata())
            clean = Image.new(img.mode, img.size)
            clean.putdata(data)
            img = clean
        if dry_run:
            click.echo(f"would write {dst}")
            return
        kwargs: dict = {}
        if do_strip and not strip_icc and "icc_profile" in img.info:
            kwargs["icc_profile"] = img.info["icc_profile"]
        buf = io.BytesIO()
        img.save(buf, format=img.format or "PNG", **kwargs)
        safe_write(dst, lambda f: f.write(buf.getvalue()),
                   force=force, backup=backup, mkdir=mkdir)
        if as_json:
            emit_json({"src": str(src), "out": str(dst),
                       "stripped": do_strip, "rotated": do_rotate})
        elif not quiet:
            click.echo(f"wrote {dst}")
        return

    # Read-only mode (default)
    exif_data = img.getexif()
    out: dict = {}
    for tag_id, value in exif_data.items():
        tag = ExifTags.TAGS.get(tag_id, str(tag_id))
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8", errors="replace")
            except Exception:
                value = repr(value)
        if "DateTime" in tag and isinstance(value, str):
            out[f"{tag}_utc"] = value.replace(":", "-", 2).replace(" ", "T") + "Z"
        out[tag] = value

    if as_json:
        emit_json({"src": str(src), "exif": out})
    else:
        for k, v in out.items():
            click.echo(f"{k}: {v}")
