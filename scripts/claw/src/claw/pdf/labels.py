"""claw pdf labels — group aggregating page-label subcommands."""

from __future__ import annotations

import click

from claw.pdf.labels_set import labels_set as _labels_set


@click.group(name="labels", context_settings={"help_option_names": ["-h", "--help"]})
def labels() -> None:
    """Page-label operations."""


labels.add_command(_labels_set, name="set")
