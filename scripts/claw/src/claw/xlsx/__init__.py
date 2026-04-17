"""claw xlsx — Excel operations. See references/claw/xlsx.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    "new":         ("claw.xlsx.new", "new"),
    "read":        ("claw.xlsx.read", "read"),
    "append":      ("claw.xlsx.append", "append"),
    "from-csv":    ("claw.xlsx.from_csv", "from_csv"),
    "from-json":   ("claw.xlsx.from_json", "from_json"),
    "from-html":   ("claw.xlsx.from_html", "from_html"),
    "from-pdf":    ("claw.xlsx.from_pdf", "from_pdf"),
    "to-csv":      ("claw.xlsx.to_csv", "to_csv"),
    "to-pdf":      ("claw.xlsx.to_pdf", "to_pdf"),
    "sql":         ("claw.xlsx.sql", "sql"),
    "style":       ("claw.xlsx.style", "style"),
    "format":      ("claw.xlsx.format", "format"),
    "table":       ("claw.xlsx.table", "table"),
    "richtext":    ("claw.xlsx.richtext_set", "richtext"),
    "image":       ("claw.xlsx.image_add", "image"),
    "name":        ("claw.xlsx.name_add", "name"),
    "print-setup": ("claw.xlsx.print_setup", "print_setup"),
    "pivots":      ("claw.xlsx.pivots_list", "pivots"),
    "freeze":      ("claw.xlsx.freeze", "freeze"),
    "filter":      ("claw.xlsx.filter_", "filter_"),
    "chart":       ("claw.xlsx.chart", "chart"),
    "validate":    ("claw.xlsx.validate", "validate"),
    "protect":     ("claw.xlsx.protect", "protect"),
    "conditional": ("claw.xlsx.conditional", "conditional"),
    "meta":        ("claw.xlsx.meta", "meta"),
    "stat":        ("claw.xlsx.stat", "stat"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """Excel (.xlsx) operations — new, read, chart, validate, protect, freeze, filter."""
