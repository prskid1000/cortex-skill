"""claw docx style — define or apply paragraph / character styles."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


@click.group(name="style")
def style() -> None:
    """Define or apply paragraph / character styles."""


@style.command(name="define")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--name", "style_name", required=True)
@click.option("--base", "base_style", default="Normal",
              help="Style to inherit from.")
@click.option("--font", "font_name", default=None)
@click.option("--size", "font_size", default=None, type=int)
@click.option("--bold", is_flag=True)
@click.option("--italic", is_flag=True)
@click.option("--color", default=None, help="#RRGGBB.")
@click.option("--space-before", "space_before", default=None, type=float,
              help="Space before in points.")
@click.option("--space-after", "space_after", default=None, type=float)
@click.option("--kind", default="paragraph",
              type=click.Choice(["paragraph", "character"]))
@common_output_options
def style_define(src: Path, style_name: str, base_style: str,
                 font_name: str | None, font_size: int | None,
                 bold: bool, italic: bool, color: str | None,
                 space_before: float | None, space_after: float | None,
                 kind: str,
                 force: bool, backup: bool, as_json: bool, dry_run: bool,
                 quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Register a new style on the document."""
    try:
        from docx import Document
        from docx.enum.style import WD_STYLE_TYPE
        from docx.shared import Pt, RGBColor
    except ImportError:
        die("python-docx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[docx]'", as_json=as_json)

    if dry_run:
        click.echo(f"would define {kind} style {style_name!r} base={base_style}")
        return

    doc = Document(str(src))
    style_type = (WD_STYLE_TYPE.PARAGRAPH if kind == "paragraph"
                  else WD_STYLE_TYPE.CHARACTER)
    styles = doc.styles
    if style_name in [s.name for s in styles]:
        die(f"style already exists: {style_name!r}",
            code=EXIT_INPUT, as_json=as_json)
    new_style = styles.add_style(style_name, style_type)
    try:
        new_style.base_style = styles[base_style]
    except KeyError:
        die(f"base style not found: {base_style!r}",
            code=EXIT_INPUT, as_json=as_json)

    font = new_style.font
    if font_name:
        font.name = font_name
    if font_size:
        font.size = Pt(font_size)
    if bold:
        font.bold = True
    if italic:
        font.italic = True
    if color:
        font.color.rgb = RGBColor.from_string(color.lstrip("#")[:6])

    if kind == "paragraph" and (space_before is not None or space_after is not None):
        pf = new_style.paragraph_format
        if space_before is not None:
            pf.space_before = Pt(space_before)
        if space_after is not None:
            pf.space_after = Pt(space_after)

    def _save(f):
        doc.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "defined": style_name, "kind": kind,
                   "base": base_style})
    elif not quiet:
        click.echo(f"defined {kind} style {style_name}")


@style.command(name="apply")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--name", "style_name", required=True)
@click.option("--to", "to_text", default=None,
              help="Anchor text — paragraphs containing this get the style.")
@click.option("--match-nth", "match_nth", default=None, type=int)
@click.option("--all-matching-style", "from_style", default=None,
              help="Re-style every paragraph currently using this style.")
@common_output_options
def style_apply(src: Path, style_name: str, to_text: str | None,
                match_nth: int | None, from_style: str | None,
                force: bool, backup: bool, as_json: bool, dry_run: bool,
                quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Apply an existing style to one or more paragraphs."""
    try:
        from docx import Document
    except ImportError:
        die("python-docx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[docx]'", as_json=as_json)

    if not (to_text or from_style):
        die("specify --to or --all-matching-style",
            code=EXIT_INPUT, as_json=as_json)

    if dry_run:
        click.echo(f"would apply style {style_name}")
        return

    doc = Document(str(src))
    try:
        target_style = doc.styles[style_name]
    except KeyError:
        die(f"style not found: {style_name!r}",
            code=EXIT_INPUT, as_json=as_json)

    touched = 0
    if to_text:
        matches = [p for p in doc.paragraphs if to_text in p.text]
        if not matches:
            die(f"anchor not found: {to_text!r}",
                code=EXIT_INPUT, as_json=as_json)
        if match_nth is not None:
            if match_nth < 1 or match_nth > len(matches):
                die(f"--match-nth {match_nth} out of range (1..{len(matches)})",
                    code=EXIT_INPUT, as_json=as_json)
            matches = [matches[match_nth - 1]]
        for p in matches:
            p.style = target_style
            touched += 1

    if from_style:
        for p in doc.paragraphs:
            if p.style and p.style.name == from_style:
                p.style = target_style
                touched += 1

    def _save(f):
        doc.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "style": style_name, "applied": touched})
    elif not quiet:
        click.echo(f"applied {style_name} to {touched} paragraph(s)")
