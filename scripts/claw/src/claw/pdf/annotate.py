"""claw pdf annotate — highlight, sticky note, or free-hand ink."""
from __future__ import annotations

import re
from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, safe_write


def _hex_to_rgb(h: str) -> tuple[float, float, float]:
    s = h.lstrip("#")
    if len(s) not in (6, 8):
        raise ValueError(f"bad color: {h}")
    r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    return (r / 255, g / 255, b / 255)


def _parse_ink(path: str) -> list[list[tuple[float, float]]]:
    out = []
    for token in path.split():
        parts = token.split(",")
        if len(parts) != 2:
            raise click.BadParameter(f"bad ink point: {token}")
        out.append((float(parts[0]), float(parts[1])))
    return [out]


@click.command(name="annotate")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--page", "page_num", type=int, required=True)
@click.option("--highlight", "highlight_term", default=None,
              help="Highlight every occurrence of TERM on the page.")
@click.option("--regex", "is_regex", is_flag=True,
              help="Treat --highlight value as a regex.")
@click.option("--note", "note_text", default=None,
              help="Add a sticky note (requires --at).")
@click.option("--at", "note_at", default=None, help="x,y anchor for --note.")
@click.option("--ink-path", "ink_path", default=None,
              help='Free-hand ink as "x1,y1 x2,y2 ...".')
@click.option("--color", default="#FFFF00")
@click.option("--opacity", type=float, default=0.5)
@click.option("--author", default=None)
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True)
@common_output_options
def annotate(src: Path, page_num: int, highlight_term: str | None, is_regex: bool,
             note_text: str | None, note_at: str | None,
             ink_path: str | None, color: str, opacity: float,
             author: str | None, out: Path | None, in_place: bool,
             force: bool, backup: bool, as_json: bool, dry_run: bool,
             quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Add annotations to a page of <SRC>."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    if not (out or in_place):
        die("pass --out FILE or --in-place", code=2)
    if not (highlight_term or note_text or ink_path):
        die("pass at least one of --highlight / --note / --ink-path", code=2)
    target = src if in_place else out
    assert target is not None

    rgb = _hex_to_rgb(color)
    doc = fitz.open(str(src))
    try:
        if not 1 <= page_num <= doc.page_count:
            die(f"--page {page_num} out of range (1..{doc.page_count})")
        page = doc.load_page(page_num - 1)
        count = 0

        if highlight_term:
            if is_regex:
                pat = re.compile(highlight_term)
                text = page.get_text("text")
                for m in pat.finditer(text):
                    rects = page.search_for(m.group(0), quads=False)
                    for r in rects:
                        ann = page.add_highlight_annot(r)
                        ann.set_colors(stroke=rgb)
                        ann.set_opacity(opacity)
                        if author:
                            ann.set_info(title=author)
                        ann.update()
                        count += 1
            else:
                rects = page.search_for(highlight_term, quads=False)
                for r in rects:
                    ann = page.add_highlight_annot(r)
                    ann.set_colors(stroke=rgb)
                    ann.set_opacity(opacity)
                    if author:
                        ann.set_info(title=author)
                    ann.update()
                    count += 1

        if note_text:
            if not note_at:
                die("--note requires --at x,y", code=2)
            try:
                x, y = (float(v) for v in note_at.split(","))
            except ValueError:
                die("--at must be x,y", code=2)
            ann = page.add_text_annot(fitz.Point(x, y), note_text)
            ann.set_colors(stroke=rgb)
            ann.set_opacity(opacity)
            if author:
                ann.set_info(title=author)
            ann.update()
            count += 1

        if ink_path:
            strokes = _parse_ink(ink_path)
            ann = page.add_ink_annot(strokes)
            ann.set_colors(stroke=rgb)
            ann.set_opacity(opacity)
            if author:
                ann.set_info(title=author)
            ann.update()
            count += 1

        if dry_run:
            click.echo(f"would add {count} annotations on page {page_num} → {target}")
            return

        data = doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()

    safe_write(target, lambda f: f.write(data),
               force=force or in_place, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(target), "page": page_num, "annotations": count})
    elif not quiet:
        click.echo(f"added {count} annotations → {target}")
