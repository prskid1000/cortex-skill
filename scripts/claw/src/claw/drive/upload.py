"""claw drive upload — upload to Drive, optionally convert to Google-native."""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path

import click

from claw.common import EXIT_INPUT, EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


UPLOAD_MIME = {
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".csv":  "text/csv",
    ".tsv":  "text/tab-separated-values",
    ".pdf":  "application/pdf",
}

NATIVE_TARGET = {
    ".xlsx": "application/vnd.google-apps.spreadsheet",
    ".csv":  "application/vnd.google-apps.spreadsheet",
    ".tsv":  "application/vnd.google-apps.spreadsheet",
    ".docx": "application/vnd.google-apps.document",
    ".pptx": "application/vnd.google-apps.presentation",
}


@click.command(name="upload")
@click.option("--from", "source", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--name", default=None, help="Target Drive name; defaults to file basename.")
@click.option("--parent", multiple=True, help="Parent folder ID(s).")
@click.option("--convert/--no-convert", default=None,
              help="Force conversion on/off. Default: smart (native for .xlsx/.csv/.docx/.pptx).")
@click.option("--mime", default=None, help="Override upload MIME type.")
@click.option("--description", default=None)
@common_output_options
def upload(source, name, parent, convert, mime, description,
           force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Upload a local file to Drive."""
    ext = source.suffix.lower()
    upload_mime = mime or UPLOAD_MIME.get(ext) or mimetypes.guess_type(str(source))[0] or "application/octet-stream"

    if convert is None:
        convert_flag = ext in NATIVE_TARGET
    else:
        convert_flag = convert

    body: dict = {"name": name or source.name}
    if parent:
        body["parents"] = list(parent)
    if description:
        body["description"] = description
    if convert_flag and ext in NATIVE_TARGET:
        body["mimeType"] = NATIVE_TARGET[ext]

    if dry_run:
        click.echo(f"would upload {source} → name={body['name']} "
                   f"mime-in={upload_mime} target={body.get('mimeType', 'unchanged')}")
        return

    try:
        proc = gws_run("drive", "files", "create",
                       "--json", json.dumps(body),
                       "--upload", str(source),
                       "--upload-content-type", upload_mime)
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)

    if proc.returncode != 0:
        die(f"gws upload failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    data = json.loads(proc.stdout)
    file_id = data.get("id")

    link_proc = gws_run("drive", "files", "get",
                        "--params", json.dumps({"fileId": file_id,
                                                "fields": "id,name,mimeType,webViewLink"}))
    link = {}
    if link_proc.returncode == 0:
        link = json.loads(link_proc.stdout)

    if as_json:
        emit_json({"file_id": file_id, "name": data.get("name"),
                   "mime_type": link.get("mimeType", data.get("mimeType")),
                   "web_view_link": link.get("webViewLink")})
    elif not quiet:
        click.echo(f"uploaded {file_id} ({link.get('mimeType', data.get('mimeType', '?'))})")
