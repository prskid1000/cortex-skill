"""claw drive — Google Drive file operations. See references/claw/drive.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    "upload":        ("claw.drive.upload", "upload"),
    "download":      ("claw.drive.download", "download"),
    "info":          ("claw.drive.info", "info"),
    "share":         ("claw.drive.share", "share"),
    "share-list":    ("claw.drive.share_list", "share_list"),
    "share-revoke":  ("claw.drive.share_revoke", "share_revoke"),
    "list":          ("claw.drive.list_", "list_"),
    "move":          ("claw.drive.move", "move"),
    "copy":          ("claw.drive.copy", "copy"),
    "rename":        ("claw.drive.rename", "rename"),
    "delete":        ("claw.drive.delete", "delete"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """Google Drive file ops — upload/download (with native conversion), list, move, copy, rename, delete, share."""
