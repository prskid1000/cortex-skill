"""claw pdf form-fill — fill AcroForm fields from a JSON object."""
from __future__ import annotations

import json
from pathlib import Path

import click

from claw.common import common_output_options, die, emit_json, safe_write


@click.command(name="form-fill")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--values", "values_path", required=True,
              type=click.Path(exists=True, dir_okay=False, path_type=Path),
              help="JSON object mapping field name → value.")
@click.option("--flatten", "flatten_after", is_flag=True,
              help="Bake filled values into page content.")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True)
@common_output_options
def form_fill(src: Path, values_path: Path, flatten_after: bool,
              out: Path | None, in_place: bool,
              force: bool, backup: bool, as_json: bool, dry_run: bool,
              quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Populate form fields of <SRC> from --values FILE.json."""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        die("pypdf not installed; install: pip install 'claw[pdf]'")

    if not (out or in_place):
        die("pass --out FILE or --in-place", code=2)
    target = src if in_place else out
    assert target is not None

    values = json.loads(values_path.read_text(encoding="utf-8"))
    if not isinstance(values, dict):
        die("--values JSON must be an object {field: value}", code=2)

    reader = PdfReader(str(src))
    writer = PdfWriter(clone_from=reader)

    updated = 0
    for page in writer.pages:
        try:
            writer.update_page_form_field_values(page, values)
            updated += 1
        except Exception:
            continue

    if dry_run:
        click.echo(f"would fill {len(values)} field(s) across {updated} page(s) → {target}")
        return

    if flatten_after:
        try:
            import fitz
            tmp_bytes_holder: list[bytes] = []

            def _write_stage(f):
                writer.write(f)

            import io
            stage = io.BytesIO()
            writer.write(stage)
            stage.seek(0)
            doc = fitz.open(stream=stage.getvalue(), filetype="pdf")
            try:
                if hasattr(doc, "bake"):
                    doc.bake(annots=False, widgets=True)
                data = doc.tobytes(deflate=True, garbage=4)
            finally:
                doc.close()
            safe_write(target, lambda f: f.write(data),
                       force=force or in_place, backup=backup, mkdir=mkdir)
        except ImportError:
            die("PyMuPDF required for --flatten; install: pip install 'claw[pdf]'")
    else:
        safe_write(target, lambda f: writer.write(f),
                   force=force or in_place, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"out": str(target), "fields_set": len(values),
                   "flattened": flatten_after})
    elif not quiet:
        click.echo(f"filled {len(values)} field(s) → {target}")
