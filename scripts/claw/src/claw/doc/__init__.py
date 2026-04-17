"""claw doc — Google Docs wrapper. See references/claw/doc.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    "create":    ("claw.doc.create", "create"),
    "build":     ("claw.doc.build", "build"),
    "append":    ("claw.doc.append", "append"),
    "replace":   ("claw.doc.replace", "replace"),
    "read":      ("claw.doc.read", "read"),
    "tabs":      ("claw.doc.tabs", "tabs"),
    "export":    ("claw.doc.export", "export"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """Google Docs — create, build (markdown → batchUpdate chunked), read, export."""
