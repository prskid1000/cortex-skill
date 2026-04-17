"""claw pdf journal — start / commit / rollback edit-journal sessions."""
from __future__ import annotations

import json
from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, safe_write  # noqa: F401


def _journal_dir() -> Path:
    base = Path.home() / ".claw" / "pdf-journal"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _session_path(name: str) -> Path:
    return _journal_dir() / f"{name}.json"


def _log_path(name: str) -> Path:
    return _journal_dir() / f"{name}.log.jsonl"


def append_entry(name: str, entry: dict) -> None:
    """Append one JSON record describing a mutating op to <name>.log.jsonl.

    Read-emit semantics — does not mutate the staged PDF. Reader verbs can
    pass a description here so `journal status` has something to show.
    """
    import datetime as _dt
    record = dict(entry)
    record.setdefault("ts", _dt.datetime.now(_dt.timezone.utc).isoformat())
    with _log_path(name).open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


@click.group(name="journal")
def journal() -> None:
    """Stage edits in a sidecar; commit or rollback atomically."""


@journal.command(name="start")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--name", required=True)
@click.option("--force", is_flag=True)
def journal_start(src: Path, name: str, force: bool) -> None:
    """Open a journal session against <SRC>."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    sp = _session_path(name)
    if sp.exists() and not force:
        die(f"journal {name!r} already exists (pass --force)", code=2)

    doc = fitz.open(str(src))
    try:
        try:
            doc.journal_enable()
        except Exception as e:
            die(f"journal_enable failed: {e}", code=1)
        staged_path = sp.with_suffix(".pdf")
        doc.save(str(staged_path), deflate=True, garbage=4)
    finally:
        doc.close()

    sp.write_text(json.dumps({
        "name": name,
        "source": str(src),
        "staged": str(staged_path),
    }, indent=2), encoding="utf-8")
    click.echo(f"journal {name!r} started (source={src})")


@journal.command(name="commit")
@click.option("--name", required=True)
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True)
@common_output_options
def journal_commit(name: str, out: Path | None, in_place: bool,
                   force: bool, backup: bool, as_json: bool, dry_run: bool,
                   quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Commit staged journal changes to disk."""
    sp = _session_path(name)
    if not sp.exists():
        die(f"no journal session: {name!r}", code=2)
    meta_payload = json.loads(sp.read_text(encoding="utf-8"))
    staged = Path(meta_payload["staged"])
    source = Path(meta_payload["source"])
    if not staged.exists():
        die(f"staged snapshot missing: {staged}", code=1)

    if not (out or in_place):
        die("pass --out FILE or --in-place", code=2)
    target = source if in_place else out
    assert target is not None

    data = staged.read_bytes()
    if dry_run:
        click.echo(f"would commit journal {name!r} ({len(data)} bytes) → {target}")
        return

    safe_write(target, lambda f: f.write(data),
               force=force or in_place, backup=backup, mkdir=mkdir)
    try:
        staged.unlink()
    except OSError:
        pass
    sp.unlink()

    if as_json:
        emit_json({"out": str(target), "committed": name})
    elif not quiet:
        click.echo(f"committed journal {name!r} → {target}")


@journal.command(name="rollback")
@click.option("--name", required=True)
def journal_rollback(name: str) -> None:
    """Discard a journal session."""
    sp = _session_path(name)
    if not sp.exists():
        die(f"no journal session: {name!r}", code=2)
    meta_payload = json.loads(sp.read_text(encoding="utf-8"))
    staged = Path(meta_payload["staged"])
    try:
        if staged.exists():
            staged.unlink()
    except OSError:
        pass
    try:
        _log_path(name).unlink()
    except OSError:
        pass
    sp.unlink()
    click.echo(f"rolled back journal {name!r}")


@journal.command(name="status")
@click.option("--name", required=True)
@click.option("--json", "as_json", is_flag=True)
def journal_status(name: str, as_json: bool) -> None:
    """Show session metadata and logged mutating ops."""
    sp = _session_path(name)
    if not sp.exists():
        die(f"no journal session: {name!r}", code=2)
    meta_payload = json.loads(sp.read_text(encoding="utf-8"))
    entries: list[dict] = []
    lp = _log_path(name)
    if lp.exists():
        for line in lp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    payload = {
        "name": name,
        "source": meta_payload.get("source"),
        "staged": meta_payload.get("staged"),
        "entries": entries,
    }
    if as_json:
        emit_json(payload)
        return
    click.echo(f"journal: {name}")
    click.echo(f"source:  {payload['source']}")
    click.echo(f"staged:  {payload['staged']}")
    click.echo(f"entries: {len(entries)}")
    for i, e in enumerate(entries, start=1):
        click.echo(f"  {i:>3}. {e.get('verb','?')} {e.get('summary','')}")
