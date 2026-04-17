"""claw web table — pull <table> elements to CSV / XLSX."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, EXIT_USAGE, common_output_options, die, emit_json, read_text,
    safe_write, write_rows_csv,
)


def _fetch_html(src: str) -> str:
    if src == "-":
        return sys.stdin.read()
    if src.startswith(("http://", "https://")):
        try:
            import httpx
        except ImportError:
            die("httpx not installed", code=EXIT_INPUT, hint="pip install 'claw[web]'")
        r = httpx.get(src, follow_redirects=True, timeout=30.0,
                      headers={"User-Agent": "claw/1.0"})
        r.raise_for_status()
        return r.text
    return read_text(src)


def _table_to_rows(table) -> list[list[str]]:
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        rows.append([c.get_text(strip=True) for c in cells])
    return rows


def _rows_to_records(rows: list[list[str]], header_mode: str) -> list[dict[str, str]] | list[list[str]]:
    if header_mode == "first-row" and rows:
        cols = rows[0]
        return [dict(zip(cols, r)) for r in rows[1:]]
    return rows


def _rows_to_csv_string(rows: list[list[str]]) -> str:
    import csv, io
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    return buf.getvalue()


@click.command(name="table")
@click.argument("src")
@click.option("--selector", default=None, help="CSS selector narrowing which table(s).")
@click.option("--index", default=None, type=int, help="1-based table index.")
@click.option("--all", "all_tables", is_flag=True, help="Emit every table.")
@click.option("--out", required=True, type=click.Path(path_type=Path),
              help="Output .csv / .xlsx, directory/ for per-table files, or `-` for stdout.")
@click.option("--headers", "header_mode", default="first-row",
              type=click.Choice(["first-row", "none"]))
@common_output_options
def table(src: str, selector: str | None, index: int | None, all_tables: bool,
          out: Path, header_mode: str, force: bool, backup: bool, as_json: bool,
          dry_run: bool, quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Pull <table> elements from a URL / file / stdin into CSV or XLSX."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        die("beautifulsoup4 not installed", code=EXIT_INPUT,
            hint="pip install 'claw[html]'", as_json=as_json)

    html = _fetch_html(src)
    soup = BeautifulSoup(html, "lxml")
    tables = soup.select(selector) if selector else soup.find_all("table")
    if not tables:
        die("no tables matched", code=EXIT_INPUT, as_json=as_json)

    if index is not None:
        if index < 1 or index > len(tables):
            die(f"--index {index} out of range (1..{len(tables)})",
                code=EXIT_USAGE, as_json=as_json)
        tables = [tables[index - 1]]

    if dry_run:
        click.echo(f"would write {len(tables)} table(s) -> {out}")
        return

    out_str = str(out)
    is_stdout = out_str == "-"
    is_xlsx = out_str.lower().endswith(".xlsx")
    is_dir = out_str.endswith(("/", "\\")) or (not is_stdout and not is_xlsx
                                               and not out_str.lower().endswith(".csv")
                                               and out.is_dir())

    if is_xlsx:
        try:
            from openpyxl import Workbook
        except ImportError:
            die("openpyxl not installed", code=EXIT_INPUT,
                hint="pip install 'claw[xlsx]'", as_json=as_json)
        wb = Workbook()
        wb.remove(wb.active)
        for i, t in enumerate(tables, 1):
            ws = wb.create_sheet(f"table_{i}")
            for row in _table_to_rows(t):
                ws.append(row)
        import io
        buf = io.BytesIO()
        wb.save(buf)
        safe_write(out, lambda f: f.write(buf.getvalue()),
                   force=force, backup=backup, mkdir=mkdir)
    elif is_dir:
        if mkdir:
            out.mkdir(parents=True, exist_ok=True)
        if not out.exists():
            die(f"directory does not exist: {out} (pass --mkdir to create)",
                code=EXIT_INPUT, as_json=as_json)
        for i, t in enumerate(tables, 1):
            rows = _table_to_rows(t)
            target = out / f"table-{i}.csv"
            records = _rows_to_records(rows, header_mode)
            if header_mode == "first-row" and rows:
                write_rows_csv(str(target), records)  # type: ignore[arg-type]
            else:
                csv_text = _rows_to_csv_string(rows)
                safe_write(target, lambda f, t=csv_text: f.write(t.encode("utf-8")),
                           force=force, backup=backup, mkdir=False)
    elif is_stdout:
        if len(tables) == 1:
            rows = _table_to_rows(tables[0])
            if as_json:
                emit_json(_rows_to_records(rows, header_mode))
            else:
                sys.stdout.write(_rows_to_csv_string(rows))
        else:
            # Multiple tables to stdout: JSON array or CSV blocks separated by "\n---\n".
            all_rows = [_table_to_rows(t) for t in tables]
            if as_json:
                emit_json([_rows_to_records(r, header_mode) for r in all_rows])
            else:
                sep = "\n---\n"
                chunks = [_rows_to_csv_string(r).rstrip("\n") for r in all_rows]
                sys.stdout.write(sep.join(chunks))
                if chunks:
                    sys.stdout.write("\n")
    else:
        # Single CSV file path with possibly multiple tables.
        if len(tables) > 1:
            die("CSV output supports only one table; use --index, --all with a directory, or .xlsx",
                code=EXIT_USAGE, as_json=as_json)
        rows = _table_to_rows(tables[0])
        records = _rows_to_records(rows, header_mode)
        if header_mode == "first-row" and rows:
            write_rows_csv(out_str, records)  # type: ignore[arg-type]
        else:
            csv_text = _rows_to_csv_string(rows)
            safe_write(out, lambda f: f.write(csv_text.encode("utf-8")),
                       force=force, backup=backup, mkdir=mkdir)

    if as_json and not is_stdout:
        emit_json({"out": str(out), "tables": len(tables)})
    elif not quiet and not is_stdout:
        click.echo(f"wrote {out} ({len(tables)} table(s))")
