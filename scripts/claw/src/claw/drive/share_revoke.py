"""claw drive share-revoke — drive.permissions.delete."""

from __future__ import annotations

import json

import click

from claw.common import EXIT_INPUT, EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


def _resolve_pid_by_user(file_id: str, user: str, as_json: bool) -> str:
    params = {
        "fileId": file_id,
        "fields": "permissions(id,type,emailAddress)",
    }
    proc = gws_run("drive", "permissions", "list",
                   "--params", json.dumps(params))
    if proc.returncode != 0:
        die(f"gws permissions list failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        for p in data.get("permissions", []) or []:
            if p.get("emailAddress", "").lower() == user.lower():
                return p.get("id") or ""

    die(f"no permission matching user {user!r} on {file_id}",
        code=EXIT_INPUT, as_json=as_json)
    return ""


@click.command(name="share-revoke")
@click.argument("file_id")
@click.option("--permission-id", "permission_id", default=None,
              help="Permission id (from `share-list`).")
@click.option("--user", default=None, help="Resolve email → permission id, then revoke.")
@common_output_options
def share_revoke(file_id, permission_id, user,
                 force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Revoke a Drive permission."""
    if bool(permission_id) == bool(user):
        die("exactly one of --permission-id or --user required",
            code=EXIT_INPUT, as_json=as_json)

    pid = permission_id
    if user:
        if dry_run:
            click.echo(f"would resolve {user} → permission id on {file_id} and revoke")
            return
        pid = _resolve_pid_by_user(file_id, user, as_json)

    if dry_run:
        click.echo(f"would revoke permission {pid} from {file_id}")
        return

    try:
        proc = gws_run("drive", "permissions", "delete",
                       "--params", json.dumps({"fileId": file_id,
                                               "permissionId": pid}))
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    if proc.returncode != 0:
        die(f"gws permissions delete failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    if as_json:
        emit_json({"file_id": file_id, "permission_id": pid, "revoked": True})
    elif not quiet:
        click.echo(f"revoked {pid} from {file_id}")
