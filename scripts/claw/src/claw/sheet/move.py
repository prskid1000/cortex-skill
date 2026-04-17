"""claw sheet move — drive.files.update with addParents / removeParents."""

from __future__ import annotations

import json

import click

from claw.common import EXIT_INPUT, EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


@click.command(name="move")
@click.argument("file_id")
@click.option("--to", "to_folder", required=True, help="Destination folder id.")
@click.option("--from", "from_folder", default=None,
              help="Folder to remove from (default: all current parents).")
@common_output_options
def move(file_id, to_folder, from_folder,
         force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Move a Drive file between folders."""
    remove = from_folder
    if not remove:
        try:
            meta = gws_run("drive", "files", "get",
                           "--params", json.dumps({"fileId": file_id,
                                                   "fields": "id,parents"}))
        except FileNotFoundError as e:
            die(str(e), code=EXIT_SYSTEM, as_json=as_json)
        if meta.returncode != 0:
            die(f"gws files get failed: {meta.stderr.strip()}",
                code=EXIT_SYSTEM, as_json=as_json)
        info = json.loads(meta.stdout)
        parents = info.get("parents", []) or []
        if not parents:
            die(f"file {file_id} has no parents to remove; pass --from FOLDER_ID",
                code=EXIT_INPUT, as_json=as_json)
        remove = ",".join(parents)

    params = {
        "fileId": file_id,
        "addParents": to_folder,
        "removeParents": remove,
        "fields": "id,parents",
    }

    if dry_run:
        click.echo(f"would move {file_id}: +{to_folder} -{remove}")
        return

    try:
        proc = gws_run("drive", "files", "update",
                       "--params", json.dumps(params),
                       "--json", json.dumps({}))
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    if proc.returncode != 0:
        die(f"gws files update failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    data = json.loads(proc.stdout) if proc.stdout.strip() else {}
    if as_json:
        emit_json({"file_id": file_id, "parents": data.get("parents"),
                   "moved_to": to_folder})
    elif not quiet:
        click.echo(f"moved {file_id} → {to_folder}")
