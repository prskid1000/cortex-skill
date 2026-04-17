"""claw doc create — create a Google Doc, optionally populate from markdown."""

from __future__ import annotations

import json

import click

from claw.common import EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


@click.command(name="create")
@click.option("--title", required=True)
@click.option("--from", "source", default=None, type=click.Path(exists=True, dir_okay=False),
              help="Markdown file to populate the new doc from.")
@click.option("--parent", default=None, help="Drive folder ID.")
@click.option("--share", "shares", multiple=True,
              help="ACL spec: user:EMAIL:role | domain:DOMAIN:role | anyone:role")
@click.option("--notify/--no-notify", "notify", default=False,
              help="Send notification email on user-type shares (default: no).")
@click.option("--tab", "tab_id", default=None)
@common_output_options
def create(title, source, parent, shares, notify, tab_id,
           force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Create a new Google Doc."""
    if dry_run:
        click.echo(f"would create doc title={title!r} parent={parent} share={list(shares)}")
        return

    try:
        proc = gws_run("docs", "documents", "create",
                       "--json", json.dumps({"title": title}))
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)
    if proc.returncode != 0:
        die(f"gws docs create failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    doc = json.loads(proc.stdout)
    doc_id = doc.get("documentId")

    if parent:
        mv = gws_run("drive", "files", "update",
                     "--params", json.dumps({"fileId": doc_id, "addParents": parent}),
                     "--json", json.dumps({}))
        if mv.returncode != 0 and verbose:
            click.echo(f"move warning: {mv.stderr.strip()}", err=True)

    if shares:
        from click.testing import CliRunner
        from claw.sheet.share import share as share_cmd
        runner = CliRunner()
        for spec in shares:
            parsed = _parse_share(spec)
            if parsed is None:
                click.echo(f"warning: bad --share: {spec}", err=True)
                continue
            argv: list[str] = [doc_id, "--role", parsed["role"]]
            if parsed["type"] == "user":
                argv += ["--user", parsed["emailAddress"]]
            elif parsed["type"] == "domain":
                argv += ["--domain", parsed["domain"]]
            else:
                argv += ["--anyone"]
            argv += ["--notify"] if notify else ["--no-notify"]
            if parsed["role"] == "owner":
                argv += ["--transfer-ownership"]
            result = runner.invoke(share_cmd, argv, standalone_mode=False)
            if result.exit_code != 0:
                click.echo(
                    f"warning: share failed for {spec}: "
                    f"{(result.output or str(result.exception)).strip()}",
                    err=True,
                )

    if source:
        from claw.doc.build import _build_and_dispatch  # late import
        _build_and_dispatch(doc_id, source, tab_id or "t.0",
                            append=False, chunk_size=8, from_index=0,
                            as_json=as_json, quiet=quiet, verbose=verbose)

    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    if as_json:
        emit_json({"doc_id": doc_id, "revision_id": doc.get("revisionId"), "url": url})
    elif not quiet:
        click.echo(f"created {doc_id} → {url}")


def _parse_share(spec: str) -> dict | None:
    parts = spec.split(":")
    if parts[0] == "user" and len(parts) == 3:
        return {"type": "user", "emailAddress": parts[1], "role": parts[2]}
    if parts[0] == "domain" and len(parts) == 3:
        return {"type": "domain", "domain": parts[1], "role": parts[2]}
    if parts[0] == "anyone" and len(parts) == 2:
        return {"type": "anyone", "role": parts[1]}
    return None
