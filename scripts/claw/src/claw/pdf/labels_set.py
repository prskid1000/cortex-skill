"""claw pdf labels-set — set PDF page label ruleset."""
from __future__ import annotations

from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, safe_write


STYLE_MAP = {"i": "r", "I": "R", "a": "a", "A": "A", "1": "D"}


def _parse_rule(rule: str, total: int) -> list[dict]:
    out: list[dict] = []
    for chunk in rule.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" not in chunk:
            raise click.BadParameter(f"bad rule chunk: {chunk!r}")
        style_part, range_part = chunk.split(":", 1)
        style = STYLE_MAP.get(style_part.strip())
        if style is None:
            raise click.BadParameter(f"unknown style: {style_part!r}")
        if "-" in range_part:
            a, b = range_part.split("-", 1)
            start = int(a)
            end = total if b.strip() == "end" else int(b)
        else:
            start = int(range_part)
            end = start
        out.append({"style": style, "startpage": start - 1, "firstpagenum": 1,
                    "_end": end})
    return out


@click.command(name="labels-set")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--rule", "rule_spec", required=True,
              help='Rule like "i:1-5,1:6-end". Styles: i I a A 1.')
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True)
@common_output_options
def labels_set(src: Path, rule_spec: str, out: Path | None, in_place: bool,
               force: bool, backup: bool, as_json: bool, dry_run: bool,
               quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Set page labels on <SRC> from --rule."""
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
        chunks = _parse_rule(rule_spec, doc.page_count)
        for c in chunks:
            c.pop("_end", None)
        doc.set_page_labels(chunks)
        if dry_run:
            click.echo(f"would set {len(chunks)} label rule(s) → {target}")
            return
        data = doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()

    safe_write(target, lambda f: f.write(data),
               force=force or in_place, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(target), "rules": len(chunks), "rule": rule_spec})
    elif not quiet:
        click.echo(f"set {len(chunks)} label rule(s) → {target}")
