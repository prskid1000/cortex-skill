"""claw drive info — drive.files.get metadata."""

from __future__ import annotations

import json

import click

from claw.common import EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


DEFAULT_FIELDS = (
    "id,name,mimeType,size,createdTime,modifiedTime,"
    "parents,owners(emailAddress,displayName),"
    "webViewLink,trashed,shared,starred"
)


@click.command(name="info")
@click.argument("file_id")
@click.option("--fields", default=DEFAULT_FIELDS,
              help="Comma-separated Drive fields projection (default: common metadata).")
@common_output_options
def info(file_id, fields,
         force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Fetch Drive file metadata (name, mime, size, parents, owners, ...)."""
    params = {"fileId": file_id, "fields": fields}

    if dry_run:
        click.echo(f"would get metadata for {file_id} (fields={fields})")
        return

    try:
        proc = gws_run("drive", "files", "get",
                       "--params", json.dumps(params))
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    if proc.returncode != 0:
        die(f"gws files get failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    data = json.loads(proc.stdout) if proc.stdout.strip() else {}

    if as_json:
        emit_json(data)
        return

    if quiet:
        return

    width = 16
    for key in ("id", "name", "mimeType", "size", "createdTime", "modifiedTime",
                "trashed", "shared", "starred", "webViewLink"):
        if key in data:
            click.echo(f"{key:<{width}} {data[key]}")
    parents = data.get("parents")
    if parents:
        click.echo(f"{'parents':<{width}} {', '.join(parents)}")
    owners = data.get("owners") or []
    for o in owners:
        who = o.get("emailAddress") or o.get("displayName") or "?"
        click.echo(f"{'owner':<{width}} {who}")
