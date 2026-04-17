"""claw doc tabs — group aggregating tab subcommands."""

from __future__ import annotations

import click

from claw.doc.tabs_list import tabs_list as _tabs_list


@click.group(name="tabs", context_settings={"help_option_names": ["-h", "--help"]})
def tabs() -> None:
    """Google Docs tab operations."""


tabs.add_command(_tabs_list, name="list")
