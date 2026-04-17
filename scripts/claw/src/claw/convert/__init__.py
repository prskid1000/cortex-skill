"""claw convert — document format conversion. See references/claw/convert.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    "convert":        ("claw.convert.convert", "convert"),
    "book":           ("claw.convert.book", "book"),
    "md2pdf-nolatex": ("claw.convert.md2pdf_nolatex", "md2pdf_nolatex"),
    "slides":         ("claw.convert.slides", "slides"),
    "list-formats":   ("claw.convert.list_formats", "list_formats"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """Format conversion — pandoc wrapper (md/docx/pdf/html/epub/slides)."""
