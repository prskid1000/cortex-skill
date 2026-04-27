#!/usr/bin/env python3
"""Claude Claw healthcheck — verify and (optionally) auto-install every dependency.

Usage:
    python ~/.claude/skills/claude-claw/scripts/healthcheck.py            # check only
    python ~/.claude/skills/claude-claw/scripts/healthcheck.py --install  # install missing
    python ~/.claude/skills/claude-claw/scripts/healthcheck.py --json

Exit codes:
    0 = everything passes
    1 = some failures (with --install, remaining failures after auto-fix)
    2 = critical failure (≥3 items failed AND --install could not recover)
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


HOME = Path.home()
SKILL_DIR = Path(__file__).resolve().parent.parent
CLAW_PKG = SKILL_DIR / "scripts" / "claw"
VENV_DIR = SKILL_DIR / ".venv"

RESULTS: dict[str, list[str]] = {"pass": [], "fail": [], "warn": [], "fixed": []}
INSTALL_MODE = False
UPGRADE_MODE = False  # implies INSTALL_MODE; forces fix_cmd even when detection PASSes


def venv_python() -> Path:
    """Path to the interpreter inside the skill-local venv."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def venv_scripts_dir() -> Path:
    return VENV_DIR / ("Scripts" if sys.platform == "win32" else "bin")


def venv_exe(name: str) -> Path:
    suffix = ".exe" if sys.platform == "win32" else ""
    return venv_scripts_dir() / f"{name}{suffix}"


def ensure_venv() -> bool:
    """Create .venv if missing; verify the interpreter runs.

    Bootstraps with sys.executable (the Python that launched healthcheck). Pip
    is upgraded once at creation. Returns False only on hard failure — callers
    gate further phases on the return value.
    """
    _print("\n=== 0. SKILL VENV ===")
    vpy = venv_python()
    if vpy.exists():
        ok, out = run_cmd([str(vpy), "--version"], timeout=10)
        if ok:
            check(f"venv at {VENV_DIR} ({out})", True)
            return True
        warn("venv", f"{vpy} exists but won't run — rerun with --recreate-venv")
        return False

    if sys.version_info < (3, 11):
        check("venv bootstrap", False,
              hint=f"claw requires Python >=3.11; this interpreter is {sys.version.split()[0]}")
        return False

    if not INSTALL_MODE:
        check("venv present", False,
              hint=f"rerun with --install to create {VENV_DIR}")
        return False

    _print(f"  [CREATE] {sys.executable} -m venv {VENV_DIR} --upgrade-deps")
    try:
        r = subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR), "--upgrade-deps"],
            capture_output=True, text=True, timeout=300,
        )
    except Exception as e:
        check("venv bootstrap", False, hint=f"venv creation crashed: {e}")
        return False
    if r.returncode != 0:
        check("venv bootstrap", False,
              hint=f"venv creation failed: {(r.stderr or r.stdout)[:300]}")
        return False
    if not vpy.exists():
        check("venv bootstrap", False, hint=f"{vpy} missing after successful venv -m")
        return False
    RESULTS["fixed"].append(f"venv at {VENV_DIR}")
    _print(f"  [FIXED] venv at {VENV_DIR}")
    return True


def recreate_venv() -> None:
    """Remove the venv tree before ensure_venv rebuilds it."""
    if VENV_DIR.exists():
        _print(f"  [RECREATE] removing {VENV_DIR}")
        shutil.rmtree(VENV_DIR, ignore_errors=True)


def _print(msg: str) -> None:
    # Windows legacy console is cp1252 by default and chokes on unicode arrows.
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"), flush=True)


# Force UTF-8 on stdout/stderr where Python supports it (PY3.7+).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass


def check(name: str, ok: bool, *, fix_cmd: str | list[str] | None = None,
          hint: str | None = None) -> bool:
    """Record a check. If INSTALL_MODE and fix_cmd given, attempt the fix."""
    if ok:
        RESULTS["pass"].append(name)
        _print(f"  [PASS] {name}")
        return True
    RESULTS["fail"].append(name)
    _print(f"  [FAIL] {name}")
    if hint:
        _print(f"         hint: {hint}")
    if fix_cmd and INSTALL_MODE:
        cmd_display = fix_cmd if isinstance(fix_cmd, str) else " ".join(fix_cmd)
        _print(f"         fix:  {cmd_display}")
        try:
            if isinstance(fix_cmd, str):
                r = subprocess.run(fix_cmd, shell=True, capture_output=True,
                                   text=True, timeout=600)
            else:
                r = subprocess.run(fix_cmd, capture_output=True,
                                   text=True, timeout=600)
            output = (r.stdout or "") + (r.stderr or "")
            already_installed = (
                "already installed" in output.lower()
                or "no applicable upgrade" in output.lower()
                or "no available upgrade" in output.lower()
            )
            if r.returncode == 0 or already_installed:
                RESULTS["fixed"].append(name)
                try:
                    RESULTS["fail"].remove(name)
                except ValueError:
                    pass
                suffix = " (already installed)" if already_installed and r.returncode != 0 else ""
                _print(f"         [FIXED] {name}{suffix}")
                return True
            _print(f"         [FIX FAILED] {r.stderr[:300] or r.stdout[:300]}")
        except subprocess.TimeoutExpired:
            _print("         [FIX TIMEOUT]")
        except Exception as e:
            _print(f"         [FIX ERROR] {e}")
    elif fix_cmd:
        cmd_display = fix_cmd if isinstance(fix_cmd, str) else " ".join(fix_cmd)
        _print(f"         install: {cmd_display}")
    return False


