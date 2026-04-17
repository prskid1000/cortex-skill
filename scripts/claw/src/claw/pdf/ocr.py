"""claw pdf ocr — PyMuPDF + Tesseract text layer over scanned pages."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import click

from claw.common import PageSelector, common_output_options, die, emit_json, safe_write


def _pymupdf_version() -> tuple[int, ...]:
    import fitz
    v = getattr(fitz, "version", ("0.0.0",))[0]
    parts: list[int] = []
    for chunk in str(v).split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        if digits:
            parts.append(int(digits))
    return tuple(parts) if parts else (0, 0, 0)


@click.command(name="ocr")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--lang", default="eng", help="Tesseract language codes, e.g. eng+fra.")
@click.option("--dpi", type=int, default=300)
@click.option("--sidecar", is_flag=True, help="Also write <out>.txt.")
@click.option("--pages", default="all")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=None)
@click.option("--in-place", is_flag=True)
@click.option("--tessdata", default=None, type=click.Path(exists=True, file_okay=False,
                                                          path_type=Path),
              help="TESSDATA_PREFIX override (path to tessdata/ directory).")
@common_output_options
def ocr(src: Path, lang: str, dpi: int, sidecar: bool, pages: str,
        out: Path | None, in_place: bool, tessdata: Path | None,
        force: bool, backup: bool, as_json: bool, dry_run: bool,
        quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Add an OCR text layer over <SRC> pages (requires tesseract on PATH)."""
    try:
        import fitz
    except ImportError:
        die("PyMuPDF not installed; install: pip install 'claw[pdf]'")

    if not (out or in_place):
        die("pass --out FILE or --in-place", code=2)
    target = src if in_place else out
    assert target is not None

    if tessdata:
        os.environ["TESSDATA_PREFIX"] = str(tessdata)

    ver = _pymupdf_version()
    use_pdfocr_save = ver >= (1, 23, 0) and hasattr(fitz.Pixmap, "pdfocr_save")

    if dry_run:
        click.echo(f"would OCR pages={pages} lang={lang} → {target} "
                   f"(PyMuPDF {'.'.join(map(str, ver))}, "
                   f"{'pdfocr_save' if use_pdfocr_save else 'fallback-textpage'})")
        return

    doc = fitz.open(str(src))
    ocr_text_parts: list[str] = []
    try:
        page_nums = PageSelector(pages).resolve(doc.page_count)

        if use_pdfocr_save:
            # Modern path: build per-page searchable PDFs via Pixmap.pdfocr_save,
            # then splice them back into the source doc.
            for n in page_nums:
                page = doc.load_page(n - 1)
                pix = page.get_pixmap(dpi=dpi)
                tmp_fd, tmp_path = tempfile.mkstemp(prefix=".claw-ocr-", suffix=".pdf")
                os.close(tmp_fd)
                try:
                    try:
                        pix.pdfocr_save(tmp_path, language=lang)
                    except TypeError:
                        pix.pdfocr_save(tmp_path, language=lang, tessdata=str(tessdata or ""))
                    ocr_doc = fitz.open(tmp_path)
                    try:
                        src_rect = page.rect
                        page.show_pdf_page(src_rect, ocr_doc, 0, overlay=True)
                        if sidecar:
                            ocr_page = ocr_doc.load_page(0)
                            ocr_text_parts.append(ocr_page.get_text())
                    finally:
                        ocr_doc.close()
                finally:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
        else:
            click.echo(
                f"warning: OCR layer quality depends on PyMuPDF >=1.23; yours is "
                f"{'.'.join(map(str, ver)) or 'unknown'}",
                err=True,
            )
            for n in page_nums:
                page = doc.load_page(n - 1)
                try:
                    tp_kwargs = {"language": lang, "dpi": dpi, "full": True}
                    if tessdata:
                        tp_kwargs["tessdata"] = str(tessdata)
                    tp = page.get_textpage_ocr(**tp_kwargs)
                except RuntimeError as e:
                    die(f"OCR failed on page {n}: {e}",
                        hint="ensure tesseract is on PATH; check `claw doctor`", code=5)
                text = page.get_text(textpage=tp)
                if sidecar:
                    ocr_text_parts.append(text)
                # Write the OCR'd text as an (effectively invisible) overlay so
                # search/extract-text can find it. Render mode 3 = invisible.
                try:
                    page.insert_textbox(
                        page.rect, text, fontname="helv", fontsize=1,
                        color=(0, 0, 0), render_mode=3, overlay=True,
                    )
                except Exception:
                    pass

        data = doc.tobytes(deflate=True)
    finally:
        doc.close()

    safe_write(target, lambda f: f.write(data),
               force=force or in_place, backup=backup, mkdir=mkdir)

    sidecar_path = None
    if sidecar:
        sidecar_path = Path(str(target) + ".txt")
        sidecar_path.write_text("\n\n".join(ocr_text_parts), encoding="utf-8")

    if as_json:
        emit_json({"out": str(target), "pages": len(page_nums), "lang": lang,
                   "sidecar": str(sidecar_path) if sidecar_path else None,
                   "engine": "pdfocr_save" if use_pdfocr_save else "textpage-fallback"})
    elif not quiet:
        click.echo(f"OCR'd {len(page_nums)} pages → {target}")
