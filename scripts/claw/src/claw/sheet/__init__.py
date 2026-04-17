"""claw sheet — Google Drive upload/download wrapper. See references/claw/sheet.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    "upload":        ("claw.sheet.upload", "upload"),
    "download":      ("claw.sheet.download", "download"),
    "share":         ("claw.sheet.share", "share"),
    "share-list":    ("claw.sheet.share_list", "share_list"),
    "share-revoke":  ("claw.sheet.share_revoke", "share_revoke"),
    "list":          ("claw.sheet.list_", "list_"),
    "move":          ("claw.sheet.move", "move"),
    "copy":          ("claw.sheet.copy", "copy"),
    "rename":        ("claw.sheet.rename", "rename"),
    "delete":        ("claw.sheet.delete", "delete"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """Google Drive uploads/downloads — xlsx→Sheet/docx→Doc auto-convert."""
