"""claw xml stream-xpath — iterparse with constant-memory cleanup."""

from __future__ import annotations

import re
import sys

import click

from claw.common import (
    EXIT_INPUT, EXIT_USAGE, common_output_options, die, emit_json,
)


def _parse_kv(items: tuple[str, ...]) -> dict[str, str]:
    out: dict[str, str] = {}
    for it in items:
        if "=" not in it:
            raise click.BadParameter(f"expected K=V, got {it!r}")
        k, v = it.split("=", 1)
        out[k.strip()] = v
    return out


def _coerce(val: str) -> object:
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


@click.command(name="stream-xpath")
@click.argument("src", type=click.Path(exists=True, dir_okay=False))
@click.argument("expression")
@click.option("--tag", required=True, help="Top-level repeating element to iterate.")
@click.option("--var", "variables", multiple=True, metavar="NAME=VALUE")
@click.option("--ns", "namespaces", multiple=True, metavar="PREFIX=URI")
@click.option("--text", "as_text", is_flag=True)
@click.option("--xml", "as_xml", is_flag=True, default=True)
@click.option("--attr", default=None)
@click.option("--allow-undeclared-vars", is_flag=True)
@click.option("--huge-tree", is_flag=True)
@common_output_options
def stream_xpath(src: str, expression: str, tag: str,
                 variables: tuple[str, ...], namespaces: tuple[str, ...],
                 as_text: bool, as_xml: bool, attr: str | None,
                 allow_undeclared_vars: bool, huge_tree: bool,
                 force: bool, backup: bool, as_json: bool, dry_run: bool,
                 quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Stream giant XML — evaluate EXPR against each <TAG> element."""
    try:
        from lxml import etree
    except ImportError:
        die("lxml not installed", code=EXIT_INPUT,
            hint="pip install 'claw[xml]'", as_json=as_json)

    try:
        vars_map = {k: _coerce(v) for k, v in _parse_kv(variables).items()}
        ns_map = _parse_kv(namespaces) or None
    except click.BadParameter as e:
        die(str(e), code=EXIT_USAGE, as_json=as_json)

    used_vars = set(re.findall(r"\$([A-Za-z_][A-Za-z0-9_]*)", expression))
    missing = used_vars - set(vars_map.keys())
    if missing and not allow_undeclared_vars:
        die(f"unbound XPath variables: {sorted(missing)}; use --var",
            code=EXIT_USAGE, as_json=as_json)

    if dry_run:
        click.echo(f"would stream {src} tag={tag} expr={expression!r}")
        return

    count = 0
    try:
        context = etree.iterparse(
            src, events=("end",), tag=tag, huge_tree=huge_tree,
            resolve_entities=False, no_network=True,
        )
        for _event, elem in context:
            try:
                results = elem.xpath(expression, namespaces=ns_map, **vars_map)
            except etree.XPathEvalError as e:
                die(f"XPath error: {e}", code=EXIT_USAGE, as_json=as_json)

            if not isinstance(results, list):
                results = [results]

            for r in results:
                if attr is not None and hasattr(r, "get"):
                    out = r.get(attr) or ""
                elif as_text:
                    if hasattr(r, "text_content"):
                        out = r.text_content()
                    elif hasattr(r, "text") and r.text is not None:
                        out = r.text
                    else:
                        out = str(r)
                elif hasattr(r, "tag"):
                    out = etree.tostring(r, encoding="unicode")
                else:
                    out = str(r)
                if as_json:
                    emit_json({"value": out})
                else:
                    sys.stdout.write(out + "\n")

            count += 1
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
    except etree.XMLSyntaxError as e:
        die(f"XML parse error: {e}", code=EXIT_INPUT, as_json=as_json)

    if verbose:
        click.echo(f"processed {count} <{tag}> elements", err=True)
