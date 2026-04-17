"""claw browser stop — terminate Edge/Chrome processes owning the debug port."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import click

from claw.common import EXIT_INPUT, common_output_options, die, emit_json


def _tasklist(image: str) -> list[int]:
    """Return PIDs of processes matching IMAGENAME."""
    try:
        proc = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {image}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, check=False,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return []
    pids: list[int] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("INFO:"):
            continue
        parts = [p.strip().strip('"') for p in line.split(",")]
        if len(parts) >= 2:
            try:
                pids.append(int(parts[1]))
            except ValueError:
                continue
    return pids


def _taskkill(pid: int, force_flag: bool = True) -> int:
    args = ["taskkill", "/PID", str(pid), "/T"]
    if force_flag:
        args.append("/F")
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    return proc.returncode


def _pid_listening_on(port: int) -> list[int]:
    """Best-effort: parse netstat to find PIDs listening on 127.0.0.1:<port>."""
    try:
        proc = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],
            capture_output=True, text=True, check=False,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return []
    pids: set[int] = set()
    needle = f":{port}"
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5 or "LISTENING" not in parts:
            continue
        local = parts[1]
        if not local.endswith(needle):
            continue
        try:
            pids.add(int(parts[-1]))
        except ValueError:
            continue
    return sorted(pids)


def _user_data_dir_from_port(port: int) -> str | None:
    """Probe CDP /json/version for userDataDir (Chromium exposes it on some builds)."""
    try:
        with urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.0) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8"))
    except (URLError, OSError, json.JSONDecodeError, TimeoutError):
        return None
    udd = data.get("userDataDir") or data.get("user-data-dir")
    if not udd:
        return None
    return udd


@click.command(name="stop")
@click.option("--all", "stop_all", is_flag=True,
              help="Kill every msedge.exe / chrome.exe process.")
@click.option("--port", default=None, type=int,
              help="Find process listening on this port and kill it.")
@click.option("--pid", default=None, type=int,
              help="Kill this specific PID.")
@click.option("--browser", type=click.Choice(["edge", "chrome", "both"]),
              default="both")
@click.option("--cleanup", is_flag=True,
              help="Remove the throwaway --user-data-dir after the process exits. "
                   "Ignored for default-profile launches.")
@common_output_options
def stop(stop_all, port, pid, browser, cleanup,
         force, backup, as_json, dry_run, quiet, verbose, mkdir) -> None:
    """Terminate browser debug processes."""
    picked = sum(1 for x in (stop_all, port, pid) if x)
    if picked != 1:
        die("exactly one of --all, --port, --pid required",
            code=EXIT_INPUT, as_json=as_json)

    cleanup_udd: str | None = None
    if cleanup and port:
        cleanup_udd = _user_data_dir_from_port(port)

    images: list[str] = []
    if browser in ("edge", "both"):
        images.append("msedge.exe")
    if browser in ("chrome", "both"):
        images.append("chrome.exe")

    targets: list[int] = []
    if pid:
        targets = [pid]
    elif port:
        listeners = _pid_listening_on(port)
        browser_pids: set[int] = set()
        for img in images:
            browser_pids.update(_tasklist(img))
        targets = [p for p in listeners if p in browser_pids]
        if not targets and listeners:
            targets = listeners
    elif stop_all:
        for img in images:
            targets.extend(_tasklist(img))

    if not targets:
        if as_json:
            emit_json({"killed": [], "reason": "no matching processes"})
        elif not quiet:
            click.echo("no matching processes")
        return

    if dry_run:
        click.echo(f"would kill PIDs: {targets}")
        return

    killed: list[dict] = []
    for p in targets:
        rc = _taskkill(p, force_flag=False)
        time.sleep(0.2)
        if rc != 0:
            rc = _taskkill(p, force_flag=True)
        killed.append({"pid": p, "returncode": rc})

    cleaned_path: str | None = None
    if cleanup and cleanup_udd:
        time.sleep(0.5)
        udd_path = Path(cleanup_udd)
        looks_throwaway = udd_path.exists() and "claw-browser-" in udd_path.name
        if looks_throwaway:
            try:
                shutil.rmtree(udd_path, ignore_errors=True)
                cleaned_path = str(udd_path)
            except OSError:
                cleaned_path = None

    if as_json:
        payload: dict = {"killed": killed}
        if cleanup:
            payload["cleanup"] = cleaned_path
        emit_json(payload)
    elif not quiet:
        for k in killed:
            status = "ok" if k["returncode"] == 0 else f"rc={k['returncode']}"
            click.echo(f"killed pid {k['pid']} ({status})")
        if cleaned_path:
            click.echo(f"removed user-data-dir {cleaned_path}")
