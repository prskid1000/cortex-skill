"""claw web — HTTP fetch + content extraction. See references/claw/web.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    "fetch":    ("claw.web.fetch", "fetch"),
    "extract":  ("claw.web.extract", "extract"),
    "table":    ("claw.web.table", "table"),
    "links":    ("claw.web.links", "links"),
    "snapshot": ("claw.web.snapshot", "snapshot"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """Web fetch + content extraction (trafilatura presets)."""
