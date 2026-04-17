"""claw xml xslt — XSLT 1.0 transform."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, EXIT_USAGE, common_output_options, die, emit_json, safe_write,
)


def _parse_kv(items: tuple[str, ...]) -> dict[str, str]:
    out: dict[str, str] = {}
    for it in items:
        if "=" not in it:
            raise click.BadParameter(f"expected K=V, got {it!r}")
        k, v = it.split("=", 1)
        out[k.strip()] = v
    return out


def _inject_top_level_params(xsl_tree, etree, params: dict[str, str]) -> None:
    """Inject or override <xsl:param name="NAME" select="EXPR"/> at the top level.

    Works around the fact that `XSLT.__call__(**kw)` requires Python-identifier
    keys: non-identifier XSLT param names (e.g. ``foo-bar``) can't be passed as
    kwargs, so we bake them into the stylesheet instead. Any existing top-level
    param with the same name is replaced so CLI values always win.
    """
    if not params:
        return
    XSL_NS = "http://www.w3.org/1999/XSL/Transform"
    root = xsl_tree.getroot()
    existing = {}
    for child in list(root):
        if child.tag == f"{{{XSL_NS}}}param":
            name = child.get("name")
            if name is not None:
                existing[name] = child
    for name, expr in params.items():
        if name in existing:
            node = existing[name]
            node.set("select", expr)
            for sub in list(node):
                node.remove(sub)
            node.text = None
        else:
            node = etree.Element(f"{{{XSL_NS}}}param")
            node.set("name", name)
            node.set("select", expr)
            root.insert(0, node)


@click.command(name="xslt")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.argument("stylesheet", type=click.Path(exists=True, path_type=Path))
@click.option("--param", "params", multiple=True, metavar="KEY=VALUE",
              help="XSLT string param (quoted literal).")
@click.option("--param-xpath", "xpath_params", multiple=True, metavar="KEY=EXPR",
              help="XSLT param using raw XPath expression (supports non-identifier names).")
@click.option("--out", default=None, type=click.Path(path_type=Path))
@click.option("--profile", default=None, type=click.Path(path_type=Path))
@common_output_options
def xslt(src: Path, stylesheet: Path, params: tuple[str, ...],
         xpath_params: tuple[str, ...], out: Path | None, profile: Path | None,
         force: bool, backup: bool, as_json: bool, dry_run: bool,
         quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Apply STYLESHEET to SRC (XSLT 1.0)."""
    try:
        from lxml import etree
    except ImportError:
        die("lxml not installed", code=EXIT_INPUT,
            hint="pip install 'claw[xml]'", as_json=as_json)

    try:
        str_params = _parse_kv(params)
        expr_params = _parse_kv(xpath_params)
    except click.BadParameter as e:
        die(str(e), code=EXIT_USAGE, as_json=as_json)

    if dry_run:
        click.echo(f"would transform {src} via {stylesheet}")
        return

    parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)
    try:
        doc = etree.parse(str(src), parser=parser)
        xsl = etree.parse(str(stylesheet), parser=parser)
    except etree.XMLSyntaxError as e:
        die(f"parse error: {e}", code=EXIT_INPUT, as_json=as_json)

    identifier_exprs: dict[str, str] = {}
    non_identifier_exprs: dict[str, str] = {}
    for k, v in expr_params.items():
        (identifier_exprs if k.isidentifier() else non_identifier_exprs)[k] = v

    identifier_strs: dict[str, str] = {}
    non_identifier_strs: dict[str, str] = {}
    for k, v in str_params.items():
        (identifier_strs if k.isidentifier() else non_identifier_strs)[k] = v

    # Non-identifier string params: inject a quoted XPath literal that matches the value.
    for k, v in non_identifier_strs.items():
        non_identifier_exprs[k] = _xpath_string_literal(v)

    if non_identifier_exprs:
        _inject_top_level_params(xsl, etree, non_identifier_exprs)

    try:
        transform = etree.XSLT(xsl)
    except etree.XSLTParseError as e:
        die(f"XSLT parse error: {e}", code=EXIT_INPUT, as_json=as_json)

    kwargs: dict = {}
    for k, v in identifier_strs.items():
        kwargs[k] = etree.XSLT.strparam(v)
    for k, v in identifier_exprs.items():
        kwargs[k] = v

    try:
        result = transform(doc, profile_run=profile is not None, **kwargs)
    except etree.XSLTApplyError as e:
        die(f"XSLT error: {e}", code=EXIT_INPUT, as_json=as_json)

    if profile is not None and hasattr(result, "xslt_profile") and result.xslt_profile is not None:
        prof_bytes = etree.tostring(result.xslt_profile, pretty_print=True)
        profile.write_bytes(prof_bytes)

    out_bytes = bytes(result)
    if out is None or str(out) == "-":
        sys.stdout.buffer.write(out_bytes)
    else:
        safe_write(out, lambda f: f.write(out_bytes),
                   force=force, backup=backup, mkdir=mkdir)
        if not quiet:
            click.echo(f"wrote {out}", err=True)

    if as_json:
        emit_json({"out": str(out) if out else None, "bytes": len(out_bytes)})


def _xpath_string_literal(value: str) -> str:
    """Return an XPath 1.0 string literal that evaluates to `value`.

    Handles both quote types. If the value contains both kinds, wrap with
    concat() since XPath 1.0 has no escape mechanism for quotes.
    """
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts: list[str] = []
    buf = ""
    for ch in value:
        if ch == "'":
            if buf:
                parts.append(f"'{buf}'")
                buf = ""
            parts.append('"\'"')
        else:
            buf += ch
    if buf:
        parts.append(f"'{buf}'")
    return "concat(" + ", ".join(parts) + ")"
