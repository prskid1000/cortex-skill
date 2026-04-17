"""claw docx — Word operations. See references/claw/docx.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    "new":           ("claw.docx.new", "new"),
    "read":          ("claw.docx.read", "read"),
    "from-md":       ("claw.docx.from_md", "from_md"),
    "add-heading":   ("claw.docx.add_heading", "add_heading"),
    "add-paragraph": ("claw.docx.add_paragraph", "add_paragraph"),
    "add-table":     ("claw.docx.add_table", "add_table"),
    "add-image":     ("claw.docx.add_image", "add_image"),
    "header":        ("claw.docx.header", "header"),
    "footer":        ("claw.docx.footer", "footer"),
    "toc":           ("claw.docx.toc", "toc"),
    "meta":          ("claw.docx.meta", "meta"),
    "comments":      ("claw.docx.comments_dump", "comments"),
    "diff":          ("claw.docx.diff", "diff"),
    "insert":        ("claw.docx.insert_pagebreak", "insert"),
    "hyperlink":     ("claw.docx.hyperlink_add", "hyperlink"),
    "style":         ("claw.docx.style", "style"),
    "section":       ("claw.docx.section", "section"),
    "custom-xml":    ("claw.docx.custom_xml", "custom_xml"),
    "table":         ("claw.docx.table_fit", "table"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """Word (.docx) — new, read, add headings/tables/images, headers/footers, TOC."""
