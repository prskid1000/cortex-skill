"""claw img overlay — scaled corner logo composited on a background."""

from __future__ import annotations

import io
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, EXIT_USAGE, common_output_options, die, emit_json, safe_write,
)


def _corner_pos(position: str, base: tuple[int, int], overlay: tuple[int, int],
                padding: int) -> tuple[int, int]:
    bw, bh = base
    ow, oh = overlay
    p = position.upper()
    if p == "TL":    return (padding, padding)
    if p == "TR":    return (bw - ow - padding, padding)
    if p == "BL":    return (padding, bh - oh - padding)
    if p == "BR":    return (bw - ow - padding, bh - oh - padding)
    if p in ("C", "CENTER", "CC"):
        return ((bw - ow) // 2, (bh - oh) // 2)
    raise click.UsageError(f"bad --position {position!r} (use TL|TR|BL|BR|center)")


@click.command(name="overlay")
@click.argument("bg", type=click.Path(exists=True, path_type=Path))
@click.option("--logo", required=True, type=click.Path(exists=True, path_type=Path),
              help="Logo image (alpha preserved).")
@click.option("--out", "dst", required=True, type=click.Path(path_type=Path))
@click.option("--scale", type=float, default=0.2,
              help="Logo width as fraction of base's shortest edge.")
@click.option("--position", default="BR",
              help="TL|TR|BL|BR|center (default BR).")
@click.option("--padding", type=int, default=20,
              help="Pixels from the corner (ignored for center).")
@click.option("--margin", "margin", type=int, default=None,
              help="Inset in pixels from the overlay corner (alias for --padding; default 10).")
@common_output_options
def overlay(bg: Path, logo: Path, dst: Path, scale: float, position: str, padding: int,
            margin: int | None,
            force: bool, backup: bool, as_json: bool, dry_run: bool,
            quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Composite a scaled logo onto <bg> at a named corner."""
    try:
        from PIL import Image
    except ImportError:
        die("Pillow not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[img]'", as_json=as_json)

    if margin is not None:
        padding = margin

    if scale <= 0 or scale > 1:
        die(f"--scale must be in (0, 1], got {scale}", code=EXIT_USAGE, as_json=as_json)

    base = Image.open(bg).convert("RGBA")
    lg = Image.open(logo).convert("RGBA")

    target_w = max(1, int(min(base.width, base.height) * scale))
    target_h = max(1, int(lg.height * (target_w / lg.width)))
    lg_scaled = lg.resize((target_w, target_h), Image.LANCZOS)

    pos = _corner_pos(position, base.size, lg_scaled.size, padding)

    if dry_run:
        click.echo(f"would overlay {logo} on {bg} scale={scale} pos={position} at={pos} -> {dst}")
        return

    canvas = base.copy()
    canvas.alpha_composite(lg_scaled, pos)

    suffix = dst.suffix.lower()
    out_fmt = suffix.lstrip(".").upper() or "PNG"
    if out_fmt == "JPG":
        out_fmt = "JPEG"
    final = canvas.convert("RGB") if out_fmt == "JPEG" else canvas

    buf = io.BytesIO()
    final.save(buf, format=out_fmt)
    safe_write(dst, lambda f: f.write(buf.getvalue()),
               force=force, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"bg": str(bg), "logo": str(logo), "dst": str(dst),
                   "position": position, "at": list(pos),
                   "logo_size": list(lg_scaled.size)})
    elif not quiet:
        click.echo(f"wrote {dst} (logo {lg_scaled.width}x{lg_scaled.height} at {position})")
