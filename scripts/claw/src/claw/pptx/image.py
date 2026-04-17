"""claw pptx image — group aggregating image subcommands."""

from __future__ import annotations

import click

from claw.pptx.image_crop import image_crop as _image_crop


@click.group(name="image", context_settings={"help_option_names": ["-h", "--help"]})
def image() -> None:
    """Picture-shape operations."""


image.add_command(_image_crop, name="crop")
