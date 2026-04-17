"""claw pdf chars — per-character positional data via pdfplumber."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import click

from claw.common import PageSelector, die, emit_json, safe_write


COLS = ("text", "x0", "top", "x1", "bottom", "fontname", "size")


@click.command(name="chars")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--pages", default="1", help="Page range (default: 1).")
@click.option("--bbox", help="Restrict to x0,y0,x1,y1.")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None,
              help="Output .csv / .json; stdout CSV if omitted.")
@click.option("--force", is_flag=True)
@click.option("--backup", is_flag=True)
@click.option("--mkdir", is_flag=True)
@click.option("--json", "as_json", is_flag=True)
def chars(src: Path, pages: str, bbox: str | None, out: Path | None,
          force: bool, backup: bool, mkdir: bool, as_json: bool) -> None:
    """Dump per-character positional data from <SRC>."""
    try:
        import pdfplumber
    except ImportError:
        die("pdfplumber not installed; install: pip install 'claw[pdf]'")

    crop_box = None
    if bbox:
        crop_box = tuple(float(x) for x in bbox.split(","))
        if len(crop_box) != 4:
            die("--bbox must be x0,y0,x1,y1", code=2)

    rows: list[dict] = []
    with pdfplumber.open(str(src)) as pdf:
        page_nums = PageSelector(pages).resolve(len(pdf.pages))
        for n in page_nums:
            page = pdf.pages[n - 1]
            target = page.within_bbox(crop_box) if crop_box else page
            for ch in target.chars:
                rows.append({
                    "page": n,
                    "text": ch.get("text", ""),
                    "x0": ch.get("x0"),
                    "top": ch.get("top"),
                    "x1": ch.get("x1"),
                    "bottom": ch.get("bottom"),
                    "fontname": ch.get("fontname", ""),
                    "size": ch.get("size"),
                })

    if as_json and out is None:
        emit_json(rows)
        return

    headers = ("page",) + COLS
    if out is None:
        w = csv.writer(click.get_text_stream("stdout"))
        w.writerow(headers)
        for r in rows:
            w.writerow([r.get(h, "") for h in headers])
        return

    suffix = out.suffix.lower()
    if suffix == ".json" or as_json:
        data = json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")
        safe_write(out, lambda f: f.write(data),
                   force=force, backup=backup, mkdir=mkdir)
    else:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(headers)
        for r in rows:
            w.writerow([r.get(h, "") for h in headers])
        data = buf.getvalue().encode("utf-8")
        safe_write(out, lambda f: f.write(data),
                   force=force, backup=backup, mkdir=mkdir)
