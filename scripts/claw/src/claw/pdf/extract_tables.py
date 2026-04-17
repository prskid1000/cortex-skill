"""claw pdf extract-tables — table extraction via pdfplumber."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import click

from claw.common import PageSelector, die, emit_json, safe_write


STRATEGIES = ("lines", "lines_strict", "text", "explicit")
AXIS_STRATEGIES = ("lines", "lines_strict", "text", "explicit")


def _parse_floats(spec: str | None) -> list[float] | None:
    if not spec:
        return None
    return [float(x) for x in spec.split(",") if x.strip()]


@click.command(name="extract-tables")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--pages", default="all", help="Page range (default: all).")
@click.option("--strategy", type=click.Choice(STRATEGIES), default="lines",
              help="Preset applied to both axes; overridden by --vertical-strategy / --horizontal-strategy.")
@click.option("--vertical-strategy", "vertical_strategy",
              type=click.Choice(AXIS_STRATEGIES), default=None,
              help="Per-axis override for vertical edges.")
@click.option("--horizontal-strategy", "horizontal_strategy",
              type=click.Choice(AXIS_STRATEGIES), default=None,
              help="Per-axis override for horizontal edges.")
@click.option("--vlines", help="Explicit vertical split x-coords, comma-separated.")
@click.option("--hlines", help="Explicit horizontal split y-coords, comma-separated.")
@click.option("--snap-tol", type=float, default=3.0)
@click.option("--join-tol", type=float, default=3.0)
@click.option("--edge-min-length", type=float, default=3.0)
@click.option("--intersection-tol", type=float, default=3.0)
@click.option("--text-tolerance", type=float, default=3.0)
@click.option("--bbox", help="Restrict search to x0,y0,x1,y1.")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None,
              help="Output .csv / .json / .xlsx; stdout CSV if omitted.")
@click.option("--force", is_flag=True)
@click.option("--backup", is_flag=True)
@click.option("--mkdir", is_flag=True)
@click.option("--json", "as_json", is_flag=True)
def extract_tables(src: Path, pages: str, strategy: str,
                   vertical_strategy: str | None, horizontal_strategy: str | None,
                   vlines: str | None, hlines: str | None,
                   snap_tol: float, join_tol: float,
                   edge_min_length: float, intersection_tol: float,
                   text_tolerance: float, bbox: str | None, out: Path | None,
                   force: bool, backup: bool, mkdir: bool, as_json: bool) -> None:
    """Extract tables from <SRC> using pdfplumber strategies."""
    try:
        import pdfplumber
    except ImportError:
        die("pdfplumber not installed; install: pip install 'claw[pdf]'")

    v_strat = vertical_strategy or strategy
    h_strat = horizontal_strategy or strategy

    settings: dict = {
        "vertical_strategy": v_strat,
        "horizontal_strategy": h_strat,
        "snap_tolerance": snap_tol,
        "join_tolerance": join_tol,
        "edge_min_length": edge_min_length,
        "intersection_tolerance": intersection_tol,
        "text_tolerance": text_tolerance,
    }

    explicit_v = _parse_floats(vlines)
    explicit_h = _parse_floats(hlines)
    if v_strat == "explicit":
        settings["explicit_vertical_lines"] = explicit_v or []
        if not explicit_v:
            die("--vertical-strategy explicit requires --vlines", code=2)
    elif explicit_v:
        settings["explicit_vertical_lines"] = explicit_v
    if h_strat == "explicit":
        settings["explicit_horizontal_lines"] = explicit_h or []
        if not explicit_h:
            die("--horizontal-strategy explicit requires --hlines", code=2)
    elif explicit_h:
        settings["explicit_horizontal_lines"] = explicit_h

    crop_box = None
    if bbox:
        crop_box = tuple(float(x) for x in bbox.split(","))
        if len(crop_box) != 4:
            die("--bbox must be x0,y0,x1,y1", hint="e.g. 72,72,540,720")

    all_tables: list[dict] = []
    with pdfplumber.open(str(src)) as pdf:
        page_nums = PageSelector(pages).resolve(len(pdf.pages))
        for n in page_nums:
            page = pdf.pages[n - 1]
            target = page.within_bbox(crop_box) if crop_box else page
            tables = target.extract_tables(table_settings=settings)
            for idx, tbl in enumerate(tables):
                all_tables.append({"page": n, "index": idx, "rows": tbl})

    if as_json and out is None:
        emit_json(all_tables)
        return

    if out is None:
        w = csv.writer(click.get_text_stream("stdout"))
        for t in all_tables:
            w.writerow([f"# page {t['page']} table {t['index']}"])
            w.writerows(t["rows"])
        return

    suffix = out.suffix.lower()
    if suffix == ".json":
        safe_write(out, lambda f: f.write(json.dumps(all_tables, ensure_ascii=False,
                                                     indent=2).encode("utf-8")),
                   force=force, backup=backup, mkdir=mkdir)
    elif suffix == ".xlsx":
        try:
            from openpyxl import Workbook
        except ImportError:
            die("openpyxl not installed; install: pip install 'claw[xlsx]'")
        wb = Workbook()
        wb.remove(wb.active)
        for t in all_tables:
            ws = wb.create_sheet(title=f"p{t['page']}_t{t['index']}"[:31])
            for row in t["rows"]:
                ws.append(row)
        safe_write(out, lambda f: wb.save(f), force=force, backup=backup, mkdir=mkdir)
    else:
        buf = io.StringIO()
        w = csv.writer(buf)
        for t in all_tables:
            w.writerow([f"# page {t['page']} table {t['index']}"])
            w.writerows(t["rows"])
        data = buf.getvalue().encode("utf-8")
        safe_write(out, lambda f: f.write(data), force=force, backup=backup, mkdir=mkdir)
