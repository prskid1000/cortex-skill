"""Windows-safe `gws` CLI invoker.

The `gws` CLI installs as a `.cmd` shim on Windows; `subprocess.run` in list
form can't execute `.cmd` without a shell, and `shell=True` breaks when the
JSON payload contains `|`, `&`, `>`, or `<` — those get interpreted by cmd.exe.

Workaround: resolve the shim to its JS entry point and invoke `node run-gws.js`
directly. List-form subprocess, no shell.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


_CACHED_NODE_ARGS: list[str] | None = None


def _resolve_node_args() -> list[str]:
    """Return `[node, run.js]` or `[gws.exe]` argv prefix."""
    global _CACHED_NODE_ARGS
    if _CACHED_NODE_ARGS is not None:
        return list(_CACHED_NODE_ARGS)

    gws_shim = shutil.which("gws")
    if not gws_shim:
        raise FileNotFoundError("gws not found on PATH")

    node = shutil.which("node")
    gws_path = Path(gws_shim).resolve()
    
    # Candidates for the actual binary or JS entry point
    candidates = [
        # Relative to shim (local install)
        gws_path.parent / "node_modules" / "@googleworkspace" / "cli" / "bin" / "gws.exe",
        gws_path.parent / "node_modules" / "@googleworkspace" / "cli" / "run.js",
        # Global install path discovered
        Path(r"C:\Users\prith\AppData\Local\nvm\v22.20.0\node_modules\@googleworkspace\cli\bin\gws.exe"),
        Path(r"C:\Users\prith\AppData\Local\nvm\v22.20.0\node_modules\@googleworkspace\cli\run.js"),
    ]
    
    for c in candidates:
        if c.exists():
            if c.suffix == ".exe":
                _CACHED_NODE_ARGS = [str(c)]
            elif node:
                _CACHED_NODE_ARGS = [node, str(c)]
            if _CACHED_NODE_ARGS:
                return list(_CACHED_NODE_ARGS)

    # Final fallback
    _CACHED_NODE_ARGS = [gws_shim]
    return list(_CACHED_NODE_ARGS)


def gws_run(*args: str, check: bool = True, **kwargs: Any) -> subprocess.CompletedProcess:
    """Run `gws <args...>` safely on Windows (no shell, no .cmd pitfall)."""
    argv = _resolve_node_args() + list(args)
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("encoding", "utf-8")
    return subprocess.run(argv, check=check, **kwargs)
