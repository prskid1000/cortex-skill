"""claw html unwrap — replace matched elements with their children."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, EXIT_USAGE, common_output_options, die, emit_json, read_text, safe_write,
)


@click.command(name="unwrap")
@click.argument("src")
@click.option("--css", "css_selectors", multiple=True, help="CSS selectors (repeatable).")
@click.option("--xpath", "xpath_selectors", multiple=True)
@click.option("--in-place", is_flag=True)
@click.option("--out", default=None, type=click.Path(path_type=Path))
@common_output_options
def unwrap(src: str, css_selectors: tuple[str, ...], xpath_selectors: tuple[str, ...],
           in_place: bool, out: Path | None, force: bool, backup: bool, as_json: bool,
           dry_run: bool, quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Remove matched tags but keep their children (tag.unwrap())."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        die("beautifulsoup4 not installed", code=EXIT_INPUT,
            hint="pip install 'claw[html]'", as_json=as_json)

    if not css_selectors and not xpath_selectors:
        die("provide at least one --css or --xpath", code=EXIT_USAGE, as_json=as_json)

    html = read_text(src)
    if dry_run:
        click.echo(f"would unwrap from {src}: css={list(css_selectors)} "
                   f"xpath={list(xpath_selectors)}")
        return

    soup = BeautifulSoup(html, "lxml")
    affected = 0
    for sel in css_selectors:
        for node in soup.select(sel):
            node.unwrap()
            affected += 1

    if xpath_selectors:
        from lxml import etree
        tree = etree.HTML(str(soup))
        for xp in xpath_selectors:
            for node in tree.xpath(xp):
                parent = node.getparent()
                if parent is None:
                    continue
                idx = list(parent).index(node)
                tail = node.tail or ""
                if node.text:
                    if idx == 0:
                        parent.text = (parent.text or "") + node.text
                    else:
                        prev = parent[idx - 1]
                        prev.tail = (prev.tail or "") + node.text
                children = list(node)
                for i, child in enumerate(children):
                    parent.insert(idx + i, child)
                if children:
                    children[-1].tail = (children[-1].tail or "") + tail
                elif idx > 0:
                    parent[idx - 1].tail = (parent[idx - 1].tail or "") + tail
                else:
                    parent.text = (parent.text or "") + tail
                if node in list(parent):
                    parent.remove(node)
                affected += 1
        result = etree.tostring(tree, encoding="unicode", method="html")
    else:
        result = str(soup)

    dst = Path(src) if in_place and src != "-" else out
    if dst is None or str(dst) == "-":
        sys.stdout.write(result)
    else:
        safe_write(dst, lambda f: f.write(result.encode("utf-8")),
                   force=force or in_place, backup=backup, mkdir=mkdir)
        if not quiet:
            click.echo(f"wrote {dst} ({affected} unwrapped)", err=True)

    if as_json:
        emit_json({"matches_affected": affected,
                   "output_bytes": len(result.encode("utf-8"))})
