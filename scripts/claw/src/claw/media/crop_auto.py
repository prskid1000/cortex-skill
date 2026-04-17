"""claw media crop-auto — detect and remove letterbox/pillarbox bars."""

from __future__ import annotations

import os
import re
import tempfile
from collections import Counter
from pathlib import Path

import click

from claw.common import (
    EXIT_SYSTEM, common_output_options, die, emit_json, require, run, safe_copy,
)


_CROP_RE = re.compile(r"crop=(\d+):(\d+):(\d+):(\d+)")


def _most_common_crop(stderr: str) -> str | None:
    matches = _CROP_RE.findall(stderr)
    if not matches:
        return None
    counter = Counter(matches)
    (w, h, x, y), _ = counter.most_common(1)[0]
    return f"crop={w}:{h}:{x}:{y}"


@click.command(name="crop-auto")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--out", "dst", default=None, type=click.Path(path_type=Path),
              help="Output path (default: <src>-cropped<ext>).")
@click.option("--sample-duration", type=float, default=60.0,
              help="Seconds to sample for cropdetect (default 60).")
@click.option("--probe-duration", "probe_duration", type=float, default=None,
              help="Seconds to analyze with cropdetect (alias for --sample-duration; default 10.0).")
@click.option("--limit", type=int, default=24,
              help="cropdetect black threshold 0-255 (default 24).")
@common_output_options
def crop_auto(src: Path, dst: Path | None, sample_duration: float,
              probe_duration: float | None, limit: int,
              force: bool, backup: bool, as_json: bool, dry_run: bool,
              quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Detect and apply crop to remove letterbox/pillarbox bars."""
    try:
        require("ffmpeg")
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, hint="winget install Gyan.FFmpeg", as_json=as_json)

    if probe_duration is not None:
        sample_duration = probe_duration

    if dst is None:
        dst = src.with_name(f"{src.stem}-cropped{src.suffix}")

    null_sink = "NUL" if os.name == "nt" else "/dev/null"
    detect_args = [
        "-hide_banner", "-nostats",
        "-ss", "0", "-i", str(src),
        "-t", str(sample_duration),
        "-vf", f"cropdetect={limit}:2:0",
        "-an", "-sn", "-f", "null", null_sink,
    ]

    if dry_run:
        click.echo("ffmpeg " + " ".join(detect_args))
        click.echo("ffmpeg <pass 2 with detected crop> -> " + str(dst))
        return

    with tempfile.TemporaryDirectory(prefix="claw-") as td:
        try:
            r1 = run("ffmpeg", *detect_args, check=False,
                     cwd=td)
        except Exception as e:
            die(f"cropdetect failed: {e}", code=EXIT_SYSTEM, as_json=as_json)

        crop_expr = _most_common_crop(r1.stderr or "")
        if not crop_expr:
            die("cropdetect produced no crop lines (video may be too short or all-black)",
                code=EXIT_SYSTEM, as_json=as_json)

        tmp = Path(td) / dst.name
        apply_args = [
            "-y", "-i", str(src),
            "-vf", crop_expr,
            "-c:a", "copy",
            str(tmp),
        ]
        try:
            run("ffmpeg", *apply_args)
        except Exception as e:
            die(f"crop apply failed: {e}", code=EXIT_SYSTEM, as_json=as_json)
        safe_copy(tmp, dst, force=force, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"src": str(src), "dst": str(dst),
                   "crop": crop_expr, "sample_duration": sample_duration, "limit": limit})
    elif not quiet:
        click.echo(f"wrote {dst} ({crop_expr})")
