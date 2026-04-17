"""claw html sanitize — allow-list HTML cleanup."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, common_output_options, die, emit_json, read_text, safe_write,
)


_WARN = ("warning: claw html sanitize is a convenience tool, NOT a security boundary. "
         "For untrusted HTML destined for a browser, use `bleach` directly.\n")

_BLEACH_MISSING_WARN = (
    "warning: --strict-allow requested but `bleach` is not installed; "
    "falling back to lxml_html_clean with `safe_attrs_only=True` (best-effort). "
    "Install with: pip install bleach\n"
)

_CATEGORY_MAP = {
    "scripts":  ("scripts", True),
    "iframes":  ("frames", True),
    "style":    ("style", True),
    "comments": ("comments", True),
    "forms":    ("forms", True),
    "embeds":   ("embedded", True),
}

_DEFAULT_ATTRS = {"href", "src", "alt", "title", "class", "id"}


def _parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [x.strip() for x in value.split(",") if x.strip()]


def _sanitize_via_bleach(html: str, allow_tags: list[str], allow_attrs: set[str]) -> str:
    import bleach
    attrs_map = {"*": sorted(allow_attrs)}
    return bleach.clean(html, tags=allow_tags, attributes=attrs_map, strip=True)


def _sanitize_via_lxml(html: str, allow_tags: list[str], allow_attrs: set[str],
                      remove_cats: list[str], strip_unknown: bool) -> str:
    try:
        from lxml_html_clean import Cleaner
    except ImportError:
        try:
            from lxml.html.clean import Cleaner
        except ImportError:
            raise
    from lxml import html as lxml_html, etree

    kwargs: dict = {
        "scripts": False, "javascript": True, "comments": False,
        "style": False, "inline_style": True, "links": False,
        "meta": False, "page_structure": False, "processing_instructions": True,
        "embedded": False, "frames": False, "forms": False,
        "annoying_tags": False, "safe_attrs_only": True,
    }
    kwargs["safe_attrs"] = frozenset(allow_attrs)
    for cat in remove_cats:
        if cat in _CATEGORY_MAP:
            flag, val = _CATEGORY_MAP[cat]
            kwargs[flag] = val
    if allow_tags:
        kwargs["allow_tags"] = list(allow_tags)
        kwargs["remove_unknown_tags"] = False
    elif strip_unknown:
        kwargs["remove_unknown_tags"] = True

    cleaner = Cleaner(**kwargs)
    tree = lxml_html.fromstring(html)
    cleaned = cleaner.clean_html(tree)
    return etree.tostring(cleaned, encoding="unicode", method="html")


@click.command(name="sanitize")
@click.argument("src")
@click.option("--allow", default=None, help="Comma-separated tags to keep (allow-list).")
@click.option("--allow-attr", default=None,
              help="Comma-separated attrs to keep (default href,src,alt,title,class,id).")
@click.option("--remove", default="scripts,iframes,style,forms,embeds",
              help="Categories to remove.")
@click.option("--strip-unknown", is_flag=True,
              help="Decompose unknown tags instead of unwrapping.")
@click.option("--strict-allow", is_flag=True,
              help="Use bleach's strict allow-list semantics (requires `bleach`).")
@click.option("--in-place", is_flag=True)
@click.option("--out", default=None, type=click.Path(path_type=Path))
@common_output_options
def sanitize(src: str, allow: str | None, allow_attr: str | None, remove: str,
             strip_unknown: bool, strict_allow: bool, in_place: bool, out: Path | None,
             force: bool, backup: bool, as_json: bool, dry_run: bool,
             quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Allow-list sanitization (not a security boundary — use bleach for that)."""
    sys.stderr.write(_WARN)

    allow_tags = _parse_csv(allow)
    allow_attrs = set(_DEFAULT_ATTRS)
    for a in _parse_csv(allow_attr):
        allow_attrs.add(a)
    remove_cats = _parse_csv(remove)

    html = read_text(src)
    if dry_run:
        click.echo(f"would sanitize {src}")
        return

    used_bleach = False
    if strict_allow:
        try:
            result = _sanitize_via_bleach(html, allow_tags, allow_attrs)
            used_bleach = True
        except ImportError:
            sys.stderr.write(_BLEACH_MISSING_WARN)
            try:
                result = _sanitize_via_lxml(html, allow_tags, allow_attrs,
                                            remove_cats, strip_unknown)
            except ImportError:
                die("neither bleach nor lxml_html_clean installed", code=EXIT_INPUT,
                    hint="pip install 'claw[html]' or pip install bleach", as_json=as_json)
    else:
        try:
            result = _sanitize_via_lxml(html, allow_tags, allow_attrs,
                                        remove_cats, strip_unknown)
        except ImportError:
            die("lxml_html_clean not installed", code=EXIT_INPUT,
                hint="pip install 'claw[html]'", as_json=as_json)

    dst = Path(src) if in_place and src != "-" else out
    if dst is None or str(dst) == "-":
        sys.stdout.write(result)
    else:
        safe_write(dst, lambda f: f.write(result.encode("utf-8")),
                   force=force or in_place, backup=backup, mkdir=mkdir)
        if not quiet:
            click.echo(f"wrote {dst}", err=True)

    if as_json:
        emit_json({"output_bytes": len(result.encode("utf-8")), "engine":
                   "bleach" if used_bleach else "lxml_html_clean"})
