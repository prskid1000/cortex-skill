"""claw pdf form-list — enumerate AcroForm fields."""
from __future__ import annotations

from pathlib import Path

import click

from claw.common import die, emit_json


FIELD_TYPES = {
    "/Tx": "text", "/Btn": "button", "/Ch": "choice", "/Sig": "signature",
}


@click.command(name="form-list")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
def form_list(src: Path, as_json: bool) -> None:
    """List AcroForm fields in <SRC>."""
    try:
        from pypdf import PdfReader
    except ImportError:
        die("pypdf not installed; install: pip install 'claw[pdf]'")

    reader = PdfReader(str(src))
    fields_map = reader.get_fields() or {}

    page_of: dict[str, int] = {}
    for i, page in enumerate(reader.pages, start=1):
        annots = page.get("/Annots")
        if not annots:
            continue
        for annot_ref in annots:
            try:
                annot = annot_ref.get_object()
            except Exception:
                continue
            name = annot.get("/T")
            if name:
                page_of[str(name)] = i

    rows: list[dict] = []
    for name, f in fields_map.items():
        ft = f.get("/FT")
        rect = f.get("/Rect")
        rows.append({
            "name": str(name),
            "type": FIELD_TYPES.get(str(ft), str(ft) if ft else "unknown"),
            "value": f.get("/V"),
            "flags": int(f.get("/Ff", 0) or 0),
            "page": page_of.get(str(name)),
            "rect": [float(x) for x in rect] if rect else None,
        })

    if as_json:
        emit_json(rows)
        return
    for r in rows:
        val = r["value"] if r["value"] is not None else ""
        click.echo(f"{r['name']:30s} {r['type']:10s} p={r['page']}  {val}")
    click.echo(f"── {len(rows)} field(s)")
