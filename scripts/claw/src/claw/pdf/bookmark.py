"""claw pdf bookmark — group aggregating bookmark-related subcommands."""

from __future__ import annotations

import click

from claw.pdf.bookmark_add import bookmark_add as _bookmark_add


@click.group(name="bookmark", context_settings={"help_option_names": ["-h", "--help"]})
def bookmark() -> None:
    """Outline (bookmark) operations."""


bookmark.add_command(_bookmark_add, name="add")
