"""claw html — BeautifulSoup/lxml HTML wrapper. See references/claw/html.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    "select":     ("claw.html.select", "select"),
    "text":       ("claw.html.text", "text"),
    "strip":      ("claw.html.strip", "strip_"),
    "unwrap":     ("claw.html.unwrap", "unwrap"),
    "wrap":       ("claw.html.wrap", "wrap"),
    "replace":    ("claw.html.replace", "replace"),
    "sanitize":   ("claw.html.sanitize", "sanitize"),
    "absolutize": ("claw.html.absolutize", "absolutize"),
    "rewrite":    ("claw.html.rewrite", "rewrite"),
    "fmt":        ("claw.html.fmt", "fmt"),
    "diagnose":   ("claw.html.diagnose", "diagnose"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """HTML — CSS select, text extract, strip, sanitize, absolutize."""