def warn(name: str, msg: str) -> None:
    RESULTS["warn"].append(f"{name}: {msg}")
    _print(f"  [WARN] {name}: {msg}")


def run_cmd(cmd: list[str] | str, timeout: int = 10) -> tuple[bool, str]:
    try:
        if isinstance(cmd, str):
            r = subprocess.run(cmd, shell=True, capture_output=True,
                               text=True, timeout=timeout)
        else:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout or r.stderr).strip()
    except Exception:
        return False, ""


# Ensure ~/.local/bin is on PATH for claw / clickup
local_bin = str(HOME / ".local" / "bin")
if local_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = local_bin + os.pathsep + os.environ.get("PATH", "")


def refresh_path_from_registry() -> None:
    """Refresh the current process PATH from the Windows registry.

    winget installs update HKCU/HKLM Environment but child shells don't see it
    until respawn. Re-read both scopes and merge into os.environ["PATH"].
    """
    if sys.platform != "win32":
        return
    try:
        import winreg  # type: ignore[import-not-found]
    except ImportError:
        return
    paths: list[str] = []
    for root, subkey in [
        (winreg.HKEY_LOCAL_MACHINE,
         r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
        (winreg.HKEY_CURRENT_USER, "Environment"),
    ]:
        try:
            with winreg.OpenKey(root, subkey) as k:
                val, _ = winreg.QueryValueEx(k, "Path")
                if val:
                    paths.extend(p for p in val.split(";") if p)
        except OSError:
            continue
    # preserve any process-local additions (like ~/.local/bin) at the front
    existing = [p for p in os.environ.get("PATH", "").split(os.pathsep) if p]
    combined: list[str] = []
    seen: set[str] = set()
    for p in existing + paths:
        key = p.lower().rstrip("\\/")
        if key and key not in seen:
            seen.add(key)
            combined.append(p)
    os.environ["PATH"] = os.pathsep.join(combined)


# Common winget install directories we scan as a secondary probe when `shutil.which`
# misses — for instance when the installer hasn't broadcast WM_SETTINGCHANGE yet.
WINGET_FALLBACKS = {
    "qpdf":      [r"C:\Program Files\qpdf*\bin\qpdf.exe"],
    "tesseract": [r"C:\Program Files\Tesseract-OCR\tesseract.exe"],
    "exiftool":  [r"C:\Program Files\ExifTool\exiftool.exe",
                  r"C:\Program Files (x86)\ExifTool\exiftool.exe"],
    "pandoc":    [r"C:\Program Files\Pandoc\pandoc.exe"],
    "ffmpeg":    [r"C:\Program Files\Gyan.FFmpeg*\ffmpeg-*\bin\ffmpeg.exe"],
    "magick":    [r"C:\Program Files\ImageMagick-*\magick.exe"],
}


def locate(name: str) -> str | None:
    """shutil.which with winget-path fallback (+ glob expansion for versioned dirs)."""
    import glob
    path = shutil.which(name)
    if path:
        return path
    for pattern in WINGET_FALLBACKS.get(name, []):
        matches = glob.glob(pattern)
        if matches:
            return matches[-1]  # latest by lex sort
    return None


# ---------------------------------------------------------------------------
# 1. Python packages (all claw extras)
# ---------------------------------------------------------------------------

PACKAGES: list[tuple[str, str]] = [
    # (pip name, import name)
    ("openpyxl",       "openpyxl"),
    ("python-docx",    "docx"),
    ("python-pptx",    "pptx"),
    ("pymupdf",        "fitz"),
    ("pypdf",          "pypdf"),
    ("pdfplumber",     "pdfplumber"),
    ("reportlab",      "reportlab"),
    ("qrcode",         "qrcode"),
    ("Pillow",         "PIL"),
    ("lxml",           "lxml"),
    ("beautifulsoup4", "bs4"),
    ("soupsieve",      "soupsieve"),
    ("trafilatura",    "trafilatura"),
    ("httpx",          "httpx"),
    ("networkx",       "networkx"),
    ("pyyaml",         "yaml"),
    ("click",          "click"),
    ("rich",           "rich"),
]


def _probe_packages_in_venv() -> tuple[set[str], set[str]]:
    """Return (present, missing) pip names by importing each module in the venv.

    One subprocess call does the whole sweep — avoids fork-per-package overhead.
    If the venv interpreter is unavailable, everything counts as missing.
    """
    vpy = venv_python()
    if not vpy.exists():
        return set(), {pip for pip, _ in PACKAGES}
    probe = "\n".join(
        f"try:\n  import {imp}\n  print('OK:{pip}')\nexcept Exception:\n  print('NO:{pip}')"
        for pip, imp in PACKAGES
    )
    try:
        r = subprocess.run([str(vpy), "-c", probe],
                           capture_output=True, text=True, timeout=60)
    except Exception:
        return set(), {pip for pip, _ in PACKAGES}
    present, missing = set(), set()
    for line in (r.stdout or "").splitlines():
        if line.startswith("OK:"):
            present.add(line[3:])
        elif line.startswith("NO:"):
            missing.add(line[3:])
    # Packages with no response at all (stderr/crash) → treat as missing.
    seen = present | missing
    for pip, _ in PACKAGES:
        if pip not in seen:
            missing.add(pip)
    return present, missing


def check_python_packages() -> None:
    _print("\n=== 1. PYTHON PACKAGES (venv) ===")
    if not venv_python().exists():
        warn("python packages", "venv missing — skipping (rerun --install)")
        return
    present, missing = _probe_packages_in_venv()
    for pip_name, _ in PACKAGES:
        if pip_name in present:
            check(pip_name, True)
        else:
            RESULTS["fail"].append(pip_name)
            _print(f"  [FAIL] {pip_name}")

    # --upgrade forces a refresh of everything; --install only fixes missing.
    targets = sorted(missing | present) if UPGRADE_MODE else sorted(missing)
    if targets and INSTALL_MODE:
        cmd = [str(venv_python()), "-m", "pip", "install",
               "--no-cache-dir", "--quiet", "--upgrade", *targets]
        label = "UPGRADE" if UPGRADE_MODE else "BATCH FIX"
        _print(f"  [{label}] (venv) pip install --upgrade {' '.join(targets)}")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if r.returncode == 0:
                for pkg in targets:
                    RESULTS["fixed"].append(pkg)
                    try:
                        RESULTS["fail"].remove(pkg)
                    except ValueError:
                        pass
                _print(f"  [FIXED] {len(targets)} package(s)")
            else:
                _print(f"  [FIX FAILED] {r.stderr[:300] or r.stdout[:300]}")
        except subprocess.TimeoutExpired:
            _print("  [FIX TIMEOUT] pip install exceeded 10 min")


# ---------------------------------------------------------------------------
# 2. CLI tools (winget-install where possible)
# ---------------------------------------------------------------------------

# Per-tool installer-silent-flags — winget's --silent only hides winget's own UI;
# some packages (Inno Setup, NSIS) run their own wizard unless we pass --custom.
CLI_TOOLS: list[tuple[str, str, str | None, str | None]] = [
    # (tool, verify command, winget id, --custom installer flags or None)
    ("git",       "git --version",     "Git.Git",                 None),
    ("node",      "node --version",    "OpenJS.NodeJS",           None),
    ("npm",       "npm --version",     None,                      None),  # comes with node
    ("npx",       "npx --version",     None,                      None),
    ("ffmpeg",    "ffmpeg -version",   "Gyan.FFmpeg",             None),
    ("ffprobe",   "ffprobe -version",  None,                      None),  # ships with ffmpeg
    ("pandoc",    "pandoc --version",  "JohnMacFarlane.Pandoc",   None),
    ("magick",    "magick --version",  "ImageMagick.ImageMagick", None),
    ("qpdf",      "qpdf --version",    "qpdf.qpdf",               None),
    # UB-Mannheim uses Inno Setup — /VERYSILENT bypasses the installer wizard.
    ("tesseract", "tesseract --version", "UB-Mannheim.TesseractOCR",
                                                                "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART"),
    ("exiftool",  "exiftool -ver",     "OliverBetz.ExifTool",     None),
    ("gws",       "gws --version",     None,                      None),
    ("clickup",   "clickup version",   None,                      None),
]


def _install_tesseract_interactive() -> None:
    """Download UB-Mannheim Tesseract installer and launch it interactively.

    Winget's --silent doesn't bypass their Inno-Setup license prompt, and
    /VERYSILENT via --custom returns non-zero for reasons that elude diagnosis.
    Instead: spawn the installer's normal UI, block until the user completes
    the wizard, then verify via shutil.which / PATH scan.
    """
    import json as _json
    import urllib.request
    import tempfile

    _print("         downloading UB-Mannheim tesseract setup from GitHub...")
    api = "https://api.github.com/repos/UB-Mannheim/tesseract/releases/latest"
    req = urllib.request.Request(api, headers={"User-Agent": "claw-healthcheck"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = _json.loads(r.read())
    setup = next((a for a in data.get("assets", [])
                  if "w64-setup" in a["name"] and a["name"].endswith(".exe")), None)
    if not setup:
        raise RuntimeError("no w64-setup asset in latest UB-Mannheim release")

    with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as tmp:
        tmp_path = tmp.name
    with urllib.request.urlopen(setup["browser_download_url"], timeout=300) as r:
        Path(tmp_path).write_bytes(r.read())

    _print(f"         launching installer: {setup['name']}")
    _print("         >>> accept the UAC prompt and complete the wizard in the new window <<<")
    try:
        # Installer needs admin (writes to Program Files). PowerShell's Start-Process
        # -Verb RunAs triggers UAC; -Wait blocks until the installer process exits.
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-Command",
             f"Start-Process -FilePath '{tmp_path}' -Verb RunAs -Wait -PassThru | "
             "Select-Object -ExpandProperty ExitCode"],
            timeout=1800, capture_output=True, text=True,
        )
        _print(f"         installer exited with code {(r.stdout or '').strip() or r.returncode}")
    finally:
        try:
            Path(tmp_path).unlink()
        except OSError:
            pass

    refresh_path_from_registry()
    if not locate("tesseract"):
        raise RuntimeError("installer finished but `tesseract` still not on PATH")


def _download_clickup() -> None:
    """Pull the latest clickup-cli Windows binary from GitHub releases."""
    import json as _json
    import urllib.request
    import zipfile
    import io

    api = "https://api.github.com/repos/triptechtravel/clickup-cli/releases/latest"
    req = urllib.request.Request(api, headers={"User-Agent": "claw-healthcheck"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = _json.loads(r.read())
    assets = data.get("assets", [])
    want = [a for a in assets
            if "windows" in a["name"].lower() or "win" in a["name"].lower()
            or a["name"].endswith(".exe")]
    if not want:
        raise RuntimeError("no Windows asset in latest release")
    url = want[0]["browser_download_url"]
    dst = HOME / ".local" / "bin"
    dst.mkdir(parents=True, exist_ok=True)

    with urllib.request.urlopen(url, timeout=120) as r:
        payload = r.read()
    if url.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            for name in zf.namelist():
                if name.lower().endswith(("clickup.exe", "clickup")):
                    with zf.open(name) as src, (dst / "clickup.exe").open("wb") as out:
                        out.write(src.read())
                    break
    else:
        (dst / "clickup.exe").write_bytes(payload)


def check_cli_tools() -> None:
    _print("\n=== 2. CLI TOOLS ===")
    have_winget = shutil.which("winget") is not None
    for name, verify, winget_id, custom_args in CLI_TOOLS:
        # Fast path: locate() is ~1ms and scans winget install dirs as a fallback
        # for when PATH hasn't been refreshed since a winget install.
        path = locate(name)
        if path and not UPGRADE_MODE:
            check(name, True)
            continue
        if path and UPGRADE_MODE:
            # Installed — record pass, then fall through to fire the upgrade path.
            RESULTS["pass"].append(name)
            _print(f"  [PASS] {name} (upgrading)")
            if winget_id and shutil.which("winget"):
                parts = [
                    f"winget upgrade -e --id {winget_id} --source winget",
                    "--accept-package-agreements --accept-source-agreements",
                    "--silent --disable-interactivity --include-unknown",
                ]
                if custom_args:
                    parts.append(f'--custom "{custom_args}"')
                fix = " ".join(parts)
                try:
                    subprocess.run(fix, shell=True, capture_output=True, text=True, timeout=600)
                    _print(f"         [UPGRADED] {name}")
                    RESULTS["fixed"].append(name)
                except Exception:
                    pass
            elif name == "gws":
                subprocess.run("npm install -g @googleworkspace/cli", shell=True, capture_output=True, timeout=300)
                _print(f"         [UPGRADED] {name}")
                RESULTS["fixed"].append(name)
            elif name == "clickup":
                try:
                    _download_clickup()
                    _print(f"         [UPGRADED] {name}")
                    RESULTS["fixed"].append(name)
                except Exception as e:
                    _print(f"         [UPGRADE FAILED] {e}")
            continue

        # Tesseract gets special handling FIRST — winget's silent install hits an
        # Inno-Setup EULA wall that neither --silent nor --custom /VERYSILENT bypasses.
        # Run the official installer interactively instead.
        if name == "tesseract":
            if INSTALL_MODE:
                try:
                    _install_tesseract_interactive()
                    RESULTS["fixed"].append("tesseract")
                    _print("  [FIXED] tesseract (interactive wizard)")
                    continue
                except Exception as e:
                    _print(f"  [FIX FAILED] tesseract: {e}")
                    RESULTS["fail"].append("tesseract")
                    continue
            check(name, False, fix_cmd=None,
                  hint="will download UB-Mannheim setup.exe and launch its wizard")
            continue

        # Not on PATH — build an install command as a LIST (preserves quoting of --custom)
        if winget_id and have_winget:
            fix_list = [
                "winget", "install", "-e", "--id", winget_id, "--source", "winget",
                "--accept-package-agreements", "--accept-source-agreements",
                "--silent", "--disable-interactivity",
            ]
            if custom_args:
                fix_list += ["--custom", custom_args]
            fix = fix_list  # list — the check() helper handles both forms
            hint = f"winget install --id {winget_id}"
        elif name == "gws":
            # Real npm package is @googleworkspace/cli (see common/gws_util.py)
            fix = "npm install -g @googleworkspace/cli"
            hint = "npm install -g @googleworkspace/cli"
        elif name == "clickup":
            # Auto-download the latest Windows binary from GitHub releases.
            if INSTALL_MODE:
                try:
                    _download_clickup()
                    RESULTS["fixed"].append("clickup")
                    _print("  [FIXED] clickup (downloaded from GitHub releases)")
                    continue
                except Exception as e:
                    _print(f"  [FIX FAILED] clickup: {e}")
            fix = None
            hint = "healthcheck will download the latest clickup-cli Windows binary from GitHub"
        elif name in ("npm", "npx", "ffprobe"):
            fix = None
            hint = "installed with its parent (node / ffmpeg)"
        else:
            fix = None
            hint = None
        check(name, False, fix_cmd=fix, hint=hint)


# ---------------------------------------------------------------------------
# 3. Google Workspace auth
# ---------------------------------------------------------------------------

def check_gws_auth() -> None:
    _print("\n=== 3. GWS AUTH ===")
    if not shutil.which("gws"):
        warn("gws auth", "gws CLI not installed — skipping auth check")
        return
    ok, output = run_cmd("gws auth status", timeout=15)
    if ok:
        check("gws authenticated", True)
    else:
        warn("gws auth", "not authenticated — run: gws auth login")


# ---------------------------------------------------------------------------
# 4. claw package itself
# ---------------------------------------------------------------------------

def _foreign_python_candidates() -> list[Path]:
    """Return Python interpreters that could host a stray `claw` install.

    Excludes the skill venv. Scans the launcher, PATH-resolved `python` /
    `python3`, and pyenv version dirs — these are the realistic places a past
    `pip install` could have leaked `claw` outside its sandbox.
    """
    venv_py = venv_python().resolve() if venv_python().exists() else None
    seen: set[Path] = set()
    out: list[Path] = []

    def _add(p: Path | None) -> None:
        if not p:
            return
        try:
            rp = p.resolve()
        except OSError:
            return
        if not rp.exists() or rp.is_dir():
            return
        if venv_py and rp == venv_py:
            return
        if rp in seen:
            return
        seen.add(rp)
        out.append(rp)

    _add(Path(sys.executable))
    for name in ("python", "python3", "python.exe"):
        w = shutil.which(name)
        if w:
            _add(Path(w))

    if sys.platform == "win32":
        pyenv_root = HOME / ".pyenv" / "pyenv-win" / "versions"
        if pyenv_root.exists():
            for ver_dir in pyenv_root.iterdir():
                _add(ver_dir / "python.exe")
    else:
        pyenv_root = HOME / ".pyenv" / "versions"
        if pyenv_root.exists():
            for ver_dir in pyenv_root.iterdir():
                _add(ver_dir / "bin" / "python")

    return out


def _claw_install_location(py: Path) -> str | None:
    """site-packages directory where `claw` is installed for this interpreter, else None.

    Used as a dedup key — pyenv-win exposes the same Python via a `.bat` shim,
    a `python3.bat` shim, and the direct `python.exe`, all of which point at
    one site-packages. We don't want to "uninstall" the same install three times.
    """
    try:
        r = subprocess.run([str(py), "-m", "pip", "show", "claw"],
                           capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return None
        for line in r.stdout.splitlines():
            if line.startswith("Location:"):
                return line.split(":", 1)[1].strip().lower()
        return None
    except Exception:
        return None


def check_claw_contamination() -> None:
    """Detect (and in --install mode, uninstall) stray `claw` installs.

    CLAUDE.md scopes claw to the skill venv only. Strays in pyenv / system
    Python typically lack the runtime extras (people pip-install the package
    without `[all]`), producing `ModuleNotFoundError: No module named 'click'`
    when PATH resolves to that interpreter's shim. Even when the deps are
    present, PATH ordering can mask the official `~/.local/bin/claw.bat`, so
    the foreign install has to go.
    """
    seen: dict[str, Path] = {}  # install location -> first interpreter found
    for py in _foreign_python_candidates():
        loc = _claw_install_location(py)
        if loc and loc not in seen:
            seen[loc] = py
    if not seen:
        return
    for loc, py in seen.items():
        label = f"foreign claw at {loc}"
        if INSTALL_MODE:
            try:
                r = subprocess.run([str(py), "-m", "pip", "uninstall", "-y", "claw"],
                                   capture_output=True, text=True, timeout=120)
                ok = r.returncode == 0
            except Exception:
                ok = False
            if ok:
                RESULTS["fixed"].append(label)
                _print(f"  [FIXED] uninstalled stray claw from {py}")
                continue
        RESULTS["fail"].append(label)
        _print(f"  [FAIL] {label}")
        _print(f"         hint: \"{py}\" -m pip uninstall -y claw")


def _verify_claw_resolution() -> None:
    """Confirm `claw` on PATH resolves to the venv shim, not something else.

    An earlier PATH entry can shadow `~/.local/bin/claw.bat` even after the
    shim is written. Surface that as a warning so the user knows to reorder
    PATH instead of silently using a stale binary.
    """
    bindir = HOME / ".local" / "bin"
    expected = bindir / ("claw.bat" if sys.platform == "win32" else "claw")
    if not expected.exists():
        return
    if sys.platform == "win32":
        try:
            r = subprocess.run(["where.exe", "claw"], capture_output=True,
                               text=True, timeout=10)
            lines = [ln for ln in (r.stdout or "").splitlines() if ln.strip()]
            actual = Path(lines[0]).resolve() if lines else None
        except Exception:
            return
    else:
        p = shutil.which("claw")
        actual = Path(p).resolve() if p else None

    if actual is None:
        warn("claw on PATH",
             f"shim exists at {expected} but PATH lookup found nothing — "
             f"prepend {bindir} to PATH")
        return
    if actual != expected.resolve():
        warn("claw on PATH",
             f"resolves to {actual}, not {expected} — "
             f"move {bindir} earlier on PATH to fix")
        return
    check(f"claw on PATH -> {expected.name}", True)


def _ensure_claw_shim() -> None:
    """Write ~/.local/bin/claw.bat (Windows) or claw symlink (POSIX) pointing at venv entry point.

    The shim keeps `claw` on PATH without leaking the rest of the venv's
    Scripts dir. ~/.local/bin is already prepended to PATH at module load.
    """
    target = venv_exe("claw")
    if not target.exists():
        warn("claw shim", f"venv entry point {target} missing — skipping shim")
        return
    bindir = HOME / ".local" / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        shim = bindir / "claw.bat"
        body = f'@echo off\r\n"{target}" %*\r\n'.encode("utf-8")
        if shim.exists() and shim.read_bytes() == body:
            check(f"claw shim {shim}", True)
            return
        shim.write_bytes(body)
        RESULTS["fixed"].append(f"claw shim {shim}")
        _print(f"  [FIXED] wrote {shim} -> {target}")
    else:
        shim = bindir / "claw"
        if shim.is_symlink() and shim.resolve() == target.resolve():
            check(f"claw shim {shim}", True)
            return
        if shim.exists() or shim.is_symlink():
            shim.unlink()
        shim.symlink_to(target)
        shim.chmod(0o755)
        RESULTS["fixed"].append(f"claw shim {shim}")
        _print(f"  [FIXED] linked {shim} -> {target}")


def check_claw_package() -> None:
    _print("\n=== 4. CLAW PACKAGE (venv) ===")
    vpy = venv_python()
    if not vpy.exists():
        warn("claw", "venv missing — skipping")
        return

    check_claw_contamination()

    probe = subprocess.run(
        [str(vpy), "-c",
         "import claw; print(getattr(claw,'__version__','?'))"],
        capture_output=True, text=True, timeout=30,
    )
    if probe.returncode == 0:
        check(f"claw {probe.stdout.strip()} (venv)", True)
    else:
        install = [str(vpy), "-m", "pip", "install", "--no-cache-dir",
                   "-e", f"{CLAW_PKG}[all]"]
        check("claw package", False, fix_cmd=install,
              hint=f"pip install -e {CLAW_PKG}[all] into {VENV_DIR}")

    _ensure_claw_shim()
    _verify_claw_resolution()


# ---------------------------------------------------------------------------
# 5. MCP servers (config-level, can't auto-install)
# ---------------------------------------------------------------------------

MCP_TEMPLATES = {
    "mcp_server_mysql": {
        "type": "stdio",
        "command": "npx",
        "args": ["@benborla29/mcp-server-mysql"],
        "env": {
            "MYSQL_HOST": "127.0.0.1",
            "MYSQL_PORT": "3306",
            "MYSQL_USER": "root",
            "MYSQL_PASS": "CHANGE_ME",
            "MYSQL_DB": "CHANGE_ME",
            "ALLOW_INSERT_OPERATION": "true",
            "ALLOW_UPDATE_OPERATION": "true",
            "ALLOW_DELETE_OPERATION": "false",
        },
    },
}


def check_mcp_servers() -> None:
    _print("\n=== 5. MCP SERVERS ===")
    cfg = HOME / ".claude.json"
    if not cfg.exists():
        # create minimal config if missing and in install mode
        if INSTALL_MODE:
            cfg.write_text(json.dumps({"mcpServers": {}}, indent=2), encoding="utf-8")
            _print(f"  [FIXED] created {cfg}")
        else:
            warn("~/.claude.json", f"not found — rerun with --install to create it")
            return
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        warn("~/.claude.json", f"invalid JSON: {e}")
        return
    if not isinstance(data, dict):
        warn("~/.claude.json", "top level is not an object — skipping")
        return
    servers = data.setdefault("mcpServers", {})

    dirty = False
    for name, template in MCP_TEMPLATES.items():
        if name in servers:
            check(f"MCP: {name}", True)
            continue
        if INSTALL_MODE:
            # write a backup once
            if not dirty:
                backup = cfg.with_suffix(".json.bak")
                backup.write_text(cfg.read_text(encoding="utf-8"), encoding="utf-8")
                _print(f"         backed up {cfg} -> {backup}")
            servers[name] = template
            dirty = True
            RESULTS["fixed"].append(f"MCP: {name}")
            _print(f"  [FIXED] MCP: {name} (placeholder env vars — edit before use)")
        else:
            check(f"MCP: {name}", False,
                  hint=f"rerun with --install to inject a placeholder entry")

    if dirty:
        cfg.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # chrome-devtools — first-party plugin from the Anthropic marketplace. Two install paths:
    #   (1) MCP-server only (automated here):  claude mcp add chrome-devtools npx chrome-devtools-mcp@latest
    #   (2) Plugin (MCP + skills, manual):     /plugin marketplace add ChromeDevTools/chrome-devtools-mcp
    #                                          /plugin install chrome-devtools-mcp
    # Path (1) is used by --install because it's scriptable; the plugin path bundles extra skills
    # (a11y-debugging, LCP optimization, troubleshooting) and must be run from inside Claude Code.
    has_cdm = any("chrome-devtools" in k for k in servers) or _has_cdm_plugin()
    if has_cdm:
        check("MCP: chrome-devtools", True)
    elif INSTALL_MODE and shutil.which("claude"):
        _print("  [FIX] claude mcp add chrome-devtools npx chrome-devtools-mcp@latest")
        try:
            r = subprocess.run(
                ["claude", "mcp", "add", "chrome-devtools",
                 "npx", "chrome-devtools-mcp@latest"],
                capture_output=True, text=True, timeout=60,
            )
            if r.returncode == 0 or "already" in (r.stdout + r.stderr).lower():
                RESULTS["fixed"].append("MCP: chrome-devtools")
                _print("  [FIXED] MCP: chrome-devtools")
            else:
                _print(f"  [FIX FAILED] {(r.stderr or r.stdout)[:300]}")
                RESULTS["fail"].append("MCP: chrome-devtools")
        except Exception as e:
            _print(f"  [FIX ERROR] {e}")
            RESULTS["fail"].append("MCP: chrome-devtools")
    else:
        check("MCP: chrome-devtools", False,
              hint="rerun with --install (uses `claude mcp add chrome-devtools npx chrome-devtools-mcp@latest`)")


def _has_cdm_plugin() -> bool:
    """Authoritative check: does `claude mcp list` report chrome-devtools?

    Falls back to scanning plugin marker dirs when the claude CLI is unavailable.
    """
    if shutil.which("claude"):
        try:
            r = subprocess.run(["claude", "mcp", "list"],
                               capture_output=True, text=True, timeout=30)
            if "chrome-devtools" in (r.stdout + r.stderr).lower():
                return True
        except Exception:
            pass
    # Fallback: plugin marker files shipped with Claude Code
    candidates = [
        HOME / ".claude" / "plugins" / "chrome-devtools-mcp",
        HOME / ".claude" / "plugins" / "enabled" / "chrome-devtools-mcp",
    ]
    return any(p.exists() for p in candidates)


# ---------------------------------------------------------------------------
# 6. LSP plugins & Windows fix
# ---------------------------------------------------------------------------
# Claude Code's LSP tool spawns language servers via libuv uv_spawn. On Windows
# libuv >= 1.49 (Node 22+) refuses to launch .cmd / .bat shims directly, so we
# rewrite each lspServers entry in marketplace.json to invoke via `cmd /c`.

LSP_MARKETPLACE = (HOME / ".claude" / "plugins" / "marketplaces"
                   / "claude-plugins-official" / ".claude-plugin" / "marketplace.json")

# Per-server: list of candidate shim paths (first hit wins), and trailing stdio flag (None for jdtls).
LSP_SERVERS: dict[str, tuple[list[Path], str | None]] = {
    "typescript": ([Path("C:/nvm4w/nodejs/typescript-language-server.cmd"),
                    HOME / "AppData/Roaming/npm/typescript-language-server.cmd"], "--stdio"),
    "pyright":    ([Path("C:/nvm4w/nodejs/pyright-langserver.cmd"),
                    HOME / "AppData/Roaming/npm/pyright-langserver.cmd"], "--stdio"),
    "jdtls":      ([HOME / ".local/bin/jdtls.bat", HOME / ".local/bin/jdtls.cmd"], None),
}


def check_lsp_plugins() -> None:
    _print("\n=== 6. LSP PLUGINS (Windows fix) ===")
    _print("  Enable via `/plugin` in Claude Code: pyright-lsp, typescript-lsp, jdtls-lsp.")

    if sys.platform != "win32":
        return

    if not LSP_MARKETPLACE.exists():
        warn("marketplace.json", f"not found at {LSP_MARKETPLACE} — enable the LSP plugins first")
        return

    try:
        marketplace = json.loads(LSP_MARKETPLACE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        warn("marketplace.json", f"unreadable JSON: {e}")
        return

    mutated = False
    for server, (candidates, stdio) in LSP_SERVERS.items():
        shim = next((p for p in candidates if p.exists()), None)
        if not shim:
            check(f"{server} shim present", False,
                  hint="install the LSP binary — tried: " + ", ".join(map(str, candidates)))
            continue

        desired = ["/c", str(shim).replace("/", "\\")] + ([stdio] if stdio else [])
        entry = next((p["lspServers"][server] for p in marketplace.get("plugins", [])
                      if server in (p.get("lspServers") or {})), None)
        if entry is None:
            warn(server, "not found in marketplace.json")
            continue

        if entry.get("command") == "cmd" and entry.get("args") == desired:
            check(f"{server} already patched ({shim.name})", True)
        else:
            entry["command"] = "cmd"
            entry["args"] = desired
            mutated = True
            check(f"{server} -> cmd /c {shim.name}", True)
            RESULTS["fixed"].append(f"lsp:{server} patched to cmd /c {shim}")

    if mutated:
        backup = LSP_MARKETPLACE.with_suffix(".json.bak")
        if not backup.exists():
            backup.write_text(LSP_MARKETPLACE.read_text(encoding="utf-8"), encoding="utf-8")
        LSP_MARKETPLACE.write_text(
            json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        _print("  marketplace.json updated - restart Claude Code for LSP changes to take effect.")


# ---------------------------------------------------------------------------
# 7. CLAUDE.md integration
# ---------------------------------------------------------------------------


def check_claude_md_integration() -> None:
    _print("\n=== 7. ~/.claude/CLAUDE.md BLOCK ===")
    cm = HOME / ".claude" / "CLAUDE.md"
    patcher = CLAW_PKG.parent / "patchers" / "md-section-patcher.py"
    block = SKILL_DIR / "references" / "patchers" / "CLAUDE.patch"
    if not cm.exists():
        warn("~/.claude/CLAUDE.md", "not found — create it and run the patcher")
        return
    if not block.exists():
        warn("CLAUDE.patch", f"source missing at {block}")
        return

    desired_body = block.read_text(encoding="utf-8").strip()
    text = cm.read_text(encoding="utf-8")
    begin_marker = "<!-- claude-claw:begin -->"
    end_marker = "<!-- claude-claw:end -->"

    drift = False
    if begin_marker in text and end_marker in text:
        b = text.index(begin_marker) + len(begin_marker)
        e = text.index(end_marker)
        current_body = text[b:e].strip()
        if current_body == desired_body:
            check("claude-claw block in sync", True)
            return
        drift = True

    fix = [sys.executable, str(patcher), "apply",
           "--target", str(cm), "--section", "claude-claw",
           "--source", str(block)]
    label = "claude-claw block drift" if drift else "claude-claw block present"
    hint = "block content differs from CLAUDE.patch — re-apply" if drift \
           else "inject the canonical block via md-section-patcher.py"
    check(label, False, fix_cmd=fix, hint=hint)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    global INSTALL_MODE
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0] if __doc__ else "")
    ap.add_argument("--install", action="store_true",
                    help="Install every missing dependency (fast — skips already-present).")
    ap.add_argument("--upgrade", action="store_true",
                    help="Force upgrade everything (pip --upgrade, winget upgrade, re-download clickup/npm). Implies --install.")
    ap.add_argument("--recreate-venv", action="store_true",
                    help="Wipe the skill-local .venv and rebuild it from scratch. Implies --install.")
    ap.add_argument("--json", action="store_true",
                    help="Emit a JSON summary on stdout (human log still goes to stderr).")
    ap.add_argument("--skip", action="append", default=[],
                    choices=["venv", "packages", "cli", "gws", "claw", "mcp", "lsp", "claude-md"],
                    help="Skip a check group.")
    args = ap.parse_args()

    global UPGRADE_MODE
    UPGRADE_MODE = args.upgrade
    INSTALL_MODE = args.install or args.upgrade or args.recreate_venv

    # Before any CLI check, refresh PATH from the registry so we see winget
    # installs from a previous session without needing a shell restart.
    refresh_path_from_registry()

    if args.json:
        # redirect human log to stderr so stdout stays JSON-only
        global _print
        _print = lambda msg: print(msg, file=sys.stderr, flush=True)  # type: ignore[assignment]

    if args.recreate_venv:
        recreate_venv()
    if "venv" not in args.skip:
        ensure_venv()
    if "packages" not in args.skip:
        check_python_packages()
    if "cli" not in args.skip:
        check_cli_tools()
    if "gws" not in args.skip:
        check_gws_auth()
    if "claw" not in args.skip:
        check_claw_package()
    if "mcp" not in args.skip:
        check_mcp_servers()
    if "lsp" not in args.skip:
        check_lsp_plugins()
    if "claude-md" not in args.skip:
        check_claude_md_integration()

    passed = len(RESULTS["pass"])
    failed = len(RESULTS["fail"])
    fixed = len(RESULTS["fixed"])
    warns = len(RESULTS["warn"])

    summary = {
        "total": passed + failed,
        "passed": passed,
        "failed": failed,
        "fixed": fixed,
        "warnings": warns,
        "install_mode": INSTALL_MODE,
        "results": RESULTS,
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        _print("\n=== SUMMARY ===")
        _print(f"  Total:    {passed + failed}")
        _print(f"  Passed:   {passed}")
        _print(f"  Failed:   {failed}")
        _print(f"  Fixed:    {fixed}")
        _print(f"  Warnings: {warns}")
        if RESULTS["warn"]:
            _print("\n  Warnings:")
            for w in RESULTS["warn"]:
                _print(f"    - {w}")
        if RESULTS["fail"]:
            _print("\n  Failed:")
            for f in RESULTS["fail"]:
                _print(f"    - {f}")
            if not INSTALL_MODE:
                _print("\n  Re-run with --install to attempt auto-fix.")

    if not args.json:
        _emit_next_steps()

    if failed == 0:
        return 0
    if failed >= 3 and INSTALL_MODE:
        return 2
    return 1


def _emit_next_steps() -> None:
    """Print the (short) set of steps healthcheck genuinely cannot automate.

    Only auth flows — everything else is installed automatically by --install.
    """
    hints: list[str] = []
    if any("gws authenticated" not in p for p in RESULTS.get("pass", [])) and \
       "gws auth status" in " ".join(RESULTS.get("warn", [])):
        hints.append("• gws auth login   # interactive Google OAuth — only step healthcheck can't do")
    if not _has_cdm_plugin():
        hints.append("• /plugin -> chrome-devtools-mcp  (inside Claude Code; plugin manager is internal)")
    if hints:
        _print("\n=== AUTH / INTERACTIVE STEPS ===")
        for h in hints:
            _print(f"  {h}")


if __name__ == "__main__":
    sys.exit(main())
