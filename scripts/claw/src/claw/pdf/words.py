"""claw pdf words — word-level extraction with font filters."""
from __future__ import annotations

import re
from pathlib import Path

import click

from claw.common import PageSelector, die, emit_json, safe_write


FILTER_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(~=|!=|>=|<=|=|>|<)\s*(.+?)\s*$")


def _parse_filter(spec: str) -> tuple[str, str, str]:
    m = FILTER_RE.match(spec)
    if not m:
        raise click.BadParameter(f"invalid --filter: {spec!r}")
    return m.group(1), m.group(2), m.group(3)


def _match(word: dict, key: str, op: str, raw: str) -> bool:
    v = word.get(key)
    if v is None:
        return False
    if op in (">=", "<=", ">", "<"):
        try:
            vf = float(v)
            rf = float(raw)
        except (TypeError, ValueError):
            return False
        return {">=": vf >= rf, "<=": vf <= rf, ">": vf > rf, "<": vf < rf}[op]
    vs = str(v)
    if op == "=":
        return vs == raw
    if op == "!=":
        return vs != raw
    if op == "~=":
        return raw.lower() in vs.lower()
    return False


@click.command(name="words")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--pages", default="1", help="Page range.")
@click.option("--filter", "filters", multiple=True,
              help='Filter e.g. "fontname~=Bold", "size>=10". Operators: =, !=, ~=, >=, <=, >, <.')
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--force", is_flag=True)
@click.option("--backup", is_flag=True)
@click.option("--mkdir", is_flag=True)
@click.option("--json", "as_json", is_flag=True)
def words(src: Path, pages: str, filters: tuple[str, ...], out: Path | None,
          force: bool, backup: bool, mkdir: bool, as_json: bool) -> None:
    """Extract words from <SRC> with font attributes."""
    try:
        import pdfplumber
    except ImportError:
        die("pdfplumber not installed; install: pip install 'claw[pdf]'")

    parsed = [_parse_filter(f) for f in filters]
    rows: list[dict] = []
    with pdfplumber.open(str(src)) as pdf:
        page_nums = PageSelector(pages).resolve(len(pdf.pages))
        for n in page_nums:
            page = pdf.pages[n - 1]
            for w in page.extract_words(extra_attrs=["fontname", "size"]):
                if all(_match(w, k, op, raw) for k, op, raw in parsed):
                    rows.append({"page": n, **w})

    if out is None:
        emit_json(rows)
        return
    import json as _json
    data = _json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")
    safe_write(out, lambda f: f.write(data), force=force, backup=backup, mkdir=mkdir)
