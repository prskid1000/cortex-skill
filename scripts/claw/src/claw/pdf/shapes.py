"""claw pdf shapes — vector shapes (rects, curves, lines) via pdfplumber."""
from __future__ import annotations

import json
from pathlib import Path

import click

from claw.common import PageSelector, die, emit_json, safe_write


SAFE_KEYS = ("x0", "y0", "x1", "y1", "top", "bottom", "width", "height",
             "stroke", "fill", "linewidth", "stroking_color", "non_stroking_color",
             "object_type", "pts")


def _clean(obj: dict) -> dict:
    out = {}
    for k in SAFE_KEYS:
        if k in obj:
            v = obj[k]
            try:
                json.dumps(v)
                out[k] = v
            except (TypeError, ValueError):
                out[k] = str(v)
    return out


@click.command(name="shapes")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--pages", default="1", help="Page range.")
@click.option("--kind", type=click.Choice(["line", "rect", "curve", "all"]),
              default="all")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--force", is_flag=True)
@click.option("--backup", is_flag=True)
@click.option("--mkdir", is_flag=True)
@click.option("--json", "as_json", is_flag=True)
def shapes(src: Path, pages: str, kind: str, out: Path | None,
           force: bool, backup: bool, mkdir: bool, as_json: bool) -> None:
    """Dump vector shapes (rects / curves / lines) from <SRC>."""
    try:
        import pdfplumber
    except ImportError:
        die("pdfplumber not installed; install: pip install 'claw[pdf]'")

    rows: list[dict] = []
    with pdfplumber.open(str(src)) as pdf:
        page_nums = PageSelector(pages).resolve(len(pdf.pages))
        for n in page_nums:
            page = pdf.pages[n - 1]
            if kind in ("rect", "all"):
                for r in page.rects:
                    rows.append({"page": n, "kind": "rect", **_clean(r)})
            if kind in ("curve", "all"):
                for c in page.curves:
                    rows.append({"page": n, "kind": "curve", **_clean(c)})
            if kind in ("line", "all"):
                for line in page.lines:
                    rows.append({"page": n, "kind": "line", **_clean(line)})

    if out is None:
        emit_json(rows)
        return
    data = json.dumps(rows, ensure_ascii=False, indent=2, default=str).encode("utf-8")
    safe_write(out, lambda f: f.write(data), force=force, backup=backup, mkdir=mkdir)
