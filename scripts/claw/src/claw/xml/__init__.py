"""claw xml — lxml wrapper. See references/claw/xml.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    "xpath":        ("claw.xml.xpath", "xpath"),
    "xslt":         ("claw.xml.xslt", "xslt"),
    "validate":     ("claw.xml.validate", "validate"),
    "canonicalize": ("claw.xml.canonicalize", "canonicalize"),
    "fmt":          ("claw.xml.fmt", "fmt"),
    "to-json":      ("claw.xml.to_json", "to_json"),
    "stream-xpath": ("claw.xml.stream_xpath", "stream_xpath"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """XML — xpath, xslt, validate, canonicalize (XXE-safe defaults)."""
