"""claw pptx — PowerPoint operations. See references/claw/pptx.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    "new":          ("claw.pptx.new", "new"),
    "from-outline": ("claw.pptx.from_outline", "from_outline"),
    "add-slide":    ("claw.pptx.add_slide", "add_slide"),
    "add-chart":    ("claw.pptx.add_chart", "add_chart"),
    "add-table":    ("claw.pptx.add_table", "add_table"),
    "add-image":    ("claw.pptx.add_image", "add_image"),
    "add-shape":    ("claw.pptx.add_shape", "add_shape"),
    "fill":         ("claw.pptx.fill", "fill"),
    "chart":        ("claw.pptx.chart_refresh", "chart"),
    "reorder":      ("claw.pptx.reorder", "reorder"),
    "brand":        ("claw.pptx.brand", "brand"),
    "image":        ("claw.pptx.image", "image"),
    "link":         ("claw.pptx.link", "link"),
    "notes":        ("claw.pptx.notes", "notes"),
    "meta":         ("claw.pptx.meta", "meta"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """PowerPoint (.pptx) — new, add-*, reorder, brand, image-crop, link, notes, meta."""
