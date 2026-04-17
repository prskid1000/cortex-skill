"""claw pdf — PDF operations. See references/claw/pdf.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    # READ / EXTRACT
    "extract-text":   ("claw.pdf.extract_text", "extract_text"),
    "extract-tables": ("claw.pdf.extract_tables", "extract_tables"),
    "extract-images": ("claw.pdf.extract_images", "extract_images"),
    "search":         ("claw.pdf.search", "search"),
    "info":           ("claw.pdf.info", "info"),
    "chars":          ("claw.pdf.chars", "chars"),
    "words":          ("claw.pdf.words", "words"),
    "shapes":         ("claw.pdf.shapes", "shapes"),
    # RENDER
    "render":         ("claw.pdf.render", "render"),
    "tables-debug":   ("claw.pdf.tables_debug", "tables_debug"),
    # TRANSFORM
    "merge":          ("claw.pdf.merge", "merge"),
    "split":          ("claw.pdf.split", "split_"),
    "rotate":         ("claw.pdf.rotate", "rotate"),
    "crop":           ("claw.pdf.crop", "crop"),
    # STAMP / WATERMARK
    "watermark":      ("claw.pdf.watermark", "watermark"),
    "stamp":          ("claw.pdf.stamp", "stamp"),
    # SECURE
    "redact":         ("claw.pdf.redact", "redact"),
    "encrypt":        ("claw.pdf.encrypt", "encrypt"),
    "decrypt":        ("claw.pdf.decrypt", "decrypt"),
    "flatten":        ("claw.pdf.flatten", "flatten"),
    # ANNOTATE
    "annotate":       ("claw.pdf.annotate", "annotate"),
    # FORMS
    "form":           ("claw.pdf.form", "form"),
    # META / STRUCTURE
    "meta":           ("claw.pdf.meta", "meta"),
    "toc":            ("claw.pdf.toc", "toc"),
    "bookmark":       ("claw.pdf.bookmark", "bookmark"),
    "layer":          ("claw.pdf.layer", "layer"),
    "labels":         ("claw.pdf.labels", "labels"),
    "attach":         ("claw.pdf.attach", "attach"),
    "journal":        ("claw.pdf.journal", "journal"),
    # OCR
    "ocr":            ("claw.pdf.ocr", "ocr"),
    # CREATE
    "from-html":      ("claw.pdf.from_html", "from_html"),
    "from-md":        ("claw.pdf.from_md", "from_md"),
    "convert":        ("claw.pdf.convert", "convert"),
    "qr":             ("claw.pdf.qr", "qr"),
    "barcode":        ("claw.pdf.barcode", "barcode"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """PDF — extract, render, merge/split, redact/encrypt, OCR, from-html/md, QR."""
