"""claw doc replace — wrap docs.batchUpdate replaceAllText request."""

from __future__ import annotations

import json

import click

from claw.common import EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


@click.command(name="replace")
@click.argument("doc_id")
@click.option("--find", "find_text", required=True, help="Literal text to find.")
@click.option("--with", "replace_text", required=True, help="Replacement text.")
@click.option("--match-case", is_flag=True)
@click.option("--tab", "tab_id", default=None,
              help="Restrict replacement to this tab (default: all tabs).")
@common_output_options
def replace(doc_id, find_text, replace_text, match_case, tab_id,
            force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Find-and-replace literal text across the doc."""
    req: dict = {
        "replaceAllText": {
            "containsText": {"text": find_text, "matchCase": bool(match_case)},
            "replaceText": replace_text,
        }
    }
    if tab_id:
        req["replaceAllText"]["tabsCriteria"] = {"tabIds": [tab_id]}

    body = {"requests": [req]}

    if dry_run:
        click.echo(f"would replace {find_text!r} → {replace_text!r} in {doc_id}")
        return

    try:
        proc = gws_run("docs", "documents", "batchUpdate",
                       "--params", json.dumps({"documentId": doc_id}),
                       "--json", json.dumps(body))
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    if proc.returncode != 0:
        die(f"gws docs batchUpdate failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    reply = json.loads(proc.stdout) if proc.stdout.strip() else {}
    occurrences = 0
    for r in reply.get("replies", []) or []:
        occurrences += (r.get("replaceAllText") or {}).get("occurrencesChanged", 0) or 0

    if as_json:
        emit_json({"doc_id": doc_id, "occurrences_changed": occurrences,
                   "find": find_text, "replace": replace_text})
    elif not quiet:
        click.echo(f"replaced {occurrences} occurrence(s) of {find_text!r} in {doc_id}")
