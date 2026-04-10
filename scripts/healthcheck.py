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
print("\n=== LSP PLUGINS ===")
# ============================================================
#
# Official LSP plugins (pyright, typescript, jdtls, kotlin) are installed via
# the Claude Code plugin marketplace. On Windows, npm-installed language servers
# are .cmd shims that Node's uv_spawn cannot execute without shell:true.
#
# Fix: patch the marketplace.json command to use node.exe directly, pointing at
# the language server's JS entry point. This mirrors how the .cmd shim works
# but bypasses the shell requirement.

settings_json = Path.home() / ".claude" / "settings.json"
marketplace_json = (
    Path.home() / ".claude" / "plugins" / "marketplaces"
    / "claude-plugins-official" / ".claude-plugin" / "marketplace.json"
)

# --- LSP plugin definitions ---
# type: "node" = npm-installed JS server (patch to node.exe + entry point)
# type: "bat"  = Java-based server with .bat launcher (patch to cmd.exe /d /s /c <bat>)
LSP_PLUGINS = {
    "typescript-lsp@claude-plugins-official": {
        "type": "node",
        "server_name": "typescript",
        "original_cmd": "typescript-language-server",
        "check_cmd": "typescript-language-server --version",
        "node_entry": "typescript-language-server/lib/cli.mjs",
    },
    "pyright-lsp@claude-plugins-official": {
        "type": "node",
        "server_name": "pyright",
        "original_cmd": "pyright-langserver",
        "check_cmd": "pyright --version",
        "node_entry": "pyright/langserver.index.js",
    },
    "jdtls-lsp@claude-plugins-official": {
        "type": "bat",
        "server_name": "jdtls",
        "original_cmd": "jdtls",
        "check_cmd": "java -version",
        "bat_path": str(Path.home() / ".local" / "bin" / "jdtls.bat"),
    },
    "kotlin-lsp@claude-plugins-official": {
        "type": "cmd",
        "server_name": "kotlin-lsp",
        "original_cmd": "kotlin-lsp",
        "check_cmd": str(Path.home() / ".local" / "kls-jetbrains" / "kotlin-lsp.cmd") + " --help",
        "cmd_path": str(Path.home() / ".local" / "kls-jetbrains" / "kotlin-lsp.cmd"),
    },
}

enabled_plugins = {}
if settings_json.exists():
    try:
        s = json.loads(settings_json.read_text(encoding="utf-8"))
        enabled_plugins = s.get("enabledPlugins", {})
    except Exception:
        pass

for plugin_key, info in LSP_PLUGINS.items():
    short_name = plugin_key.split("@")[0]
    is_enabled = enabled_plugins.get(plugin_key, False)
    check(f"LSP plugin: {short_name} enabled", is_enabled)
    if not is_enabled:
        continue

    # Verify prerequisite binary exists
    ok, output = run_cmd(info["check_cmd"], timeout=15)
    check(f"LSP prereq: {info['check_cmd'].split()[0]}", ok)

    # For bat/cmd-based servers, verify the launcher exists
    if info["type"] == "bat":
        bat = Path(info["bat_path"])
        check(f"LSP launcher: {bat.name}", bat.exists())
        if not bat.exists():
            warn(f"LSP: {short_name}", f"Launcher not found: {bat}. See references/setup.md for install instructions.")
    elif info["type"] == "cmd":
        cmd_path = Path(info["cmd_path"])
        check(f"LSP launcher: {cmd_path.name}", cmd_path.exists())
        if not cmd_path.exists():
            warn(f"LSP: {short_name}", f"Launcher not found: {cmd_path}. See references/setup.md for install instructions.")

