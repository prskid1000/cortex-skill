"""claw convert list-formats — enumerate pandoc input/output formats."""

from __future__ import annotations

import click

from claw.common import EXIT_SYSTEM, die, emit_json, require, run


def _list(direction: str) -> list[str]:
    flag = "--list-input-formats" if direction == "in" else "--list-output-formats"
    r = run("pandoc", flag)
    return [line.strip() for line in (r.stdout or "").splitlines() if line.strip()]


@click.command(name="list-formats")
@click.option("--direction", default="both",
              type=click.Choice(["in", "out", "both"]),
              help="Which format list to emit.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON instead of a table.")
def list_formats(direction: str, as_json: bool) -> None:
    """List pandoc input/output formats."""
    try:
        require("pandoc")
    except FileNotFoundError as e:
        die(str(e), code=EXIT_SYSTEM, hint="winget install JohnMacFarlane.Pandoc",
            as_json=as_json)

    try:
        inputs = _list("in") if direction in ("in", "both") else []
        outputs = _list("out") if direction in ("out", "both") else []
    except Exception as e:
        die(f"pandoc failed: {e}", code=EXIT_SYSTEM, as_json=as_json)

    if as_json:
        if direction == "in":
            emit_json(inputs)
        elif direction == "out":
            emit_json(outputs)
        else:
            emit_json({"input": inputs, "output": outputs})
        return

    if direction in ("in", "both"):
        click.echo("INPUT FORMATS")
        click.echo("-------------")
        for f in inputs:
            click.echo(f)
        if direction == "both":
            click.echo("")
    if direction in ("out", "both"):
        click.echo("OUTPUT FORMATS")
        click.echo("--------------")
        for f in outputs:
            click.echo(f)
