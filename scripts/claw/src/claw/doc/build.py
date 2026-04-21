"""claw doc build — markdown → docs.batchUpdate (chunked)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import click

from claw.common import EXIT_PARTIAL, EXIT_SYSTEM, common_output_options, die, emit_json, gws_run


HEADING_MAP = {
    1: "TITLE",
    2: "HEADING_1",
    3: "HEADING_2",
    4: "HEADING_3",
    5: "HEADING_4",
    6: "HEADING_5",
}


def _tokenize_inline(text: str) -> list[tuple[str, dict]]:
    """Split a paragraph into (plain, style_dict) runs.

    Minimal inline-markdown tokenizer: `**bold**`, `*italic*`, `` `code` ``, `[t](u)`.
    """
    out: list[tuple[str, dict]] = []
    i = 0
    n = len(text)
    buf = ""

    def flush(style: dict | None = None) -> None:
        nonlocal buf
        if buf:
            out.append((buf, style or {}))
            buf = ""

    while i < n:
        c = text[i]
        if c == "`":
            end = text.find("`", i + 1)
            if end > i:
                flush()
                out.append((text[i + 1:end], {"code": True}))
                i = end + 1
                continue
        if text.startswith("**", i):
            end = text.find("**", i + 2)
            if end > i:
                flush()
                out.append((text[i + 2:end], {"bold": True}))
                i = end + 2
                continue
        if c == "*" and not text.startswith("**", i):
            end = text.find("*", i + 1)
            if end > i:
                flush()
                out.append((text[i + 1:end], {"italic": True}))
                i = end + 1
                continue
        if c == "[":
            m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", text[i:])
            if m:
                flush()
                out.append((m.group(1), {"link": m.group(2)}))
                i += m.end()
                continue
        buf += c
        i += 1
    flush()
    return out


def _blocks_from_md(md: str) -> list[dict]:
    """Parse markdown into a flat list of block descriptors."""
    lines = md.splitlines()
    blocks: list[dict] = []
    para: list[str] = []

    def flush_para() -> None:
        if para:
            text = " ".join(para).strip()
            if text:
                blocks.append({"kind": "para", "text": text})
            para.clear()

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush_para()
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush_para()
            blocks.append({"kind": "heading", "level": len(m.group(1)), "text": m.group(2)})
            continue
        if line.startswith(">"):
            flush_para()
            blocks.append({"kind": "quote", "text": line[1:].lstrip()})
            continue
        m = re.match(r"^\s*[-*+]\s+(.*)$", line)
        if m:
            flush_para()
            blocks.append({"kind": "bullet", "text": m.group(1), "ordered": False})
            continue
        m = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if m:
            flush_para()
            blocks.append({"kind": "bullet", "text": m.group(1), "ordered": True})
            continue
        para.append(line)
    flush_para()
    return blocks


def _style_fields(style: dict) -> tuple[dict, str]:
    """Convert a style dict → (textStyle payload, comma-joined fields mask)."""
    ts: dict = {}
    fields: list[str] = []
    if style.get("bold"):
        ts["bold"] = True
        fields.append("bold")
    if style.get("italic"):
        ts["italic"] = True
        fields.append("italic")
    if style.get("code"):
        ts["weightedFontFamily"] = {"fontFamily": "Consolas"}
        fields.append("weightedFontFamily")
    if "link" in style:
        ts["link"] = {"url": style["link"]}
        fields.append("link")
    return ts, ",".join(fields)


def _requests_for_blocks(blocks: list[dict], tab_id: str, start_index: int) -> tuple[list[dict], int]:
    """Flatten blocks → batchUpdate requests. Returns (requests, end_index)."""
    reqs: list[dict] = []
    idx = start_index

    for b in blocks:
        block_start = idx
        if b["kind"] == "heading":
            text = b["text"] + "\n"
            reqs.append({"insertText": {"location": {"index": idx, "tabId": tab_id}, "text": text}})
            reqs.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": idx, "endIndex": idx + len(text), "tabId": tab_id},
                    "paragraphStyle": {"namedStyleType": HEADING_MAP[b["level"]]},
                    "fields": "namedStyleType",
                }
            })
            idx += len(text)
        elif b["kind"] == "quote":
            runs = _tokenize_inline(b["text"])
            for run_text, _ in runs:
                reqs.append({"insertText": {"location": {"index": idx, "tabId": tab_id}, "text": run_text}})
                idx += len(run_text)
            nl = "\n"
            reqs.append({"insertText": {"location": {"index": idx, "tabId": tab_id}, "text": nl}})
            idx += 1
            reqs.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": block_start, "endIndex": idx, "tabId": tab_id},
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT",
                                       "indentStart": {"magnitude": 36, "unit": "PT"}},
                    "fields": "namedStyleType,indentStart",
                }
            })
            reqs.append({
                "updateTextStyle": {
                    "range": {"startIndex": block_start, "endIndex": idx, "tabId": tab_id},
                    "textStyle": {"italic": True}, "fields": "italic",
                }
            })
        elif b["kind"] == "bullet":
            runs = _tokenize_inline(b["text"])
            for run_text, style in runs:
                run_start = idx
                reqs.append({"insertText": {"location": {"index": idx, "tabId": tab_id}, "text": run_text}})
                idx += len(run_text)
                ts, fields = _style_fields(style)
                if ts:
                    reqs.append({
                        "updateTextStyle": {
                            "range": {"startIndex": run_start, "endIndex": idx, "tabId": tab_id},
                            "textStyle": ts, "fields": fields,
                        }
                    })
            reqs.append({"insertText": {"location": {"index": idx, "tabId": tab_id}, "text": "\n"}})
            idx += 1
            preset = ("NUMBERED_DECIMAL_ALPHA_ROMAN" if b["ordered"]
                      else "BULLET_DISC_CIRCLE_SQUARE")
            reqs.append({
                "createParagraphBullets": {
                    "range": {"startIndex": block_start, "endIndex": idx, "tabId": tab_id},
                    "bulletPreset": preset,
                }
            })
        else:  # para
            runs = _tokenize_inline(b["text"])
            for run_text, style in runs:
                run_start = idx
                reqs.append({"insertText": {"location": {"index": idx, "tabId": tab_id}, "text": run_text}})
                idx += len(run_text)
                ts, fields = _style_fields(style)
                if ts:
                    reqs.append({
                        "updateTextStyle": {
                            "range": {"startIndex": run_start, "endIndex": idx, "tabId": tab_id},
                            "textStyle": ts, "fields": fields,
                        }
                    })
            reqs.append({"insertText": {"location": {"index": idx, "tabId": tab_id}, "text": "\n"}})
            idx += 1
    return reqs, idx


def _dispatch(doc_id: str, requests: list[dict], chunk_size: int,
              from_index: int, *, verbose: bool) -> int:
    """Send requests in chunks. Returns last successfully-sent chunk index."""
    last_ok = from_index - 1
    i = from_index
    while i < len(requests):
        chunk = requests[i:i + chunk_size]
        body = json.dumps({"requests": chunk}, ensure_ascii=False)
        proc = gws_run("docs", "documents", "batchUpdate",
                       "--params", json.dumps({"documentId": doc_id}),
                       "--json", body, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"chunk starting at index {i} failed: {proc.stderr.strip()}")
        last_ok = i
        if verbose:
            click.echo(f"chunk {i}..{i + len(chunk) - 1} ok", err=True)
        i += chunk_size
        time.sleep(0.5)
    return last_ok


def _collect_embedded_objects(body: dict) -> list[dict]:
    """Walk body.content — collect tables, positioned objects, and inline objects.

    Returns descriptors of shape `{kind, startIndex, endIndex, ...id-field}` so the caller
    can sort them reverse-by-startIndex and issue deletes without invalidating indices.
    """
    found: list[dict] = []
    for elt in body.get("content", []) or []:
        if "table" in elt:
            found.append({
                "kind": "table",
                "startIndex": elt.get("startIndex", 0),
                "endIndex": elt.get("endIndex", 0),
            })
        if "paragraph" in elt:
            for piece in elt["paragraph"].get("elements", []) or []:
                if "inlineObjectElement" in piece:
                    found.append({
                        "kind": "inlineObject",
                        "startIndex": piece.get("startIndex", 0),
                        "endIndex": piece.get("endIndex", 0),
                        "objectId": piece["inlineObjectElement"].get("inlineObjectId"),
                    })
    return found


def _positioned_object_ids(doc: dict) -> list[str]:
    return list((doc.get("positionedObjects") or {}).keys())


def _build_and_dispatch(doc_id: str, source: str, tab_id: str, *,
                        append: bool, chunk_size: int, from_index: int,
                        as_json: bool, quiet: bool, verbose: bool,
                        force_clear: bool = False) -> None:
    md = Path(source).read_text(encoding="utf-8")
    blocks = _blocks_from_md(md)
    start_index = 1
    if append:
        get = gws_run("docs", "documents", "get",
                      "--params", json.dumps({"documentId": doc_id, "includeTabsContent": True}))
        if get.returncode == 0:
            data = json.loads(get.stdout)
            body = _find_tab_body(data, tab_id)
            if body:
                start_index = max(_max_end_index(body) - 1, 1)
    else:
        get = gws_run("docs", "documents", "get",
                      "--params", json.dumps({"documentId": doc_id, "includeTabsContent": True}))
        if get.returncode == 0:
            data = json.loads(get.stdout)
            body = _find_tab_body(data, tab_id)
            if body:
                objects = _collect_embedded_objects(body)
                pos_ids = _positioned_object_ids(data)
                if objects or pos_ids:
                    if not force_clear:
                        summary = ", ".join(
                            f"{o['kind']}@[{o['startIndex']},{o['endIndex']})"
                            for o in objects
                        )
                        if pos_ids:
                            summary = (summary + "; " if summary else "") + \
                                      f"positionedObjects=[{','.join(pos_ids)}]"
                        click.echo(
                            f"warning: doc has embedded objects ({summary}); "
                            f"skipping clear and appending at end. "
                            f"pass --force-clear to remove them.",
                            err=True,
                        )
                        start_index = max(_max_end_index(body) - 1, 1)
                        requests, _ = _requests_for_blocks(blocks, tab_id, start_index)
                        try:
                            last_ok = _dispatch(doc_id, requests, chunk_size,
                                                from_index, verbose=verbose)
                        except RuntimeError as e:
                            if as_json:
                                emit_json({"doc_id": doc_id, "error": str(e)})
                            die(str(e), code=EXIT_PARTIAL, as_json=as_json)
                            return
                        if as_json:
                            emit_json({"doc_id": doc_id,
                                       "chunks": (len(requests) + chunk_size - 1) // chunk_size,
                                       "last_index": last_ok,
                                       "total_requests": len(requests),
                                       "skipped_clear": True})
                        elif not quiet:
                            click.echo(f"applied {len(requests)} requests to {doc_id}")
                        return

                    pre: list[dict] = []
                    for obj in sorted(objects, key=lambda o: o["startIndex"], reverse=True):
                        if obj["kind"] == "table":
                            pre.append({"deleteTable": {
                                "tableStartLocation": {
                                    "index": obj["startIndex"], "tabId": tab_id,
                                },
                            }})
                        elif obj["kind"] == "inlineObject":
                            pre.append({"deleteContentRange": {
                                "range": {
                                    "startIndex": obj["startIndex"],
                                    "endIndex": obj["endIndex"],
                                    "tabId": tab_id,
                                },
                            }})
                    for pid in pos_ids:
                        pre.append({"deletePositionedObject": {
                            "objectId": pid, "tabId": tab_id,
                        }})
                    if pre:
                        drop = gws_run("docs", "documents", "batchUpdate",
                                       "--params", json.dumps({"documentId": doc_id}),
                                       "--json", json.dumps({"requests": pre}))
                        if drop.returncode != 0 and verbose:
                            click.echo(f"object-clear warning: {drop.stderr.strip()}",
                                       err=True)
                        re_get = gws_run(
                            "docs", "documents", "get",
                            "--params", json.dumps(
                                {"documentId": doc_id, "includeTabsContent": True}
                            ),
                        )
                        if re_get.returncode == 0:
                            body = _find_tab_body(json.loads(re_get.stdout), tab_id) or body

                end = _max_end_index(body)
                if end > 2:
                    pre = [{"deleteContentRange": {
                        "range": {"startIndex": 1, "endIndex": end - 1, "tabId": tab_id},
                    }}]
                    drop = gws_run("docs", "documents", "batchUpdate",
                                   "--params", json.dumps({"documentId": doc_id}),
                                   "--json", json.dumps({"requests": pre}))
                    if drop.returncode != 0 and verbose:
                        click.echo(f"clear warning: {drop.stderr.strip()}", err=True)

    requests, _ = _requests_for_blocks(blocks, tab_id, start_index)
    try:
        last_ok = _dispatch(doc_id, requests, chunk_size, from_index, verbose=verbose)
    except RuntimeError as e:
        if as_json:
            emit_json({"doc_id": doc_id, "error": str(e)})
        die(str(e), code=EXIT_PARTIAL, as_json=as_json)
        return

    if as_json:
        emit_json({"doc_id": doc_id, "chunks": (len(requests) + chunk_size - 1) // chunk_size,
                   "last_index": last_ok, "total_requests": len(requests)})
    elif not quiet:
        click.echo(f"applied {len(requests)} requests to {doc_id}")


def _find_tab_body(doc: dict, tab_id: str) -> dict | None:
    for tab in doc.get("tabs", []) or []:
        props = tab.get("tabProperties", {})
        if props.get("tabId") == tab_id:
            return tab.get("documentTab", {}).get("body", {})
    return doc.get("body") or None


def _max_end_index(body: dict) -> int:
    elts = body.get("content", [])
    if not elts:
        return 1
    return max((e.get("endIndex", 1) for e in elts), default=1)


@click.command(name="build")
@click.argument("doc_id")
@click.option("--from", "source", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--tab", "tab_id", default="t.0")
@click.option("--append", is_flag=True)
@click.option("--replace-all", is_flag=True)
@click.option("--force-clear", is_flag=True,
              help="Delete embedded tables / inline / positioned objects before clearing text.")
@click.option("--chunk-size", default=4, type=int)
@click.option("--from-index", default=0, type=int)
@common_output_options
def build(doc_id, source, tab_id, append, replace_all, force_clear,
          chunk_size, from_index,
          force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Apply a markdown file to an existing Doc."""
    if dry_run:
        md = Path(source).read_text(encoding="utf-8")
        blocks = _blocks_from_md(md)
        requests, _ = _requests_for_blocks(blocks, tab_id, 1)
        click.echo(f"would send {len(requests)} requests in "
                   f"{(len(requests) + chunk_size - 1) // chunk_size} chunks")
        return

    try:
        _build_and_dispatch(doc_id, source, tab_id,
                            append=append and not replace_all,
                            chunk_size=chunk_size, from_index=from_index,
                            as_json=as_json, quiet=quiet, verbose=verbose,
                            force_clear=force_clear)
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, as_json=as_json)
