"""claw docx comments dump — extract review comments from the docx comments part."""

from __future__ import annotations

import zipfile
from pathlib import Path

import click

from claw.common import EXIT_INPUT, die, emit_json


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


@click.group(name="comments")
def comments() -> None:
    """Comment-review operations."""


@comments.command(name="dump")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--author", default=None, help="Filter by author.")
@click.option("--json", "as_json", is_flag=True)
def comments_dump(src: Path, author: str | None, as_json: bool) -> None:
    """Emit each comment as {author, text, range_text, timestamp}."""
    try:
        from lxml import etree
    except ImportError:
        die("lxml not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[docx]'", as_json=as_json)

    with zipfile.ZipFile(src) as zf:
        try:
            comments_xml = zf.read("word/comments.xml")
        except KeyError:
            if as_json:
                emit_json([])
            else:
                click.echo("(no comments)")
            return
        try:
            doc_xml = zf.read("word/document.xml")
        except KeyError:
            doc_xml = b""

    nsmap = {"w": W_NS}
    c_root = etree.fromstring(comments_xml)

    range_texts: dict[str, str] = {}
    if doc_xml:
        d_root = etree.fromstring(doc_xml)
        starts = d_root.findall(f".//{{{W_NS}}}commentRangeStart")
        for start in starts:
            cid = start.get(f"{{{W_NS}}}id")
            buf: list[str] = []
            cur = start
            while True:
                cur = cur.getnext()
                if cur is None:
                    break
                if cur.tag == f"{{{W_NS}}}commentRangeEnd" and cur.get(f"{{{W_NS}}}id") == cid:
                    break
                for t in cur.iter(f"{{{W_NS}}}t"):
                    if t.text:
                        buf.append(t.text)
            range_texts[cid] = "".join(buf).strip()

    results = []
    for c in c_root.findall(f"{{{W_NS}}}comment"):
        cid = c.get(f"{{{W_NS}}}id")
        auth = c.get(f"{{{W_NS}}}author")
        ts = c.get(f"{{{W_NS}}}date")
        texts = [t.text for t in c.iter(f"{{{W_NS}}}t") if t.text]
        if author and auth != author:
            continue
        results.append({
            "id": cid,
            "author": auth,
            "timestamp": ts,
            "text": "".join(texts).strip(),
            "range_text": range_texts.get(cid, ""),
        })

    if as_json:
        emit_json(results)
    else:
        for r in results:
            click.echo(f"[{r['author']} @ {r['timestamp']}] {r['text']}")
            if r["range_text"]:
                click.echo(f"  on: {r['range_text']}")
