"""claw docx diff — surface tracked w:ins / w:del revisions."""

from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path

import click

from claw.common import EXIT_INPUT, die, emit_json


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


@click.command(name="diff")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--author", default=None)
@click.option("--since", default=None, help="ISO date YYYY-MM-DD.")
@click.option("--json", "as_json", is_flag=True)
def diff(src: Path, author: str | None, since: str | None, as_json: bool) -> None:
    """Emit a list of tracked insertions and deletions."""
    try:
        from lxml import etree
    except ImportError:
        die("lxml not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[docx]'", as_json=as_json)

    with zipfile.ZipFile(src) as zf:
        try:
            doc_xml = zf.read("word/document.xml")
        except KeyError:
            die("word/document.xml missing", code=EXIT_INPUT, as_json=as_json)

    root = etree.fromstring(doc_xml)

    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError:
            die(f"invalid --since: {since!r}", code=EXIT_INPUT, as_json=as_json)

    results = []
    for kind in ("ins", "del"):
        for el in root.findall(f".//{{{W_NS}}}{kind}"):
            auth = el.get(f"{{{W_NS}}}author")
            ts = el.get(f"{{{W_NS}}}date")
            text_tag = "delText" if kind == "del" else "t"
            texts = [t.text for t in el.iter(f"{{{W_NS}}}{text_tag}") if t.text]
            if author and auth != author:
                continue
            if since_dt and ts:
                try:
                    rev_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if rev_dt.replace(tzinfo=None) < since_dt:
                        continue
                except ValueError:
                    pass
            results.append({
                "kind": "insertion" if kind == "ins" else "deletion",
                "author": auth,
                "timestamp": ts,
                "text": "".join(texts),
            })

    if as_json:
        emit_json(results)
    else:
        for r in results:
            marker = "+" if r["kind"] == "insertion" else "-"
            click.echo(f"{marker} [{r['author']} @ {r['timestamp']}] {r['text']}")
