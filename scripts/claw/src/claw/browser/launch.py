"""claw browser launch — start Edge/Chrome with remote-debugging port."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import click

from claw.common import EXIT_INPUT, EXIT_SYSTEM, common_output_options, die, emit_json


EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def _find_binary(browser: str, override: str | None) -> str | None:
    if override:
        return override if Path(override).exists() else None
    name = "msedge" if browser == "edge" else "chrome"
    w = shutil.which(name)
    if w:
        return w
    candidates = EDGE_CANDIDATES if browser == "edge" else CHROME_CANDIDATES
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def _default_user_data_dir(browser: str) -> Path:
    local = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    if browser == "edge":
        return Path(local) / "Microsoft" / "Edge" / "User Data"
    return Path(local) / "Google" / "Chrome" / "User Data"


def _process_running(image: str) -> bool:
    try:
        proc = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {image}", "/NH"],
            capture_output=True, text=True, check=False,
        )
        return image.lower() in proc.stdout.lower()
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def _kill_process(image: str) -> None:
    subprocess.run(["taskkill", "/F", "/IM", image, "/T"],
                   capture_output=True, text=True, check=False)


def _poll_debug_port(port: int, timeout_s: float) -> dict | None:
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


def _probe_cdp(port: int) -> dict | None:
    """One-shot GET on /json/version; None if port is not a CDP endpoint."""
    try:
        with urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.0) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except (URLError, OSError, json.JSONDecodeError, TimeoutError):
        return None
    return None


def _port_free(port: int) -> bool:
    """True if we can bind 127.0.0.1:<port> right now."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
    except OSError:
        return False
    finally:
        s.close()
    return True


@click.command(name="launch")
@click.option("--profile", type=click.Choice(["default", "throwaway"]), default="default")
@click.option("--browser", type=click.Choice(["edge", "chrome"]), default="edge")
@click.option("--port", default=9222, type=int)
@click.option("--user-data-dir", "user_data_dir", default=None)
@click.option("--browser-path", "binary_override", default=None,
              help="Override auto-discovered browser binary path.")
@click.option("--kill-existing", "force_kill", is_flag=True,
              help="Kill existing browser processes before launching (default profile only).")
@click.option("--timeout", default=15, type=int, help="Seconds to wait for /json/version.")
@common_output_options
def launch(profile, browser, port, user_data_dir, binary_override,
           force_kill, timeout,
           force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Launch Edge or Chrome with --remote-debugging-port open."""
    binary = _find_binary(browser, binary_override)
    if not binary:
        die(f"{browser} binary not found; pass --browser-path",
            code=EXIT_SYSTEM, as_json=as_json)

    image = "msedge.exe" if browser == "edge" else "chrome.exe"

    if profile == "default":
        udd = Path(user_data_dir) if user_data_dir else _default_user_data_dir(browser)
        if _process_running(image):
            if not force_kill:
                die(f"{image} already running; pass --force to kill it "
                    f"(the user-data-dir is locked while any tab is open)",
                    code=EXIT_INPUT, as_json=as_json)
            _kill_process(image)
            time.sleep(1.0)
    else:
        udd = Path(user_data_dir) if user_data_dir else Path(
            tempfile.mkdtemp(prefix="claw-browser-"))

    args = [
        binary,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={udd}",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank",
    ]

    if dry_run:
        click.echo("would run: " + " ".join(f'"{a}"' if " " in a else a for a in args))
        return

    if not _port_free(port):
        cdp = _probe_cdp(port)
        if cdp is not None:
            die(f"port {port} already serves a CDP endpoint — reuse it or pick --port",
                code=4,
                hint=f"ws URL: {cdp.get('webSocketDebuggerUrl')}",
                as_json=as_json)
        else:
            die(f"port {port} is occupied by a non-CDP process",
                code=4,
                hint="pick a different --port (default 9222)",
                as_json=as_json)
        return

    try:
        proc = subprocess.Popen(args, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    except OSError as e:
        die(f"failed to spawn browser: {e}", code=EXIT_SYSTEM, as_json=as_json)

    version = _poll_debug_port(port, timeout)
    if not version:
        die(f"debug port {port} did not open within {timeout}s",
            code=4, hint="Try closing background browser processes or `--profile throwaway`",
            as_json=as_json)
        return

    result = {
        "pid": proc.pid,
        "port": port,
        "websocket_url": version.get("webSocketDebuggerUrl"),
        "profile": profile,
        "user_data_dir": str(udd),
        "browser": browser,
        "browser_version": version.get("Browser"),
    }

    if as_json:
        emit_json(result)
    elif not quiet:
        click.echo(f"launched {browser} pid={proc.pid} port={port}")
        click.echo(f"ws: {result['websocket_url']}")
