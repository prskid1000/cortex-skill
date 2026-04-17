"""claw media loudnorm — EBU R128 two-pass loudness normalization."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

import click

from claw.common import (
    EXIT_SYSTEM, common_output_options, die, emit_json, require, run, safe_copy,
)


def _parse_pass1(stderr: str) -> dict:
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", stderr, re.DOTALL)
    if not m:
        raise RuntimeError("could not parse loudnorm pass-1 JSON from stderr")
    return json.loads(m.group(0))


@click.command(name="loudnorm")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--out", "dst", required=True, type=click.Path(path_type=Path))
@click.option("--I", "target_i", type=float, default=-16.0, help="Integrated LUFS.")
@click.option("--TP", "target_tp", type=float, default=-1.5, help="True peak dBTP.")
@click.option("--LRA", "target_lra", type=float, default=11.0, help="Loudness range.")
@common_output_options
def loudnorm(src: Path, dst: Path, target_i: float, target_tp: float, target_lra: float,
             force: bool, backup: bool, as_json: bool, dry_run: bool,
             quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Two-pass EBU R128 loudness normalization."""
    try:
        require("ffmpeg")
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, hint="winget install Gyan.FFmpeg", as_json=as_json)

    af1 = (f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}"
           f":print_format=json")

    null_sink = "NUL" if os.name == "nt" else "/dev/null"
    pass1 = ["-y", "-i", str(src), "-af", af1, "-f", "null", null_sink]

    try:
        r1 = run("ffmpeg", *pass1, check=True)
    except Exception as e:
        die(f"loudnorm pass-1 failed: {e}", code=EXIT_SYSTEM, as_json=as_json)

    try:
        measured = _parse_pass1(r1.stderr)
    except Exception as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    if dry_run:
        if as_json:
            emit_json({"src": str(src), "dst": str(dst),
                       "I": target_i, "TP": target_tp, "LRA": target_lra,
                       "measured": measured, "dry_run": True})
        else:
            click.echo(json.dumps(measured, indent=2))
            click.echo(f"(pass-2 skipped: --dry-run; would write {dst})")
        return

    af2 = (f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}"
           f":measured_I={measured['input_i']}"
           f":measured_TP={measured['input_tp']}"
           f":measured_LRA={measured['input_lra']}"
           f":measured_thresh={measured['input_thresh']}"
           f":offset={measured['target_offset']}"
           f":linear=true:print_format=summary")

    with tempfile.TemporaryDirectory(prefix="claw-") as td:
        tmp = Path(td) / dst.name
        args = ["-y", "-i", str(src), "-af", af2, "-c:v", "copy", str(tmp)]
        try:
            run("ffmpeg", *args)
        except Exception as e:
            die(f"loudnorm pass-2 failed: {e}", code=EXIT_SYSTEM, as_json=as_json)
        safe_copy(tmp, dst, force=force, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"src": str(src), "dst": str(dst),
                   "I": target_i, "TP": target_tp, "LRA": target_lra,
                   "measured": measured})
    elif not quiet:
        click.echo(f"wrote {dst} (I={target_i} LUFS)")
