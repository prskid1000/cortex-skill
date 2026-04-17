"""claw pdf bookmark-add — append a single bookmark entry."""
from __future__ import annotations

from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, safe_write


@click.command(name="bookmark-add")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--title", required=True)
@click.option("--page", "page_num", type=int, required=True, help="1-indexed page.")
@click.option("--level", type=int, default=1)
@click.option("--parent", default=None,
              help="Title of a parent TOC entry; the new bookmark nests under it.")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True)
@common_output_options
def bookmark_add(src: Path, title: str, page_num: int, level: int,
                 parent: str | None,
                 out: Path | None, in_place: bool,
                 force: bool, backup: bool, as_json: bool, dry_run: bool,
                 quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Append a bookmark to <SRC>'s outline."""
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
        if not 1 <= page_num <= doc.page_count:
            die(f"--page {page_num} out of range (1..{doc.page_count})")
        current = doc.get_toc(simple=True) or []

        insert_level = level
        if parent:
            for idx, entry in enumerate(current):
                if entry[1] == parent:
                    insert_level = entry[0] + 1
                    current.insert(idx + 1, [insert_level, title, page_num])
                    break
            else:
                die(f"parent bookmark not found: {parent!r}", code=2)
        else:
            current.append([insert_level, title, page_num])

        doc.set_toc(current)
        if dry_run:
            click.echo(f"would add bookmark {title!r} at page {page_num} → {target}")
            return
        data = doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()

    safe_write(target, lambda f: f.write(data),
               force=force or in_place, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(target), "title": title, "page": page_num,
                   "level": insert_level})
    elif not quiet:
        click.echo(f"added bookmark {title!r} → {target}")
