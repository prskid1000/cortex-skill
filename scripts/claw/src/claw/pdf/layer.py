"""claw pdf layer — group aggregating OCG layer subcommands."""

from __future__ import annotations

import click

from claw.pdf.layer_toggle import layer_toggle as _layer_toggle


@click.group(name="layer", context_settings={"help_option_names": ["-h", "--help"]})
def layer() -> None:
    """OCG (optional content group) operations."""


layer.add_command(_layer_toggle, name="toggle")
