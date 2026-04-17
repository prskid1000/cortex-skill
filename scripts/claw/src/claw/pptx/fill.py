"""claw pptx fill — set the text of an existing placeholder or named shape."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


@click.command(name="fill")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.argument("text")
@click.option("--slide", required=True, type=int, help="1-based slide index.")
@click.option("--placeholder", "placeholder_idx", default=None, type=int,
              help="Placeholder idx on the layout (see `meta get --layouts`).")
@click.option("--shape-name", "shape_name", default=None,
              help="Exact name of a shape on the slide.")
@common_output_options
def fill(src: Path, text: str, slide: int, placeholder_idx: int | None,
         shape_name: str | None,
         force: bool, backup: bool, as_json: bool, dry_run: bool,
         quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Write `text` into a placeholder (by idx) or a named shape."""
    try:
        from pptx import Presentation
    except ImportError:
        die("python-pptx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[pptx]'", as_json=as_json)

    if (placeholder_idx is None) == (shape_name is None):
        die("specify exactly one of --placeholder or --shape-name",
            code=EXIT_INPUT, as_json=as_json)

    if dry_run:
        click.echo(f"would fill slide {slide} placeholder={placeholder_idx} "
                   f"shape={shape_name}")
        return

    prs = Presentation(str(src))
    if slide < 1 or slide > len(prs.slides):
        die(f"slide {slide} out of range", code=EXIT_INPUT, as_json=as_json)
    target = prs.slides[slide - 1]

    shape = None
    if placeholder_idx is not None:
        for ph in target.placeholders:
            if ph.placeholder_format.idx == placeholder_idx:
                shape = ph
                break
        if shape is None:
            die(f"placeholder idx {placeholder_idx} not found on slide {slide}",
                code=EXIT_INPUT, as_json=as_json)
    else:
        for s in target.shapes:
            if s.name == shape_name:
                shape = s
                break
        if shape is None:
            die(f"shape {shape_name!r} not found on slide {slide}",
                code=EXIT_INPUT, as_json=as_json)

    if not shape.has_text_frame:
        die("target shape has no text frame", code=EXIT_INPUT, as_json=as_json)
    shape.text_frame.text = text

    def _save(f):
        prs.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "slide": slide,
                   "placeholder": placeholder_idx, "shape_name": shape_name,
                   "length": len(text)})
    elif not quiet:
        target_desc = (f"placeholder {placeholder_idx}"
                       if placeholder_idx is not None else f"shape {shape_name!r}")
        click.echo(f"filled {target_desc} on slide {slide}")
