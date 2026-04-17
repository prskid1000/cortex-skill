"""claw docx hyperlink add — insert a hyperlink run relative to an anchor."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
HYPERLINK_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"


@click.group(name="hyperlink")
def hyperlink() -> None:
    """Hyperlink operations."""


@hyperlink.command(name="add")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--text", required=True, help="Link display text.")
@click.option("--url", required=True)
@click.option("--at", "anchor", default=None,
              help="Anchor paragraph text to place the link near.")
@click.option("--before/--after", "before", default=False)
@click.option("--match-nth", "match_nth", default=1, type=int)
@common_output_options
def hyperlink_add(src: Path, text: str, url: str, anchor: str | None,
                  before: bool, match_nth: int,
                  force: bool, backup: bool, as_json: bool, dry_run: bool,
                  quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Insert a clickable hyperlink paragraph relative to an anchor (or append)."""
    try:
        from docx import Document
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
    except ImportError:
        die("python-docx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[docx]'", as_json=as_json)

    if dry_run:
        click.echo(f"would add hyperlink {text!r} -> {url}")
        return

    doc = Document(str(src))
    part = doc.part
    r_id = part.relate_to(url, HYPERLINK_TYPE, is_external=True)

    new_p = doc.add_paragraph()

    hyperlink_el = OxmlElement("w:hyperlink")
    hyperlink_el.set(qn("r:id"), r_id)

    run_el = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    rstyle = OxmlElement("w:rStyle")
    rstyle.set(qn("w:val"), "Hyperlink")
    rpr.append(rstyle)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rpr.append(u)
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    rpr.append(color)
    run_el.append(rpr)

    t_el = OxmlElement("w:t")
    t_el.text = text
    t_el.set(qn("xml:space"), "preserve")
    run_el.append(t_el)
    hyperlink_el.append(run_el)
    new_p._p.append(hyperlink_el)

    if anchor:
        matches = [p for p in doc.paragraphs if anchor in p.text and p is not new_p]
        if not matches:
            die(f"anchor not found: {anchor!r}", code=EXIT_INPUT, as_json=as_json)
        if match_nth < 1 or match_nth > len(matches):
            die(f"--match-nth {match_nth} out of range (1..{len(matches)})",
                code=EXIT_INPUT, as_json=as_json)
        target = matches[match_nth - 1]
        new_el = new_p._p
        new_el.getparent().remove(new_el)
        if before:
            target._p.addprevious(new_el)
        else:
            target._p.addnext(new_el)

    def _save(f):
        doc.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "text": text, "url": url, "anchor": anchor})
    elif not quiet:
        click.echo(f"added hyperlink {text!r} -> {url}")
