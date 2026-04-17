"""claw html diagnose — show how each installed parser parses the document."""

from __future__ import annotations

import io
import sys

import click

from claw.common import (
    EXIT_INPUT, common_output_options, die, emit_json, read_text,
)


@click.command(name="diagnose")
@click.argument("src")
@common_output_options
def diagnose(src: str,
             force: bool, backup: bool, as_json: bool, dry_run: bool,
             quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Show how each installed parser parses the document."""
    try:
        from bs4 import diagnose as bs4_diagnose
    except ImportError:
        die("beautifulsoup4 not installed", code=EXIT_INPUT,
            hint="pip install 'claw[html]'", as_json=as_json)

    html = read_text(src)
    if dry_run:
        click.echo(f"would diagnose {src}")
        return

    buf = io.StringIO()
    orig_stdout = sys.stdout
    try:
        sys.stdout = buf
        bs4_diagnose.diagnose(html)
    finally:
        sys.stdout = orig_stdout

    report = buf.getvalue()
    if as_json:
        emit_json({"src": src, "report": report})
    else:
        sys.stdout.write(report)
