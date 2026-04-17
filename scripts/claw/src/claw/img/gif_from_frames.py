"""claw img gif-from-frames — animated GIF from a directory of frames."""

from __future__ import annotations

import io
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, EXIT_USAGE, common_output_options, die, emit_json, safe_write,
)


DEFAULT_PATTERNS = ("*.png", "*.jpg", "*.jpeg", "*.webp")


@click.command(name="gif-from-frames")
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--out", "dst", default=None, type=click.Path(path_type=Path),
              help="Output path (default: <dir>.gif).")
@click.option("--fps", type=float, required=True, help="Frames per second.")
@click.option("--loop", type=int, default=0,
              help="Loop count (0 = forever, 1 = play once).")
@click.option("--optimize", is_flag=True, help="Run GIF palette optimizer.")
@click.option("--pattern", default=None,
              help="Glob pattern (default: *.png|jpg|jpeg|webp).")
@common_output_options
def gif_from_frames(directory: Path, dst: Path | None, fps: float, loop: int, optimize: bool,
                    pattern: str | None,
                    force: bool, backup: bool, as_json: bool, dry_run: bool,
                    quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Build an animated GIF from sorted frames in <dir>."""
    try:
        from PIL import Image
    except ImportError:
        die("Pillow not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[img]'", as_json=as_json)

    if fps <= 0:
        die(f"--fps must be positive, got {fps}", code=EXIT_USAGE, as_json=as_json)

    patterns = [pattern] if pattern else list(DEFAULT_PATTERNS)
    frames_paths: list[Path] = []
    for pat in patterns:
        frames_paths.extend(directory.glob(pat))
    frames_paths = [f for f in sorted(set(frames_paths)) if f.is_file()]

    if not frames_paths:
        die(f"no frames matched in {directory}", code=EXIT_INPUT, as_json=as_json)

    if dst is None:
        dst = directory.with_suffix(".gif")

    duration_ms = int(round(1000.0 / fps))

    if dry_run:
        click.echo(f"would build {dst} from {len(frames_paths)} frames "
                   f"(fps={fps} duration={duration_ms}ms loop={loop} optimize={optimize})")
        return

    first = Image.open(frames_paths[0]).convert("RGBA")
    rest = [Image.open(p).convert("RGBA") for p in frames_paths[1:]]

    buf = io.BytesIO()
    first.save(
        buf,
        format="GIF",
        save_all=True,
        append_images=rest,
        duration=duration_ms,
        loop=loop,
        optimize=optimize,
        disposal=2,
    )

    safe_write(dst, lambda f: f.write(buf.getvalue()),
               force=force, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"dst": str(dst), "frames": len(frames_paths),
                   "fps": fps, "duration_ms": duration_ms, "loop": loop,
                   "optimize": optimize})
    elif not quiet:
        click.echo(f"wrote {dst} ({len(frames_paths)} frames @ {fps} fps)")
