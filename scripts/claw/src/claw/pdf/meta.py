"""claw pdf meta — get / set core PDF metadata."""
from __future__ import annotations

from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, safe_write


META_FIELDS = ("title", "author", "subject", "keywords", "creator", "producer")


@click.group(name="meta")
def meta() -> None:
    """Read / write PDF core metadata."""


@meta.command(name="get")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
def meta_get(src: Path, as_json: bool) -> None:
    """Print core metadata of <SRC>."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    doc = fitz.open(str(src))
    try:
        m = dict(doc.metadata or {})
    finally:
        doc.close()

    payload = {
        "title": m.get("title", ""),
        "author": m.get("author", ""),
        "subject": m.get("subject", ""),
        "keywords": m.get("keywords", ""),
        "creator": m.get("creator", ""),
        "producer": m.get("producer", ""),
        "creation_date": m.get("creationDate", ""),
        "mod_date": m.get("modDate", ""),
    }
    if as_json:
        emit_json(payload)
        return
    for k, v in payload.items():
        click.echo(f"{k:15s} {v}")


@meta.command(name="set")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--title", default=None)
@click.option("--author", default=None)
@click.option("--subject", default=None)
@click.option("--keywords", default=None, help="Comma-separated.")
@click.option("--creator", default=None)
@click.option("--producer", default=None)
@click.option("--creation-date", "creation_date", default=None,
              help="YYYY-MM-DD.")
@click.option("--mod-date", "mod_date", default=None, help="YYYY-MM-DD.")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True)
@click.option("--journal", "journal_name", default=None,
              help="Name of an open journal session; emits journal records alongside "
                   "the metadata update. TODO: ambiguous — implemented as read-emit "
                   "(log-only; does not mutate the staged PDF).")
@common_output_options
def meta_set(src: Path, title: str | None, author: str | None, subject: str | None,
             keywords: str | None, creator: str | None, producer: str | None,
             creation_date: str | None, mod_date: str | None,
             out: Path | None, in_place: bool, journal_name: str | None,
             force: bool, backup: bool, as_json: bool, dry_run: bool,
             quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Set core metadata on <SRC>."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    if not (out or in_place):
        die("pass --out FILE or --in-place", code=2)
    target = src if in_place else out
    assert target is not None

    def _pdf_date(s: str) -> str:
        return "D:" + s.replace("-", "") + "000000Z"

    updates = {}
    if title is not None:        updates["title"] = title
    if author is not None:       updates["author"] = author
    if subject is not None:      updates["subject"] = subject
    if keywords is not None:     updates["keywords"] = keywords
    if creator is not None:      updates["creator"] = creator
    if producer is not None:     updates["producer"] = producer
    if creation_date is not None: updates["creationDate"] = _pdf_date(creation_date)
    if mod_date is not None:     updates["modDate"] = _pdf_date(mod_date)

    if not updates:
        die("pass at least one metadata flag", code=2)

    doc = fitz.open(str(src))
    try:
        current = dict(doc.metadata or {})
        current.update(updates)
        doc.set_metadata(current)
        if dry_run:
            click.echo(f"would set {list(updates.keys())} → {target}")
            return
        data = doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()

    safe_write(target, lambda f: f.write(data),
               force=force or in_place, backup=backup, mkdir=mkdir)
    if journal_name:
        from claw.pdf.journal import append_entry as _journal_append
        _journal_append(journal_name, {
            "verb": "meta set", "src": str(src), "out": str(target),
            "updated": list(updates.keys()),
            "summary": f"set {', '.join(updates.keys())}",
        })
    if as_json:
        emit_json({"out": str(target), "updated": list(updates.keys())})
    elif not quiet:
        click.echo(f"updated {', '.join(updates.keys())} → {target}")
