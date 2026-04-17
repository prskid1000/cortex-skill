"""claw pptx new — create a blank .pptx."""

from __future__ import annotations

import shutil
from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


ASPECT_ALIASES = {
    "16:9": "16:9",
    "widescreen": "16:9",
    "4:3": "4:3",
    "standard": "4:3",
}


@click.command(name="new")
@click.argument("out", type=click.Path(path_type=Path))
@click.option("--template", default=None,
              type=click.Path(exists=True, path_type=Path))
@click.option("--aspect",
              type=click.Choice(["16:9", "4:3", "widescreen", "standard"]),
              default="16:9",
              show_default=True,
              help="Slide aspect ratio. widescreen=16:9, standard=4:3.")
@common_output_options
def new(out: Path, template: Path | None, aspect: str,
        force: bool, backup: bool, as_json: bool, dry_run: bool,
        quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Create a blank .pptx (optionally from a template)."""
    try:
        from pptx import Presentation
        from pptx.util import Inches
    except ImportError:
        die("python-pptx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[pptx]'", as_json=as_json)

    aspect_norm = ASPECT_ALIASES[aspect]

    if dry_run:
        click.echo(f"would write {out} ({aspect_norm})"
                   + (f" from {template}" if template else ""))
        return

    if template:
        import tempfile
        tmp = Path(tempfile.mkstemp(suffix=".pptx")[1])
        shutil.copy2(template, tmp)
        prs = Presentation(str(tmp))
        sldIdLst = prs.slides._sldIdLst
        for sldId in list(sldIdLst):
            rId = sldId.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            prs.part.drop_rel(rId)
            sldIdLst.remove(sldId)
        tmp.unlink(missing_ok=True)
    else:
        prs = Presentation()

    if not template:
        if aspect_norm == "16:9":
            prs.slide_width = Inches(13.333)
            prs.slide_height = Inches(7.5)
        else:
            prs.slide_width = Inches(10)
            prs.slide_height = Inches(7.5)

    def _save(f):
        prs.save(f)

    safe_write(out, _save, force=force, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(out), "aspect": aspect_norm,
                   "template": str(template) if template else None})
    elif not quiet:
        click.echo(f"wrote {out}")
