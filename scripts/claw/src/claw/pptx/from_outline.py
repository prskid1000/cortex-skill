"""claw pptx from-outline — build a deck from a Markdown outline."""

from __future__ import annotations

import re
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, common_output_options, die, emit_json, read_text, safe_write,
)


@click.command(name="from-outline")
@click.argument("out", type=click.Path(path_type=Path))
@click.option("--data", "md_src", required=True, help="Markdown file or '-' for stdin.")
@click.option("--template", "template_path", default=None,
              type=click.Path(exists=True, path_type=Path))
@click.option("--layout-title", "layout_title", default=0, type=int,
              help="Layout index for the very first (title) slide.")
@click.option("--layout-body", "layout_body", default=1, type=int,
              help="Layout index for content slides.")
@click.option("--notes-from-blockquote", "notes_bq", is_flag=True,
              help="Treat `> text` lines as speaker notes.")
@common_output_options
def from_outline(out: Path, md_src: str, template_path: Path | None,
                 layout_title: int, layout_body: int, notes_bq: bool,
                 force: bool, backup: bool, as_json: bool, dry_run: bool,
                 quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Build a deck from a Markdown outline (H1 = title slide, H2 = content slide)."""
    try:
        from pptx import Presentation
    except ImportError:
        die("python-pptx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[pptx]'", as_json=as_json)

    md = read_text(md_src)
    slides = _parse_outline(md, notes_bq=notes_bq)
    if not slides:
        die("outline produced no slides", code=EXIT_INPUT, as_json=as_json)

    if dry_run:
        click.echo(f"would write {out} with {len(slides)} slide(s)")
        return

    if template_path:
        prs = Presentation(str(template_path))
        slide_ids = list(prs.slides._sldIdLst)
        for sid in slide_ids:
            prs.slides._sldIdLst.remove(sid)
    else:
        prs = Presentation()

    layout_count = len(prs.slide_layouts)
    if layout_title >= layout_count or layout_body >= layout_count:
        die(f"layout index out of range (0..{layout_count - 1})",
            code=EXIT_INPUT, as_json=as_json)

    for i, slide_data in enumerate(slides):
        layout_idx = layout_title if (i == 0 and slide_data["kind"] == "title") else layout_body
        layout = prs.slide_layouts[layout_idx]
        slide = prs.slides.add_slide(layout)
        if slide.shapes.title is not None:
            slide.shapes.title.text = slide_data["title"]
        bullets = slide_data.get("bullets", [])
        if bullets:
            body_ph = next((ph for ph in slide.placeholders
                            if ph.placeholder_format.idx != 0 and ph.has_text_frame), None)
            if body_ph is not None:
                tf = body_ph.text_frame
                tf.text = bullets[0]
                for extra in bullets[1:]:
                    tf.add_paragraph().text = extra
        if slide_data.get("notes"):
            slide.notes_slide.notes_text_frame.text = slide_data["notes"]

    def _save(f):
        prs.save(f)

    safe_write(out, _save, force=force, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(out), "slides": len(slides)})
    elif not quiet:
        click.echo(f"wrote {out} with {len(slides)} slide(s)")


def _parse_outline(md: str, *, notes_bq: bool) -> list[dict]:
    slides: list[dict] = []
    current: dict | None = None
    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        h1 = re.match(r"^#\s+(.+)$", line)
        h2 = re.match(r"^##\s+(.+)$", line)
        bullet = re.match(r"^\s*[-*]\s+(.+)$", line)
        note = re.match(r"^>\s+(.+)$", line)
        if h1:
            if current:
                slides.append(current)
            current = {"kind": "title" if not slides else "body",
                       "title": h1.group(1).strip(),
                       "bullets": [], "notes": ""}
        elif h2:
            if current:
                slides.append(current)
            current = {"kind": "body", "title": h2.group(1).strip(),
                       "bullets": [], "notes": ""}
        elif bullet and current is not None:
            current["bullets"].append(bullet.group(1).strip())
        elif note and current is not None and notes_bq:
            existing = current["notes"]
            current["notes"] = (existing + "\n" + note.group(1).strip()).strip()
        elif current is not None and not line.startswith("#"):
            current["bullets"].append(line.strip())
    if current:
        slides.append(current)
    return slides
