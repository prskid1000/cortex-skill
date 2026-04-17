"""claw doc tabs-list — list tab ids + titles in a Doc."""

from __future__ import annotations

import json

import click

from claw.common import EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


def _walk_tabs(tabs: list[dict], depth: int = 0, path: list[int] | None = None):
    path = path or []
    for i, tab in enumerate(tabs or []):
        props = tab.get("tabProperties", {}) or {}
        yield {
            "tab_id": props.get("tabId"),
            "title": props.get("title"),
            "index": props.get("index", i),
            "depth": depth,
            "path": path + [i],
        }
        yield from _walk_tabs(tab.get("childTabs", []) or [], depth + 1, path + [i])


@click.command(name="tabs-list")
@click.argument("doc_id")
@common_output_options
def tabs_list(doc_id,
              force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """List all tabs in a Doc."""
    if dry_run:
        click.echo(f"would list tabs of {doc_id}")
        return

    try:
        proc = gws_run("docs", "documents", "get",
                       "--params", json.dumps({"documentId": doc_id,
                                               "includeTabsContent": True}))
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    if proc.returncode != 0:
        die(f"gws docs get failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    doc = json.loads(proc.stdout)
    tabs = list(_walk_tabs(doc.get("tabs", []) or []))

    if as_json:
        for t in tabs:
            emit_json({k: v for k, v in t.items() if k != "path"})
        return

    if not tabs:
        if not quiet:
            click.echo("(no tabs — legacy body-only doc)")
        return

    for t in tabs:
        indent = "  " * t["depth"]
        click.echo(f"{indent}{t['tab_id']}\t{t['title']}")
