"""claw pdf barcode — generate various barcode types as single-page PDFs."""
from __future__ import annotations

import io
import re
from pathlib import Path

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json, safe_write


BARCODE_TYPES = ("code128", "ean", "ean13", "upc", "upca", "qr")
SIZE_RE = re.compile(r"^(\d+(?:\.\d+)?)(in|cm|mm|pt)?x(\d+(?:\.\d+)?)(in|cm|mm|pt)?$",
                     re.IGNORECASE)


def _to_points(value: float, unit: str | None) -> float:
    u = (unit or "pt").lower()
    if u == "in": return value * 72.0
    if u == "cm": return value * 72.0 / 2.54
    if u == "mm": return value * 72.0 / 25.4
    return value


def _parse_size(raw: str | None) -> tuple[float, float]:
    if not raw:
        return 200.0, 100.0
    m = SIZE_RE.match(raw.strip())
    if not m:
        raise click.BadParameter(f"invalid --size: {raw!r} (e.g. 3inx1in or 200x100)")
    w = _to_points(float(m.group(1)), m.group(2))
    h = _to_points(float(m.group(3)), m.group(4))
    return w, h


@click.command(name="barcode")
@click.option("--type", "kind", required=True, type=click.Choice(BARCODE_TYPES))
@click.option("--value", required=True)
@click.option("-o", "--out", required=True, type=click.Path(path_type=Path))
@click.option("--size", "size_spec", default=None,
              help="WxH with optional units (e.g. 3inx1in). Default 200x100pt.")
@click.option("--caption", default=None)
@common_output_options
def barcode(kind: str, value: str, out: Path, size_spec: str | None,
            caption: str | None,
            force: bool, backup: bool, as_json: bool, dry_run: bool,
            quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Generate a single-page barcode PDF."""
    try:
        from reportlab.pdfgen.canvas import Canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.utils import ImageReader
    except ImportError:
        die("reportlab not installed; install: pip install 'claw[pdf]'")

    try:
        w, h = _parse_size(size_spec)
    except click.BadParameter as e:
        die(str(e), code=EXIT_INPUT)

    page_w, page_h = letter

    if dry_run:
        click.echo(f"would write {kind} barcode ({value!r}) → {out}")
        return

    def build(f):
        c = Canvas(f, pagesize=letter)
        x = (page_w - w) / 2
        y = (page_h - h) / 2

        if kind == "qr":
            try:
                import qrcode
            except ImportError:
                die("qrcode not installed; install: pip install 'claw[pdf]'")
            img = qrcode.make(value)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            side = min(w, h)
            c.drawImage(ImageReader(buf),
                        (page_w - side) / 2, (page_h - side) / 2,
                        width=side, height=side)
        elif kind == "code128":
            from reportlab.graphics.barcode import code128
            bar_h = max(10.0, h - (18 if caption else 6))
            bc = code128.Code128(value, barHeight=bar_h, humanReadable=not caption)
            bw = bc.width
            bc.drawOn(c, (page_w - bw) / 2, y + (h - bar_h) / 2)
        elif kind in ("ean", "ean13"):
            from reportlab.graphics.barcode.eanbc import Ean13BarcodeWidget
            from reportlab.graphics.shapes import Drawing
            widget = Ean13BarcodeWidget(value)
            bounds = widget.getBounds()
            bw = bounds[2] - bounds[0]
            bh = bounds[3] - bounds[1]
            scale_x = w / bw if bw else 1
            scale_y = h / bh if bh else 1
            d = Drawing(w, h, transform=[scale_x, 0, 0, scale_y,
                                         -bounds[0] * scale_x,
                                         -bounds[1] * scale_y])
            d.add(widget)
            from reportlab.graphics import renderPDF
            renderPDF.draw(d, c, x, y)
        elif kind in ("upc", "upca"):
            from reportlab.graphics.barcode.eanbc import Ean13BarcodeWidget
            from reportlab.graphics.shapes import Drawing
            padded = "0" + value if len(value) == 12 else value
            widget = Ean13BarcodeWidget(padded)
            bounds = widget.getBounds()
            bw = bounds[2] - bounds[0]
            bh = bounds[3] - bounds[1]
            scale_x = w / bw if bw else 1
            scale_y = h / bh if bh else 1
            d = Drawing(w, h, transform=[scale_x, 0, 0, scale_y,
                                         -bounds[0] * scale_x,
                                         -bounds[1] * scale_y])
            d.add(widget)
            from reportlab.graphics import renderPDF
            renderPDF.draw(d, c, x, y)

        if caption:
            c.setFont("Helvetica", 10)
            c.drawCentredString(page_w / 2, y - 14, caption)

        c.showPage()
        c.save()

    safe_write(out, build, force=force, backup=backup, mkdir=mkdir)
    if as_json:
        emit_json({"out": str(out), "type": kind, "value": value})
    elif not quiet:
        click.echo(f"wrote {kind} barcode → {out}")
