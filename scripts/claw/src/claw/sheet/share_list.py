"""claw sheet share-list — drive.permissions.list."""

from __future__ import annotations

import json

import click

from claw.common import EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


@click.command(name="share-list")
@click.argument("file_id")
@common_output_options
def share_list(file_id,
               force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """List current Drive permissions on a file."""
    params = {
        "fileId": file_id,
        "fields": "permissions(id,type,role,emailAddress,domain,displayName,deleted)",
    }

    if dry_run:
        click.echo(f"would list permissions on {file_id}")
        return

    try:
        proc = gws_run("drive", "permissions", "list",
                       "--params", json.dumps(params))
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    if proc.returncode != 0:
        die(f"gws permissions list failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    perms: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            perms.extend(data.get("permissions", []) or [])

    if as_json:
        for p in perms:
            emit_json({
                "permission_id": p.get("id"),
                "type": p.get("type"),
                "role": p.get("role"),
                "email": p.get("emailAddress"),
                "domain": p.get("domain"),
                "display_name": p.get("displayName"),
            })
        return

    for p in perms:
        who = p.get("emailAddress") or p.get("domain") or p.get("type", "?")
        click.echo(f"{p.get('id', '?'):24} {p.get('role', '?'):10} "
                   f"{p.get('type', '?'):8} {who}")
