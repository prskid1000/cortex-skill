"""claw pdf qr — single-page QR code PDF."""
from __future__ import annotations

import io
from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


PAGE_SIZES = ("Letter", "A4", "Legal")
EC_LEVELS = {"L": "ERROR_CORRECT_L", "M": "ERROR_CORRECT_M",
             "Q": "ERROR_CORRECT_Q", "H": "ERROR_CORRECT_H"}


@click.command(name="qr")
@click.option("--value", required=True, help="QR payload (URL, text, etc.).")
@click.option("-o", "--out", required=True, type=click.Path(path_type=Path))
@click.option("--size", type=float, default=150, help="QR edge length in points.")
@click.option("--ec", type=click.Choice(list(EC_LEVELS)), default="M")
@click.option("--page-size", type=click.Choice(PAGE_SIZES), default="Letter")
@click.option("--caption", default=None)
@common_output_options
def qr(value: str, out: Path, size: float, ec: str, page_size: str,
       caption: str | None,
       force: bool, backup: bool, as_json: bool, dry_run: bool,
       quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Generate a QR code PDF."""
    try:
        import qrcode
    except ImportError:
        die("qrcode not installed; install: pip install 'claw[pdf]'")
    try:
        from reportlab.lib import pagesizes
        from reportlab.pdfgen.canvas import Canvas
        from reportlab.lib.utils import ImageReader
    except ImportError:
        die("reportlab not installed; install: pip install 'claw[pdf]'")

    ec_const = getattr(qrcode.constants, EC_LEVELS[ec])
    qr_obj = qrcode.QRCode(error_correction=ec_const, box_size=10, border=2)
    qr_obj.add_data(value)
    qr_obj.make(fit=True)
    img = qr_obj.make_image(fill_color="black", back_color="white")
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_buf.seek(0)

    # reportlab exposes mixed case: A4 upper; letter/legal lower; LETTER/LEGAL upper.
    # Try upper → lower → title; die cleanly if none match.
    page = (getattr(pagesizes, page_size.upper(), None)
            or getattr(pagesizes, page_size.lower(), None)
            or getattr(pagesizes, page_size, None))
    if page is None:
        die(f"unknown page size: {page_size}", code=EXIT_INPUT)

    if dry_run:
        click.echo(f"would write QR ({value!r}) → {out}")
        return

    def build(f):
        c = Canvas(f, pagesize=page)
        w, h = page
        x = (w - size) / 2
        y = (h - size) / 2
        c.drawImage(ImageReader(img_buf), x, y, width=size, height=size)
        if caption:
            c.setFont("Helvetica", 12)
            c.drawCentredString(w / 2, y - 18, caption)
        c.showPage()
        c.save()

    safe_write(out, build, force=force, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(out), "value": value, "ec": ec, "size": size})
    elif not quiet:
        click.echo(f"wrote QR → {out}")
