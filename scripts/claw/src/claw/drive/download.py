"""claw drive download — export Google-native or binary files."""

from __future__ import annotations

import json
from pathlib import Path

import click

from claw.common import EXIT_INPUT, EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


EXPORT_MIME = {
    "pdf":  "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv":  "text/csv",
    "tsv":  "text/tab-separated-values",
    "ods":  "application/x-vnd.oasis.opendocument.spreadsheet",
    "html": "text/html",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "md":   "text/markdown",
    "txt":  "text/plain",
    "epub": "application/epub+zip",
    "odt":  "application/vnd.oasis.opendocument.text",
    "rtf":  "application/rtf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "odp":  "application/vnd.oasis.opendocument.presentation",
}


@click.command(name="download")
@click.argument("file_id")
@click.option("--out", required=True, type=click.Path(path_type=Path))
@click.option("--as", "format_", type=click.Choice(list(EXPORT_MIME)), default=None)
@common_output_options
def download(file_id, out, format_,
             force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Download FILE_ID → OUT (binary or exported)."""
    fmt = format_
    if out.exists() and not force:
        die(f"{out} exists (pass --force)", code=EXIT_INPUT, as_json=as_json)
    if mkdir:
        out.parent.mkdir(parents=True, exist_ok=True)

    if dry_run:
        click.echo(f"would download file={file_id} as={fmt} → {out}")
        return

    try:
        meta = gws_run("drive", "files", "get",
                       "--params", json.dumps({"fileId": file_id, "fields": "id,name,mimeType"}))
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)
    if meta.returncode != 0:
        die(f"gws get failed: {meta.stderr.strip()}", code=EXIT_SYSTEM, as_json=as_json)

    info = json.loads(meta.stdout)
    is_native = info.get("mimeType", "").startswith("application/vnd.google-apps.")

    if is_native:
        if not fmt:
            die("Google-native file; --as is required "
                "(e.g. --as xlsx for Sheets, --as pdf, --as md)",
                code=EXIT_INPUT, as_json=as_json)
        proc = gws_run("drive", "files", "export",
                       "--params", json.dumps({"fileId": file_id,
                                               "mimeType": EXPORT_MIME[fmt]}),
                       "--output", str(out))
    else:
        proc = gws_run("drive", "files", "get",
                       "--params", json.dumps({"fileId": file_id, "alt": "media"}),
                       "--output", str(out))

    if proc.returncode != 0:
        die(f"gws download failed: {proc.stderr.strip()}",
            code=EXIT_SYSTEM, as_json=as_json)

    if as_json:
        emit_json({"file_id": file_id, "name": info.get("name"),
                   "path": str(out),
                   "bytes": out.stat().st_size if out.exists() else 0})
    elif not quiet:
        click.echo(f"downloaded {file_id} → {out}")
