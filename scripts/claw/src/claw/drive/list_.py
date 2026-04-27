"""claw drive list — drive.files.list with sugar."""

from __future__ import annotations

import json

import click

from claw.common import EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


MIME_SHORTCUTS = {
    "sheet":  "application/vnd.google-apps.spreadsheet",
    "doc":    "application/vnd.google-apps.document",
    "slides": "application/vnd.google-apps.presentation",
    "folder": "application/vnd.google-apps.folder",
    "pdf":    "application/pdf",
}


@click.command(name="list")
@click.option("--parent", default=None, help="Folder ID; expands to `<ID> in parents`.")
@click.option("--query", "raw_query", default=None, help="Raw Drive search string.")
@click.option("--mime", default=None,
              help="MIME filter. Shortcuts: sheet|doc|slides|folder|pdf, or a full MIME.")
@click.option("--name", "name_contains", default=None, help="Expands to `name contains 'X'`.")
@click.option("--max", "max_results", default=100, type=int)
@click.option("--all", "all_pages", is_flag=True, help="Paginate all results (NDJSON).")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
@common_output_options
def list_(parent, raw_query, mime, name_contains, max_results, all_pages, fmt,
          force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """List Drive files."""
    clauses: list[str] = []
    if parent:
        clauses.append(f'"{parent}" in parents')
    if mime:
        target = MIME_SHORTCUTS.get(mime, mime)
        clauses.append(f'mimeType = "{target}"')
    if name_contains:
        clauses.append(f'name contains "{name_contains}"')
    if raw_query:
        clauses.append(raw_query)
    if not clauses:
        clauses.append("trashed = false")

    params: dict = {"q": " and ".join(clauses), "pageSize": max_results,
                    "fields": "nextPageToken,files(id,name,mimeType,modifiedTime,size,webViewLink,parents)"}

    if dry_run:
        click.echo(f"would list with q={params['q']}")
        return

    extra: list[str] = []
    if all_pages:
        extra.append("--page-all")

    try:
        proc = gws_run("drive", "files", "list",
                       "--params", json.dumps(params), *extra)
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    if proc.returncode != 0:
        die(f"gws list failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    files: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        files.extend(data.get("files", []) if isinstance(data, dict) else [])

    if fmt == "json" or as_json:
        for f in files:
            emit_json(f)
        return

    for f in files:
        click.echo(f"{f.get('id', '?'):44} {f.get('mimeType', '?'):50} {f.get('name', '?')}")
