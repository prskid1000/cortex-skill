#!/usr/bin/env python3
"""
Claude Claw Self-Test: Verify all Python packages, CLI tools, and skill files are present.
Run (bash):       python ~/.claude/skills/claude-claw/scripts/healthcheck.py
Run (Windows):    python "%USERPROFILE%\\.claude\\skills\\claude-claw\\scripts\\healthcheck.py"

Exit codes: 0 = all pass, 1 = some failures (auto-fix attempted), 2 = critical failures
"""

import subprocess
import sys
import json
import os
from pathlib import Path

# Ensure CLI tools are in PATH
extra_paths = [
    str(Path.home() / ".local" / "bin"),
]
for p in extra_paths:
    if p not in os.environ.get("PATH", ""):
        os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")

RESULTS = {"pass": [], "fail": [], "warn": [], "fixed": []}

def check(name, ok, fix_cmd=None):
    if ok:
        RESULTS["pass"].append(name)
        print(f"  [PASS] {name}")
    else:
        RESULTS["fail"].append(name)
        print(f"  [FAIL] {name}")
        if fix_cmd:
            print(f"         Attempting auto-fix: {fix_cmd}")
            try:
                result = subprocess.run(fix_cmd, shell=True, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    RESULTS["fixed"].append(name)
                    RESULTS["fail"].remove(name)
                    print(f"         [FIXED] {name}")
                else:
                    print(f"         [FIX FAILED] {result.stderr[:200]}")
            except Exception as e:
                print(f"         [FIX ERROR] {e}")

def warn(name, msg):
    RESULTS["warn"].append(f"{name}: {msg}")
    print(f"  [WARN] {name}: {msg}")

def run_cmd(cmd, timeout=10):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout.strip()
    except Exception:
        return False, ""

# ============================================================
print("\n=== PYTHON PACKAGES ===")
# ============================================================

PACKAGES = {
    "openpyxl": "openpyxl",
    "python-docx": "docx",
    "python-pptx": "pptx",
    "pymupdf": "fitz",
    "PyPDF2": "PyPDF2",
    "reportlab": "reportlab",
    "pdfplumber": "pdfplumber",
    "pillow": "PIL",
    "lxml": "lxml",
    "beautifulsoup4": "bs4",
}

for pip_name, import_name in PACKAGES.items():
    try:
        __import__(import_name)
        check(f"Python: {pip_name}", True)
    except ImportError:
        check(f"Python: {pip_name}", False, fix_cmd=f"pip install {pip_name}")

# ============================================================
print("\n=== CLI TOOLS ===")
# ============================================================

CLI_TOOLS = {
    "gws": "gws --version",
    "clickup": "clickup version",
    "git": "git --version",
    "ffmpeg": "ffmpeg -version",
    "pandoc": "pandoc --version",
    "magick (ImageMagick)": "magick --version",
    "node": "node --version",
    "npx": "npx --version",
}

for name, cmd in CLI_TOOLS.items():
    ok, output = run_cmd(cmd)
    check(f"CLI: {name}", ok)

# ============================================================
print("\n=== GOOGLE WORKSPACE AUTH ===")
# ============================================================

ok, output = run_cmd("gws auth status", timeout=15)
if ok and output:
    try:
        auth_info = json.loads(output)
        token_valid = auth_info.get("token_valid", False)
        has_refresh = auth_info.get("has_refresh_token", False)
        if token_valid and has_refresh:
            check("GWS: Auth", True)
        else:
            check("GWS: Auth", False)
            warn("GWS", "Token invalid or missing refresh token — run 'gws auth login'")
    except json.JSONDecodeError:
        check("GWS: Auth", False)
        warn("GWS", "Could not parse auth status output")
else:
    check("GWS: Auth", False)
    warn("GWS", "Run 'gws auth login' to authenticate")

# ============================================================
print("\n=== MCP SERVERS ===")
# ============================================================
#
# This block VERIFIES MCP config;
# it does not patch ~/.claude.json automatically (that file is the harness's
# main config and is too high-stakes to rewrite from a script). On failure
# the exact fix is printed and the user applies it manually, then restarts
# Claude Code.
#
# Note: do NOT wrap `npx` in `cmd /c` in these configs — Claude Code's MCP
# launcher already spawns Windows servers as `cmd.exe /d /s /c "npx ..."`
# internally. A manual wrapper causes double-wrapping.

claude_json = Path.home() / ".claude.json"
plugin_mcp_json = (
    Path.home()
    / ".claude" / "plugins" / "cache" / "chrome-devtools-plugins"
    / "chrome-devtools-mcp" / "latest" / ".mcp.json"
)

# --- MySQL MCP ---
mysql_ok = False
if claude_json.exists():
    try:
        cfg = json.loads(claude_json.read_text(encoding="utf-8"))
        entry = cfg.get("mcpServers", {}).get("mcp_server_mysql")
        if entry and entry.get("command") == "npx" and "@benborla29/mcp-server-mysql" in " ".join(entry.get("args", [])):
            mysql_ok = True
    except Exception as e:
        warn("MCP: mysql", f"Could not parse ~/.claude.json: {e}")

check("MCP: mysql (~/.claude.json -> mcpServers.mcp_server_mysql)", mysql_ok)
if not mysql_ok:
    warn("MCP: mysql", "Add to ~/.claude.json under mcpServers. See references/setup.md -> 'MySQL' for the exact JSON block. Restart Claude Code after editing.")

# --- Chrome DevTools MCP (plugin-provided) ---
cdt_ok = False
if plugin_mcp_json.exists():
    try:
        cdt_cfg = json.loads(plugin_mcp_json.read_text(encoding="utf-8"))
        cdt_entry = cdt_cfg.get("chrome-devtools", {})
        if cdt_entry.get("command") == "npx" and "chrome-devtools-mcp" in " ".join(cdt_entry.get("args", [])):
            cdt_ok = True
    except Exception as e:
        warn("MCP: chrome-devtools", f"Could not parse plugin .mcp.json: {e}")

check("MCP: chrome-devtools (plugin .mcp.json)", cdt_ok)
if not cdt_ok:
    warn("MCP: chrome-devtools", f"Plugin cache at {plugin_mcp_json} is missing or malformed. Install/reinstall via the Claude Code plugin marketplace (chrome-devtools-plugins).")

# ============================================================
print("\n=== CONTEXT-MODE PLUGIN ===")
# ============================================================
#
# context-mode (https://github.com/mksglu/context-mode) is the MCP plugin
# that provides ctx_execute, ctx_batch_execute, ctx_search, etc.
# This block verifies:
#   1. Plugin is registered and enabled in settings.json
#   2. node_modules exist in the cached install (MCP server needs them)
#   3. The Windows "spawn bun ENOENT" fix is applied in the bundles
#      (bun must be in the executor's needsShell list so shell:true is used)

settings_json = Path.home() / ".claude" / "settings.json"
ctx_plugin_key = "context-mode@context-mode"

# --- Plugin registration ---
ctx_registered = False
ctx_enabled = False
ctx_install_path = None
if settings_json.exists():
    try:
        settings = json.loads(settings_json.read_text(encoding="utf-8"))
        ctx_enabled = settings.get("enabledPlugins", {}).get(ctx_plugin_key, False)
    except Exception as e:
        warn("context-mode", f"Could not parse settings.json: {e}")

installed_plugins_json = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
if installed_plugins_json.exists():
    try:
        ip = json.loads(installed_plugins_json.read_text(encoding="utf-8"))
        entries = ip.get("plugins", {}).get(ctx_plugin_key, [])
        if entries:
            ctx_registered = True
            ctx_install_path = Path(entries[0].get("installPath", ""))
    except Exception as e:
        warn("context-mode", f"Could not parse installed_plugins.json: {e}")

check("context-mode: registered in installed_plugins.json", ctx_registered)
check("context-mode: enabled in settings.json", ctx_enabled)
if not ctx_registered:
    warn("context-mode", "Install via Claude Code plugin marketplace: mksglu/context-mode")

# --- node_modules in cached install ---
if ctx_install_path and ctx_install_path.exists():
    node_modules = ctx_install_path / "node_modules"
    has_nm = node_modules.is_dir()
    has_sqlite = (node_modules / "better-sqlite3").is_dir() if has_nm else False
    check("context-mode: node_modules present", has_nm)
    check("context-mode: better-sqlite3 installed", has_sqlite)
    if not has_nm or not has_sqlite:
        # Auto-fix: run npm install in the cached plugin dir
        fix = f'cd "{ctx_install_path}" && npm install --silent'
        check("context-mode: npm install (auto-fix)", False, fix_cmd=fix)
else:
    if ctx_registered:
        warn("context-mode", f"Install path not found: {ctx_install_path}")

# --- Windows bun spawn fix ---
# On Windows, bun installed via nvm4w/scoop is a POSIX shell script shim.
# Node.js spawn("bun") fails with ENOENT. The fix: add "bun" to the
# executor's needsShell list in the bundles so shell:true is used.
if sys.platform == "win32" and ctx_install_path and ctx_install_path.exists():
    bundles_patched = True
    bundles_to_patch = []
    needle = b'"tsx","ts-node","elixir"'
    patched_needle = b'"tsx","ts-node","elixir","bun"'

    # Check both cached and marketplace copies
    marketplace_dir = Path.home() / ".claude" / "plugins" / "marketplaces" / "context-mode"
    for bundle_dir in [ctx_install_path, marketplace_dir]:
        if not bundle_dir.exists():
            continue
        for bundle_name in ["server.bundle.mjs", "cli.bundle.mjs"]:
            bundle_path = bundle_dir / bundle_name
            if bundle_path.exists():
                content = bundle_path.read_bytes()
                if patched_needle in content:
                    pass  # Already patched
                elif needle in content:
                    bundles_patched = False
                    bundles_to_patch.append(bundle_path)

    if bundles_patched:
        check("context-mode: bun needsShell patch (Windows)", True)
    else:
        print(f"  [FAIL] context-mode: bun needsShell patch (Windows)")
        print(f"         Attempting auto-fix: patching {len(bundles_to_patch)} bundle(s)...")
        patch_ok = True
        for bp in bundles_to_patch:
            try:
                data = bp.read_bytes()
                data = data.replace(needle, patched_needle)
                bp.write_bytes(data)
                print(f"         [FIXED] {bp}")
                RESULTS["fixed"].append(f"context-mode: patched {bp.name}")
            except Exception as e:
                print(f"         [FIX FAILED] {bp}: {e}")
                patch_ok = False
        if patch_ok:
            RESULTS["pass"].append("context-mode: bun needsShell patch (Windows)")
        else:
            RESULTS["fail"].append("context-mode: bun needsShell patch (Windows)")

# ============================================================
print("\n=== SKILL STRUCTURE ===")
# ============================================================

skill_dir = Path.home() / ".claude" / "skills" / "claude-claw"

check("Skill: claude-claw/SKILL.md exists", (skill_dir / "SKILL.md").exists())
check("Skill: claude-claw/scripts/ exists", (skill_dir / "scripts").is_dir())
check("Skill: claude-claw/references/ exists", (skill_dir / "references").is_dir())
check("Skill: claude-claw/examples/ exists", (skill_dir / "examples").is_dir())

# Reference files
reference_files = [
    "gws-cli.md",
    "document-creation.md",
    "pdf-tools.md",
    "media-tools.md",
    "conversion-tools.md",
    "web-parsing.md",
    "email-reference.md",
    "database-reference.md",
    "clickup-cli.md",
    "setup.md",
]
for f in reference_files:
    p = skill_dir / "references" / f
    if p.exists():
        check(f"Reference: {f}", True)
    else:
        warn("References", f"Missing references/{f}")

# Example files
example_files = [
    "office-documents.md",
    "pdf-workflows.md",
    "image-processing.md",
    "video-audio.md",
    "email-workflows.md",
    "database-export.md",
    "data-pipelines.md",
    "document-conversion.md",
    "clickup-workflows.md",
]
for f in example_files:
    p = skill_dir / "examples" / f
    if p.exists():
        check(f"Example: {f}", True)
    else:
        warn("Examples", f"Missing examples/{f}")

# ============================================================
print("\n=== SUMMARY ===")
# ============================================================

total = len(RESULTS["pass"]) + len(RESULTS["fail"])
passed = len(RESULTS["pass"])
failed = len(RESULTS["fail"])
fixed = len(RESULTS["fixed"])
warnings = len(RESULTS["warn"])

print(f"\nTotal: {total} checks")
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")
print(f"  Fixed:  {fixed}")
print(f"  Warnings: {warnings}")

if RESULTS["warn"]:
    print("\nWarnings:")
    for w in RESULTS["warn"]:
        print(f"  - {w}")

if RESULTS["fail"]:
    print("\nFailed:")
    for f in RESULTS["fail"]:
        print(f"  - {f}")

if failed > 0:
    print("\nStatus: SOME FAILURES")
    sys.exit(1 if failed < 3 else 2)
else:
    print("\nStatus: ALL PASS")
    sys.exit(0)
