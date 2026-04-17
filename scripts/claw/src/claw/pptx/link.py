"""claw pptx link — add hyperlink to a shape or placeholder."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


@click.group(name="link")
def link() -> None:
    """Manage hyperlinks on slide shapes."""


@link.command(name="add")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--slide", required=True, type=int, help="1-based slide number.")
@click.option("--shape", "shape_idx", default=None, type=int,
              help="0-based index into slide.shapes.")
@click.option("--shape-name", "shape_name", default=None,
              help="Match by shape.name instead of --shape.")
@click.option("--placeholder", "placeholder_idx", default=None, type=int,
              help="Placeholder idx (layout placeholder index).")
@click.option("--url", required=True, help="Hyperlink target URL.")
@click.option("--text", "new_text", default=None,
              help="Replace the first run's text with this string.")
@common_output_options
def add(src: Path, slide: int, shape_idx: int | None, shape_name: str | None,
        placeholder_idx: int | None, url: str, new_text: str | None,
        force: bool, backup: bool, as_json: bool, dry_run: bool,
        quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Attach a hyperlink to a shape's first text run (or replace the run's text)."""
    try:
        from pptx import Presentation
    except ImportError:
        die("python-pptx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[pptx]'", as_json=as_json)

    if sum(x is not None for x in (shape_idx, shape_name, placeholder_idx)) != 1:
        die("pass exactly one of --shape / --shape-name / --placeholder",
            code=EXIT_INPUT, as_json=as_json)

    prs = Presentation(str(src))
    if slide < 1 or slide > len(prs.slides):
        die(f"slide {slide} out of range (1..{len(prs.slides)})",
            code=EXIT_INPUT, as_json=as_json)
    target = prs.slides[slide - 1]

    shape = None
    if shape_idx is not None:
        if shape_idx < 0 or shape_idx >= len(target.shapes):
            die(f"shape {shape_idx} out of range (0..{len(target.shapes) - 1})",
                code=EXIT_INPUT, as_json=as_json)
        shape = target.shapes[shape_idx]
    elif shape_name is not None:
        for shp in target.shapes:
            if shp.name == shape_name:
                shape = shp
                break
        if shape is None:
            die(f"no shape named {shape_name!r} on slide {slide}",
                code=EXIT_INPUT, as_json=as_json)
    else:
        for ph in target.placeholders:
            if ph.placeholder_format.idx == placeholder_idx:
                shape = ph
                break
        if shape is None:
            die(f"no placeholder idx={placeholder_idx} on slide {slide}",
                code=EXIT_INPUT, as_json=as_json)

    if not shape.has_text_frame:
        die(f"shape {shape.name!r} has no text frame", code=EXIT_INPUT, as_json=as_json)

    if dry_run:
        click.echo(f"would add link on slide {slide} shape {shape.name} -> {url}")
        return

    tf = shape.text_frame
    if not tf.paragraphs:
        para = tf.paragraphs[0] if tf.paragraphs else tf.add_paragraph()
    else:
        para = tf.paragraphs[0]

    run = None
    if para.runs:
        run = para.runs[0]
    if run is None:
        run = para.add_run()
        run.text = new_text or url

    if new_text is not None:
        run.text = new_text
    elif not run.text:
        run.text = url

    run.hyperlink.address = url

    def _save(f):
        prs.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "slide": slide, "shape": shape.name,
                   "url": url, "text": run.text})
    elif not quiet:
        click.echo(f"linked {shape.name} on slide {slide} -> {url}")
