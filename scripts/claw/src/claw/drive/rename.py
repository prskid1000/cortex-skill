"""claw drive rename — drive.files.update with a new name."""

from __future__ import annotations

import json

import click

from claw.common import EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


@click.command(name="rename")
@click.argument("file_id")
@click.option("--name", required=True, help="New name.")
@common_output_options
def rename(file_id, name,
           force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Rename a Drive file."""
    params = {"fileId": file_id, "fields": "id,name"}
    body = {"name": name}

    if dry_run:
        click.echo(f"would rename {file_id} → {name!r}")
        return

    try:
        proc = gws_run("drive", "files", "update",
                       "--params", json.dumps(params),
                       "--json", json.dumps(body))
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    if proc.returncode != 0:
        die(f"gws files update failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    data = json.loads(proc.stdout) if proc.stdout.strip() else {}
    if as_json:
        emit_json({"file_id": file_id, "name": data.get("name", name)})
    elif not quiet:
        click.echo(f"renamed {file_id} → {name}")
