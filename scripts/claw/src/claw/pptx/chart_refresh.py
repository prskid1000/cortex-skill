"""claw pptx chart refresh — replace data on an existing native chart."""

from __future__ import annotations

from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, common_output_options, die, emit_json, read_rows, safe_write,
)


@click.group(name="chart")
def chart() -> None:
    """Chart update operations."""


@chart.command(name="refresh")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--slide", required=True, type=int, help="1-based slide index.")
@click.option("--csv", "csv_path", required=True,
              type=click.Path(exists=True, path_type=Path))
@click.option("--shape-name", "shape_name", default=None,
              help="Disambiguate when a slide contains multiple charts.")
@common_output_options
def chart_refresh(src: Path, slide: int, csv_path: Path, shape_name: str | None,
                  force: bool, backup: bool, as_json: bool, dry_run: bool,
                  quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Re-read a CSV and replace the chart's data in place."""
    try:
        from pptx import Presentation
        from pptx.chart.data import CategoryChartData
    except ImportError:
        die("python-pptx not installed", code=EXIT_INPUT,
            hint="uv tool install 'claw[pptx]'", as_json=as_json)

    rows = read_rows(csv_path, header=True)
    if not rows:
        die("CSV has no rows", code=EXIT_INPUT, as_json=as_json)

    if dry_run:
        click.echo(f"would refresh chart on slide {slide} from {csv_path}")
        return

    prs = Presentation(str(src))
    if slide < 1 or slide > len(prs.slides):
        die(f"slide {slide} out of range", code=EXIT_INPUT, as_json=as_json)
    target = prs.slides[slide - 1]

    chart_shape = None
    for s in target.shapes:
        if not s.has_chart:
            continue
        if shape_name and s.name != shape_name:
            continue
        chart_shape = s
        break
    if chart_shape is None:
        die(f"no chart found on slide {slide}"
            + (f" with shape name {shape_name!r}" if shape_name else ""),
            code=EXIT_INPUT, as_json=as_json)

    if isinstance(rows[0], dict):
        headers = list(rows[0].keys())
        cat_key = headers[0]
        data = CategoryChartData()
        data.categories = [r[cat_key] for r in rows]
        for col in headers[1:]:
            data.add_series(col, [_num(r[col]) for r in rows])
    else:
        headers = rows[0]
        data = CategoryChartData()
        data.categories = [r[0] for r in rows[1:]]
        for ci, col in enumerate(headers[1:], start=1):
            data.add_series(col, [_num(r[ci]) for r in rows[1:]])

    chart_shape.chart.replace_data(data)

    def _save(f):
        prs.save(f)

    safe_write(src, _save, force=True, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(src), "slide": slide, "csv": str(csv_path),
                   "series": len(headers) - 1})
    elif not quiet:
        click.echo(f"refreshed chart on slide {slide}")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0
