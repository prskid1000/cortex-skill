"""claw doc append — append markdown to an existing Doc (no clear)."""

from __future__ import annotations

import json
from pathlib import Path

import click

from claw.common import EXIT_PARTIAL, EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


@click.command(name="append")
@click.argument("doc_id")
@click.option("--from", "source", default=None,
              type=click.Path(exists=True, dir_okay=False))
@click.option("--text", "text", default=None, help="Literal text to append.")
@click.option("--tab", "tab_id", default="t.0")
@click.option("--chunk-size", default=8, type=int)
@common_output_options
def append(doc_id, source, text, tab_id, chunk_size,
           force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Append markdown/text to the end of an existing Doc."""
    if not source and text is None:
        die("provide --from FILE or --text STR", code=EXIT_SYSTEM, as_json=as_json)

    from claw.doc.build import (
        _blocks_from_md, _dispatch, _find_tab_body, _max_end_index, _requests_for_blocks,
    )

    if source:
        md = Path(source).read_text(encoding="utf-8")
    else:
        md = text or ""

    blocks = _blocks_from_md(md)

    try:
        get = gws_run("docs", "documents", "get",
                      "--params", json.dumps({"documentId": doc_id,
                                              "includeTabsContent": True}))
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)
    if get.returncode != 0:
        die(f"gws docs get failed: {get.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    data = json.loads(get.stdout)
    body = _find_tab_body(data, tab_id) or {}
    start_index = max(_max_end_index(body) - 1, 1)

    requests, _ = _requests_for_blocks(blocks, tab_id, start_index)

    if dry_run:
        click.echo(f"would append {len(requests)} requests to {doc_id} "
                   f"at index {start_index}")
        return

    try:
        last_ok = _dispatch(doc_id, requests, chunk_size, 0, verbose=verbose)
    except RuntimeError as e:
        if as_json:
            emit_json({"doc_id": doc_id, "error": str(e)})
        die(str(e), code=EXIT_PARTIAL, as_json=as_json)
        return

    if as_json:
        emit_json({"doc_id": doc_id,
                   "chunks": (len(requests) + chunk_size - 1) // chunk_size,
                   "last_index": last_ok, "total_requests": len(requests),
                   "start_index": start_index})
    elif not quiet:
        click.echo(f"appended {len(requests)} requests to {doc_id}")
