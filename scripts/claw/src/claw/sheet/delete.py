"""claw sheet delete — trash (recoverable) or permanently delete a Drive file."""

from __future__ import annotations

import json
import sys

import click

from claw.common import EXIT_INPUT, EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


@click.command(name="delete")
@click.argument("file_id")
@click.option("--permanent", is_flag=True, help="Permanently delete (skip trash).")
@click.option("--yes", is_flag=True, help="Skip interactive confirmation.")
@common_output_options
def delete(file_id, permanent, yes,
           force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Trash (default) or permanently delete a Drive file."""
    if permanent and not yes:
        if not sys.stdin.isatty():
            die("--permanent without --yes in non-TTY context",
                code=EXIT_INPUT, hint="pass --yes to confirm", as_json=as_json)
        click.confirm(f"Permanently delete {file_id}? This cannot be undone.",
                      abort=True)

    if dry_run:
        action = "permanently delete" if permanent else "trash"
        click.echo(f"would {action} {file_id}")
        return

    try:
        if permanent:
            proc = gws_run("drive", "files", "delete",
                           "--params", json.dumps({"fileId": file_id}))
        else:
            proc = gws_run("drive", "files", "update",
                           "--params", json.dumps({"fileId": file_id,
                                                   "fields": "id,trashed"}),
                           "--json", json.dumps({"trashed": True}))
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    if proc.returncode != 0:
        die(f"gws delete failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    if as_json:
        emit_json({"file_id": file_id, "permanent": bool(permanent),
                   "trashed": not permanent})
    elif not quiet:
        verb = "deleted" if permanent else "trashed"
        click.echo(f"{verb} {file_id}")