# --- Windows marketplace.json auto-patch ---
if sys.platform == "win32" and marketplace_json.exists():
    try:
        mkt = json.loads(marketplace_json.read_text(encoding="utf-8"))
        plugins_list = mkt.get("plugins", [])

        # Resolve node.exe and npm global root (for node-type servers)
        node_exe = None
        npm_root = None
        r = subprocess.run(["node", "-e", "console.log(process.execPath)"],
                           capture_output=True, text=True, timeout=10, shell=True)
        if r.returncode == 0:
            node_exe = r.stdout.strip()
        r = subprocess.run(["npm", "root", "-g"],
                           capture_output=True, text=True, timeout=10, shell=True)
        if r.returncode == 0:
            npm_root = r.stdout.strip()

        # Desired initializationOptions and timeouts per server
        EXTRA_CFG = {
            "jdtls": {
                "initializationOptions": {
                    "settings": {
                        "java": {
                            "autobuild": {"enabled": False},
                            "import": {"exclusions": [
                                "**/node_modules/**", "**/bower_components/**",
                                "**/.metadata/**", "**/.git/**",
                                "**/target/**", "**/build/**",
                                "**/bin/**", "**/.gradle/**",
                            ]},
                        }
                    }
                },
                "startupTimeout": 180000,
            },
            "kotlin-lsp": {
                "startupTimeout": 300000,
            },
        }

        patched_any = False
        for plugin_def in plugins_list:
            lsp_servers = plugin_def.get("lspServers", {})
            for srv_name, srv_cfg in lsp_servers.items():
                cmd = srv_cfg.get("command", "")

                # --- Command patch (uv_spawn fix) ---
                # Already patched if command is a full path (node.exe, cmd.exe, or .cmd)
                if cmd.lower().endswith("node.exe") or cmd.lower().endswith("cmd.exe") or cmd.lower().endswith(".cmd"):
                    check(f"LSP patch: {srv_name} (Windows uv_spawn)", True)
                else:
                    # Find matching plugin definition
                    for info in LSP_PLUGINS.values():
                        if cmd != info["original_cmd"] or srv_name != info["server_name"]:
                            continue

                        if info["type"] == "node" and node_exe and npm_root:
                            entry = Path(npm_root) / info["node_entry"]
                            if entry.exists():
                                old_args = srv_cfg.get("args", [])
                                srv_cfg["command"] = node_exe
                                srv_cfg["args"] = [str(entry)] + old_args
                                patched_any = True
                                print(f"  [PATCH] LSP {srv_name}: {cmd} -> node.exe {entry}")
                            else:
                                warn(f"LSP patch: {srv_name}", f"Entry point not found: {entry}")

                        elif info["type"] == "bat":
                            bat = Path(info["bat_path"])
                            if bat.exists():
                                old_args = srv_cfg.get("args", [])
                                srv_cfg["command"] = "cmd.exe"
                                srv_cfg["args"] = ["/d", "/s", "/c", str(bat)] + old_args
                                patched_any = True
                                print(f"  [PATCH] LSP {srv_name}: {cmd} -> cmd.exe {bat}")
                            else:
                                warn(f"LSP patch: {srv_name}", f"Launcher not found: {bat}")

                        elif info["type"] == "cmd":
                            cmd_path = Path(info["cmd_path"])
                            if cmd_path.exists():
                                old_args = srv_cfg.get("args", [])
                                srv_cfg["command"] = str(cmd_path)
                                srv_cfg["args"] = old_args
                                patched_any = True
                                print(f"  [PATCH] LSP {srv_name}: {cmd} -> {cmd_path}")
                            else:
                                warn(f"LSP patch: {srv_name}", f"Launcher not found: {cmd_path}")
                        break

                # --- Extra config patch (initializationOptions, timeouts) ---
                if srv_name in EXTRA_CFG:
                    for key, val in EXTRA_CFG[srv_name].items():
                        if srv_cfg.get(key) != val:
                            srv_cfg[key] = val
                            patched_any = True
                            print(f"  [PATCH] LSP {srv_name}: set {key}")

        if patched_any:
            marketplace_json.write_text(
                json.dumps(mkt, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            RESULTS["fixed"].append("LSP: marketplace.json Windows patch")
            print("  [FIXED] marketplace.json updated — restart Claude Code to apply")
        else:
            check("LSP patch: marketplace.json (Windows)", True)

    except Exception as e:
        warn("LSP patch", f"Could not process marketplace.json: {e}")

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
    "clickup-cli.md",
    "setup.md",
]
for f in reference_files:
    p = skill_dir / "references" / f
    if p.exists():
        check(f"Reference: {f}", True)

# Example files
example_files = [
    "office-documents.md",
    "pdf-workflows.md",
    "image-processing.md",
    "video-audio.md",
    "email-workflows.md",
    "data-pipelines.md",
    "document-conversion.md",
    "clickup-workflows.md",
]
for f in example_files:
    p = skill_dir / "examples" / f
    if p.exists():
        check(f"Example: {f}", True)

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
