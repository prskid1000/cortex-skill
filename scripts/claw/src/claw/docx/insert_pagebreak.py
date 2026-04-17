"""claw docx insert pagebreak — force a page break before / after an anchor."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


@click.group(name="insert")
def insert() -> None:
    """Structural insertions (pagebreak, ...)."""


@insert.command(name="pagebreak")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--before", "before_text", default=None,
              help="Anchor paragraph text — break inserted BEFORE it.")
@click.option("--after", "after_text", default=None,
              help="Anchor paragraph text — break inserted AFTER it.")
@click.option("--match-nth", "match_nth", default=1, type=int,
              help="If anchor matches multiple paragraphs, pick the Nth (1-based).")
@common_output_options
def insert_pagebreak(src: Path, before_text: str | None, after_text: str | None,
                     match_nth: int,
                     force: bool, backup: bool, as_json: bool, dry_run: bool,
                     quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Insert a block-level page break relative to a paragraph anchor."""
    try:
        from docx import Document
    except ImportError:
        die("python-docx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[docx]'", as_json=as_json)

    if bool(before_text) == bool(after_text):
        die("specify exactly one of --before or --after",
            code=EXIT_INPUT, as_json=as_json)

    needle = before_text or after_text
    is_before = before_text is not None

    if dry_run:
        click.echo(f"would insert pagebreak {'before' if is_before else 'after'} {needle!r}")
        return

    doc = Document(str(src))
    matches = [p for p in doc.paragraphs if needle in p.text]
    if not matches:
        die(f"anchor not found: {needle!r}", code=EXIT_INPUT, as_json=as_json)
    if match_nth < 1 or match_nth > len(matches):
        die(f"--match-nth {match_nth} out of range (1..{len(matches)})",
            code=EXIT_INPUT, as_json=as_json)
    target = matches[match_nth - 1]

    if is_before:
        target.paragraph_format.page_break_before = True
    else:
        new_p = doc.add_paragraph()
        new_p.paragraph_format.page_break_before = True
        new_el = new_p._p
        new_el.getparent().remove(new_el)
        target._p.addnext(new_el)

    def _save(f):
        doc.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src),
                   "position": "before" if is_before else "after",
                   "anchor": needle})
    elif not quiet:
        click.echo(f"inserted page break {'before' if is_before else 'after'} {needle!r}")
