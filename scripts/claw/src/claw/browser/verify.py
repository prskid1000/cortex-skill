"""claw browser verify — poll /json/version until the debug port answers."""

from __future__ import annotations

import json
import sys
import time
from urllib.request import urlopen

import click

from claw.common import common_output_options, die, emit_json


def _poll(port: int, timeout_s: float) -> dict | None:
    deadline = time.monotonic() + timeout_s
    url = f"http://127.0.0.1:{port}/json/version"
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8"))
        except Exception:
            time.sleep(0.2)
    return None


@click.command(name="verify")
@click.option("--port", default=9222, type=int)
@click.option("--timeout", default=15, type=int, help="Seconds to wait.")
@common_output_options
def verify(port, timeout,
           force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Verify the Chrome DevTools debug port is responding."""
    if dry_run:
        click.echo(f"would probe http://127.0.0.1:{port}/json/version")
        return

    data = _poll(port, float(timeout))
    if not data:
        if as_json:
            emit_json({"port": port, "ok": False,
                       "error": f"no response within {timeout}s"})
        else:
            click.echo(f"debug port {port} did not respond within {timeout}s", err=True)
        sys.exit(4)

    if as_json:
        emit_json(data)
    elif not quiet:
        click.echo(json.dumps(data, indent=2))
