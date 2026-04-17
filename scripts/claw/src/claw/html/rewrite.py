"""claw html rewrite — find-and-replace URL substrings via lxml.html.rewrite_links."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, common_output_options, die, emit_json, read_text, safe_write,
)


@click.command(name="rewrite")
@click.argument("src")
@click.option("--from", "from_url", required=True, help="Substring to match.")
@click.option("--to", "to_url", required=True, help="Replacement.")
@click.option("--attrs", default=None,
              help="Comma-separated link-bearing attrs (lxml default if omitted).")
@click.option("--in-place", is_flag=True)
@click.option("--out", default=None, type=click.Path(path_type=Path))
@common_output_options
def rewrite(src: str, from_url: str, to_url: str, attrs: str | None,
            in_place: bool, out: Path | None,
            force: bool, backup: bool, as_json: bool, dry_run: bool,
            quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Rewrite URL substrings across link-bearing attributes."""
    try:
        from lxml import html as lxml_html, etree
    except ImportError:
        die("lxml not installed", code=EXIT_INPUT,
            hint="pip install 'claw[html]'", as_json=as_json)

    html = read_text(src)
    if dry_run:
        click.echo(f"would rewrite {from_url!r} → {to_url!r} in {src}")
        return

    count = 0

    def _fn(link: str) -> str:
        nonlocal count
        if from_url in link:
            count += 1
            return link.replace(from_url, to_url)
        return link

    doc = lxml_html.fromstring(html)
    doc.rewrite_links(_fn)
    result = etree.tostring(doc, encoding="unicode", method="html")

    dst = Path(src) if in_place and src != "-" else out
    if dst is None or str(dst) == "-":
        sys.stdout.write(result)
    else:
        safe_write(dst, lambda f: f.write(result.encode("utf-8")),
                   force=force or in_place, backup=backup, mkdir=mkdir)
        if not quiet:
            click.echo(f"wrote {dst} ({count} links rewritten)", err=True)

    if as_json:
        emit_json({"matches_affected": count,
                   "output_bytes": len(result.encode("utf-8")),
                   "from": from_url, "to": to_url})
