"""claw html replace — replace matched elements with text or HTML fragment."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, EXIT_USAGE, common_output_options, die, emit_json, read_text, safe_write,
)


@click.command(name="replace")
@click.argument("src")
@click.option("--css", "css_selectors", multiple=True)
@click.option("--xpath", "xpath_selectors", multiple=True)
@click.option("--text", "text_replacement", default=None,
              help="Replace matches with this literal text.")
@click.option("--html", "html_replacement", default=None,
              help="Replace matches with this HTML fragment.")
@click.option("--with-file", "with_file", default=None, type=click.Path(exists=True),
              help="Read HTML fragment from FILE.")
@click.option("--in-place", is_flag=True)
@click.option("--out", default=None, type=click.Path(path_type=Path))
@common_output_options
def replace(src: str, css_selectors: tuple[str, ...], xpath_selectors: tuple[str, ...],
            text_replacement: str | None, html_replacement: str | None,
            with_file: str | None, in_place: bool, out: Path | None,
            force: bool, backup: bool, as_json: bool, dry_run: bool,
            quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Replace matched elements (tag.replace_with(...))."""
    try:
        from bs4 import BeautifulSoup, NavigableString
    except ImportError:
        die("beautifulsoup4 not installed", code=EXIT_INPUT,
            hint="pip install 'claw[html]'", as_json=as_json)

    if not css_selectors and not xpath_selectors:
        die("provide at least one --css or --xpath", code=EXIT_USAGE, as_json=as_json)

    picked = [x for x in (text_replacement, html_replacement, with_file) if x is not None]
    if len(picked) != 1:
        die("exactly one of --text, --html, --with-file required",
            code=EXIT_USAGE, as_json=as_json)

    html_frag: str | None = None
    text_frag: str | None = None
    if text_replacement is not None:
        text_frag = text_replacement
    elif html_replacement is not None:
        html_frag = html_replacement
    elif with_file is not None:
        html_frag = Path(with_file).read_text(encoding="utf-8")

    html = read_text(src)
    if dry_run:
        click.echo(f"would replace in {src}")
        return

    soup = BeautifulSoup(html, "lxml")
    affected = 0

    def _make_replacement():
        if text_frag is not None:
            return NavigableString(text_frag)
        frag_soup = BeautifulSoup(html_frag, "lxml")
        body = frag_soup.body
        if body is None:
            return frag_soup
        children = list(body.children)
        if len(children) == 1:
            return children[0]
        wrapper = soup.new_tag("span")
        for c in children:
            wrapper.append(c)
        return wrapper

    for sel in css_selectors:
        for node in soup.select(sel):
            node.replace_with(_make_replacement())
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
                if text_frag is not None:
                    if idx == 0:
                        parent.text = (parent.text or "") + text_frag + tail
                    else:
                        prev = parent[idx - 1]
                        prev.tail = (prev.tail or "") + text_frag + tail
                    parent.remove(node)
                else:
                    frag_tree = etree.HTML(f"<div>{html_frag}</div>")
                    frag_div = frag_tree.find(".//div")
                    new_nodes = list(frag_div) if frag_div is not None else []
                    parent.remove(node)
                    for i, n in enumerate(new_nodes):
                        parent.insert(idx + i, n)
                    if new_nodes:
                        new_nodes[-1].tail = (new_nodes[-1].tail or "") + tail
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
            click.echo(f"wrote {dst} ({affected} replaced)", err=True)

    if as_json:
        emit_json({"matches_affected": affected,
                   "output_bytes": len(result.encode("utf-8"))})
