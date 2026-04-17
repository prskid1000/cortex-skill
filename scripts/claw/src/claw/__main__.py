"""Entry point: `claw ...` -> dispatch to lazily-loaded noun groups."""

from __future__ import annotations

import sys

# Force UTF-8 on stdout/stderr — Windows legacy cp1252 console chokes on help
# text that contains unicode arrows / em-dashes. Must run before `click` formats anything.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

import click

from claw.common.click_ext import LazyGroup, help_all_option

NOUNS = {
    "xlsx":     ("claw.xlsx", "group"),
    "docx":     ("claw.docx", "group"),
    "pptx":     ("claw.pptx", "group"),
    "pdf":      ("claw.pdf", "group"),
    "img":      ("claw.img", "group"),
    "media":    ("claw.media", "group"),
    "convert":  ("claw.convert", "group"),
    "email":    ("claw.email", "group"),
    "doc":      ("claw.doc", "group"),
    "sheet":    ("claw.sheet", "group"),
    "web":      ("claw.web", "group"),
    "html":     ("claw.html", "group"),
    "xml":      ("claw.xml", "group"),
    "browser":  ("claw.browser", "group"),
    "pipeline": ("claw.pipeline", "group"),
    "doctor":   ("claw.doctor", "doctor"),
    "completion": ("claw.completion", "completion"),
}


@click.command(cls=LazyGroup, lazy_commands=NOUNS, invoke_without_command=True,
               context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="claw")
@help_all_option()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """claw — CLI over openpyxl / fitz / Pillow / python-docx / pptx / lxml / pandoc / ffmpeg / magick.

    Every noun exposes verbs that absorb common glue. Run `claw <noun> --help`.
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command(name="help", hidden=True)
@click.argument("command", nargs=-1)
@click.pass_context
def help_alias(ctx: click.Context, command: tuple[str, ...]) -> None:
    """`claw help <cmd>` — equivalent to `claw <cmd> --help`."""
    if not command:
        click.echo(ctx.parent.get_help() if ctx.parent else "")
        return
    target: click.Command = cli
    parent_ctx = ctx.parent
    for c in command:
        if not isinstance(target, click.Group):
            click.echo(f"`{' '.join(command[:command.index(c)])}` has no subcommand `{c}`", err=True)
            sys.exit(2)
        cmd = target.get_command(ctx, c)
        if cmd is None:
            click.echo(f"unknown command: {' '.join(command)}", err=True)
            sys.exit(2)
        # Build a fresh context per step so the help output shows the full
        # invocation path (`claw xlsx from-csv`) instead of `claw help`.
        parent_ctx = click.Context(target, info_name=target.name, parent=parent_ctx)
        target = cmd
    target_ctx = click.Context(target, info_name=target.name, parent=parent_ctx)
    click.echo(target.get_help(target_ctx))


if __name__ == "__main__":
    cli()
