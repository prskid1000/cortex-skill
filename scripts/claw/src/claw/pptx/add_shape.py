"""claw pptx add-shape — draw a shape on a slide and optionally fill it with text."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


SHAPE_MAP = {
    "rect":         "RECTANGLE",
    "rectangle":    "RECTANGLE",
    "rounded-rect": "ROUNDED_RECTANGLE",
    "oval":         "OVAL",
    "ellipse":      "OVAL",
    "triangle":     "ISOCELES_TRIANGLE",
    "arrow":        "RIGHT_ARROW",
    "callout":      "RECTANGULAR_CALLOUT",
    "line":         "LINE_CALLOUT_1",
}


@click.command(name="add-shape")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--slide", required=True, type=int, help="1-based slide index.")
@click.option("--kind", "shape_kind", default=None,
              type=click.Choice(list(SHAPE_MAP.keys())),
              help="Shape kind (alias: --type).")
@click.option("--type", "shape_type_alias", default=None,
              type=click.Choice(list(SHAPE_MAP.keys())),
              help="Alias for --kind.")
@click.option("--at", "at_pos", default=None, help="x,y position (e.g. 1in,2in).")
@click.option("-x", "x_pos", default=None)
@click.option("-y", "y_pos", default=None)
@click.option("--size", default=None, help="w,h (e.g. 2in,1in).")
@click.option("-w", "w_val", default=None)
@click.option("-h", "h_val", default=None)
@click.option("--text", default=None)
@click.option("--fill", default=None, help="#RRGGBB fill.")
@click.option("--line", "line_color", default=None, help="#RRGGBB outline.")
@click.option("--text-color", "text_color", default=None)
@common_output_options
def add_shape(src: Path, slide: int, shape_kind: str | None,
              shape_type_alias: str | None, at_pos: str | None,
              x_pos: str | None, y_pos: str | None, size: str | None,
              w_val: str | None, h_val: str | None, text: str | None,
              fill: str | None, line_color: str | None, text_color: str | None,
              force: bool, backup: bool, as_json: bool, dry_run: bool,
              quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Draw a rectangle / oval / triangle / arrow / callout / line on a slide."""
    try:
        from pptx import Presentation
        from pptx.dml.color import RGBColor
        from pptx.enum.shapes import MSO_SHAPE
        from pptx.util import Cm, Emu, Inches, Pt
    except ImportError:
        die("python-pptx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[pptx]'", as_json=as_json)

    kind = shape_kind or shape_type_alias
    if not kind:
        die("pass --kind (or --type)", code=EXIT_INPUT, as_json=as_json)

    x_raw = x_pos
    y_raw = y_pos
    if at_pos:
        parts = at_pos.split(",")
        if len(parts) != 2:
            die(f"invalid --at: {at_pos!r}", code=EXIT_INPUT, as_json=as_json)
        x_raw, y_raw = parts

    w_raw = w_val
    h_raw = h_val
    if size:
        parts = size.split(",")
        if len(parts) != 2:
            die(f"invalid --size: {size!r}", code=EXIT_INPUT, as_json=as_json)
        w_raw, h_raw = parts

    if None in (x_raw, y_raw, w_raw, h_raw):
        die("need --at and --size (or -x/-y/-w/-h)",
            code=EXIT_INPUT, as_json=as_json)

    if dry_run:
        click.echo(f"would add {kind} on slide {slide}")
        return

    def _emu(spec: str):
        s = spec.strip().lower()
        if s.endswith("in"):
            return Inches(float(s[:-2]))
        if s.endswith("cm"):
            return Cm(float(s[:-2]))
        if s.endswith("pt"):
            return Pt(float(s[:-2]))
        return Emu(int(s))

    x, y = _emu(x_raw), _emu(y_raw)
    w, h = _emu(w_raw), _emu(h_raw)

    prs = Presentation(str(src))
    slide_obj = prs.slides[slide - 1]
    shape_enum = getattr(MSO_SHAPE, SHAPE_MAP[kind])
    shape = slide_obj.shapes.add_shape(shape_enum, x, y, w, h)

    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(fill.lstrip("#")[:6])
    if line_color:
        shape.line.color.rgb = RGBColor.from_string(line_color.lstrip("#")[:6])
    if text is not None:
        shape.text_frame.text = text
        if text_color:
            rgb = RGBColor.from_string(text_color.lstrip("#")[:6])
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    run.font.color.rgb = rgb

    def _save(f):
        prs.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "slide": slide, "kind": kind})
    elif not quiet:
        click.echo(f"added {kind} to slide {slide}")
