"""claw html wrap — wrap matched elements in a new parent."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, EXIT_USAGE, common_output_options, die, emit_json, read_text, safe_write,
)


_SEL_RE = re.compile(r"^([a-zA-Z][\w-]*)((?:[#.][\w-]+)*)$")


def _parse_wrap_spec(spec: str) -> tuple[str, list[str], str | None]:
    """Parse tiny selector: `div`, `div.scroll`, `div.a.b#main`."""
    m = _SEL_RE.match(spec.strip())
    if not m:
        raise click.BadParameter(f"--with must be `tag[.class...][#id]`, got {spec!r}")
    tag = m.group(1)
    rest = m.group(2) or ""
    classes: list[str] = []
    id_ = None
    for tok in re.findall(r"[#.][\w-]+", rest):
        if tok.startswith("."):
            classes.append(tok[1:])
        else:
            id_ = tok[1:]
    return tag, classes, id_


@click.command(name="wrap")
@click.argument("src")
@click.option("--css", "css_selectors", multiple=True)
@click.option("--xpath", "xpath_selectors", multiple=True)
@click.option("--with", "wrap_spec", required=True,
              help="New parent: `tag`, `tag.class`, `tag.a.b#id`.")
@click.option("--in-place", is_flag=True)
@click.option("--out", default=None, type=click.Path(path_type=Path))
@common_output_options
def wrap(src: str, css_selectors: tuple[str, ...], xpath_selectors: tuple[str, ...],
         wrap_spec: str, in_place: bool, out: Path | None,
         force: bool, backup: bool, as_json: bool, dry_run: bool,
         quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Wrap each matched element in a new parent tag."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        die("beautifulsoup4 not installed", code=EXIT_INPUT,
            hint="pip install 'claw[html]'", as_json=as_json)

    if not css_selectors and not xpath_selectors:
        die("provide at least one --css or --xpath", code=EXIT_USAGE, as_json=as_json)

    try:
        tag_name, classes, id_ = _parse_wrap_spec(wrap_spec)
    except click.BadParameter as e:
        die(str(e), code=EXIT_USAGE, as_json=as_json)

    html = read_text(src)
    if dry_run:
        click.echo(f"would wrap {src} matches in <{tag_name}> "
                   f"class={classes} id={id_}")
        return

    soup = BeautifulSoup(html, "lxml")
    affected = 0

    def _new_wrapper():
        attrs: dict = {}
        if classes:
            attrs["class"] = " ".join(classes)
        if id_:
            attrs["id"] = id_
        return soup.new_tag(tag_name, attrs=attrs)

    for sel in css_selectors:
        for node in soup.select(sel):
            node.wrap(_new_wrapper())
            affected += 1

    if xpath_selectors:
        from lxml import etree
        tree = etree.HTML(str(soup))
        for xp in xpath_selectors:
            for node in tree.xpath(xp):
                parent = node.getparent()
                if parent is None:
                    continue
                wrapper = etree.SubElement(parent, tag_name)
                if classes:
                    wrapper.set("class", " ".join(classes))
                if id_:
                    wrapper.set("id", id_)
                idx = list(parent).index(node)
                parent.remove(wrapper)
                parent.insert(idx, wrapper)
                parent.remove(node)
                wrapper.append(node)
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
            click.echo(f"wrote {dst} ({affected} wrapped)", err=True)

    if as_json:
        emit_json({"matches_affected": affected,
                   "output_bytes": len(result.encode("utf-8"))})
