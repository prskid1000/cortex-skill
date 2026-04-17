"""claw pdf attach — embedded file attachments (list / add / extract / remove)."""
from __future__ import annotations

from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, safe_write


@click.group(name="attach")
def attach() -> None:
    """Manage embedded file attachments in a PDF."""


@attach.command(name="list")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
def attach_list(src: Path, as_json: bool) -> None:
    """List embedded attachments in <SRC>."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    doc = fitz.open(str(src))
    try:
        names = doc.embfile_names() if hasattr(doc, "embfile_names") else []
        rows: list[dict] = []
        for name in names:
            info = doc.embfile_info(name) if hasattr(doc, "embfile_info") else {}
            rows.append({
                "name": name,
                "filename": info.get("filename", name),
                "description": info.get("desc", ""),
                "size": info.get("size", 0),
            })
    finally:
        doc.close()

    if as_json:
        emit_json(rows)
        return
    for r in rows:
        click.echo(f"{r['name']:30s} {r['size']:>10}  {r['description']}")
    click.echo(f"── {len(rows)} attachment(s)")


@attach.command(name="add")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--file", "attach_path", required=True,
              type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--name", default=None, help="Attachment name (default: filename).")
@click.option("--description", default="")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True)
@common_output_options
def attach_add(src: Path, attach_path: Path, name: str | None, description: str,
               out: Path | None, in_place: bool,
               force: bool, backup: bool, as_json: bool, dry_run: bool,
               quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Embed --file into <SRC>."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    if not (out or in_place):
        die("pass --out FILE or --in-place", code=2)
    target = src if in_place else out
    assert target is not None

    attach_name = name or attach_path.name
    doc = fitz.open(str(src))
    try:
        payload = attach_path.read_bytes()
        doc.embfile_add(attach_name, payload, filename=attach_path.name,
                        desc=description)
        if dry_run:
            click.echo(f"would embed {attach_path.name} as {attach_name!r} → {target}")
            return
        data = doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()

    safe_write(target, lambda f: f.write(data),
               force=force or in_place, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(target), "name": attach_name,
                   "size": len(payload)})
    elif not quiet:
        click.echo(f"attached {attach_name!r} → {target}")


@attach.command(name="extract")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--name", required=True, help="Attachment name to extract.")
@click.option("-o", "--out", required=True, type=click.Path(path_type=Path))
@click.option("--force", is_flag=True)
@click.option("--mkdir", is_flag=True)
@click.option("--json", "as_json", is_flag=True)
def attach_extract(src: Path, name: str, out: Path, force: bool, mkdir: bool,
                   as_json: bool) -> None:
    """Extract an attachment to --out."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    doc = fitz.open(str(src))
    try:
        try:
            data = doc.embfile_get(name)
        except Exception:
            die(f"attachment not found: {name!r}", code=2)
    finally:
        doc.close()

    safe_write(out, lambda f: f.write(data), force=force, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(out), "name": name, "bytes": len(data)})
    else:
        click.echo(f"extracted {name!r} → {out} ({len(data)} bytes)")


@attach.command(name="remove")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--name", required=True)
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True)
@common_output_options
def attach_remove(src: Path, name: str,
                  out: Path | None, in_place: bool,
                  force: bool, backup: bool, as_json: bool, dry_run: bool,
                  quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Remove an embedded attachment."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    if not (out or in_place):
        die("pass --out FILE or --in-place", code=2)
    target = src if in_place else out
    assert target is not None

    doc = fitz.open(str(src))
    try:
        try:
            doc.embfile_del(name)
        except Exception:
            die(f"attachment not found: {name!r}", code=2)
        if dry_run:
            click.echo(f"would remove attachment {name!r} → {target}")
            return
        data = doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()

    safe_write(target, lambda f: f.write(data),
               force=force or in_place, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(target), "removed": name})
    elif not quiet:
        click.echo(f"removed {name!r} → {target}")
