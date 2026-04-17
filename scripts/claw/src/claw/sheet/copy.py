"""claw sheet copy — drive.files.copy."""

from __future__ import annotations

import json

import click

from claw.common import EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


@click.command(name="copy")
@click.argument("file_id")
@click.option("--to", "to_folder", default=None, help="Destination folder id.")
@click.option("--parent", "parent_folder", default=None,
              help="Destination folder id; the copy is created under this parent.")
@click.option("--name", default=None, help="Name for the copy.")
@common_output_options
def copy(file_id, to_folder, parent_folder, name,
         force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Duplicate a Drive file."""
    folder = to_folder or parent_folder
    body: dict = {}
    if name:
        body["name"] = name
    if folder:
        body["parents"] = [folder]

    params = {"fileId": file_id, "fields": "id,name,parents,mimeType,webViewLink"}

    if dry_run:
        click.echo(f"would copy {file_id} → name={name} parent={folder}")
        return

    try:
        proc = gws_run("drive", "files", "copy",
                       "--params", json.dumps(params),
                       "--json", json.dumps(body))
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    if proc.returncode != 0:
        die(f"gws files copy failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    data = json.loads(proc.stdout) if proc.stdout.strip() else {}
    new_id = data.get("id")

    if as_json:
        emit_json({"source_file_id": file_id, "file_id": new_id,
                   "name": data.get("name"), "parents": data.get("parents"),
                   "web_view_link": data.get("webViewLink")})
    elif not quiet:
        click.echo(f"copied {file_id} → {new_id}")
