"""claw pdf layer-toggle — show / hide an OCG (optional content group)."""
from __future__ import annotations

from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, safe_write


@click.command(name="layer-toggle")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--name", required=True, help="Layer (OCG) name.")
@click.option("--show/--hide", "show", default=False,
              help="Set layer visibility (default: --hide).")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True)
@common_output_options
def layer_toggle(src: Path, name: str, show: bool,
                 out: Path | None, in_place: bool,
                 force: bool, backup: bool, as_json: bool, dry_run: bool,
                 quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Show or hide an OCG layer by name."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    if not (out or in_place):
        die("pass --out FILE or --in-place", code=2)
    target = src if in_place else out
    assert target is not None

    doc = fitz.open(str(src))
    try:
        configs = doc.layer_ui_configs() or []
        match = None
        for cfg in configs:
            if cfg.get("text") == name or cfg.get("name") == name:
                match = cfg
                break
        if match is None:
            die(f"layer not found: {name!r}", code=2)

        number = match.get("number")
        if number is None:
            die(f"layer has no config number: {name!r}", code=1)

        try:
            doc.set_layer_ui_config(number, action=0 if show else 1)
        except Exception as e:
            die(f"failed to toggle layer: {e}", code=1)

        if dry_run:
            verb = "show" if show else "hide"
            click.echo(f"would {verb} layer {name!r} → {target}")
            return
        data = doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()

    safe_write(target, lambda f: f.write(data),
               force=force or in_place, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(target), "layer": name, "visible": show})
    elif not quiet:
        verb = "shown" if show else "hidden"
        click.echo(f"layer {name!r} {verb} → {target}")
