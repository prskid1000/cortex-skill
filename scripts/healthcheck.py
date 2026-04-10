#!/usr/bin/env python3
"""
Claude Claw Healthcheck — verify and auto-fix all dependencies.

Usage:
    python ~/.claude/skills/claude-claw/scripts/healthcheck.py

Exit codes: 0 = all pass, 1 = failures (auto-fix attempted), 2 = critical
"""

import subprocess
import sys
import json
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RESULTS = {"pass": [], "fail": [], "warn": [], "fixed": []}


def check(name: str, ok: bool, fix_cmd: str = ""):
    if ok:
        RESULTS["pass"].append(name)
        print(f"  [PASS] {name}")
    else:
        RESULTS["fail"].append(name)
        print(f"  [FAIL] {name}")
        if fix_cmd:
            print(f"         Auto-fix: {fix_cmd}")
            try:
                r = subprocess.run(fix_cmd, shell=True, capture_output=True, text=True, timeout=120)
                if r.returncode == 0:
                    RESULTS["fixed"].append(name)
                    RESULTS["fail"].remove(name)
                    print(f"         [FIXED] {name}")
                else:
                    print(f"         [FIX FAILED] {r.stderr[:200]}")
            except Exception as e:
                print(f"         [FIX ERROR] {e}")


def warn(name: str, msg: str):
    RESULTS["warn"].append(f"{name}: {msg}")
    print(f"  [WARN] {name}: {msg}")


def run_cmd(cmd: str, timeout: int = 10) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout.strip()
    except Exception:
        return False, ""


# Ensure ~/.local/bin is in PATH
local_bin = str(Path.home() / ".local" / "bin")
if local_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = local_bin + os.pathsep + os.environ["PATH"]

HOME = Path.home()

# ---------------------------------------------------------------------------
# 1. Python packages
# ---------------------------------------------------------------------------

def check_python_packages():
    print("\n=== 1. PYTHON PACKAGES ===")
    packages = {
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
    for pip_name, import_name in packages.items():
        try:
            __import__(import_name)
            check(pip_name, True)
        except ImportError:
            check(pip_name, False, fix_cmd=f"pip install {pip_name}")


# ---------------------------------------------------------------------------
# 2. CLI tools
# ---------------------------------------------------------------------------

def check_cli_tools():
    print("\n=== 2. CLI TOOLS ===")
    tools = {
        "gws": "gws --version",
        "clickup": "clickup version",
        "git": "git --version",
        "ffmpeg": "ffmpeg -version",
        "pandoc": "pandoc --version",
        "magick": "magick --version",
        "node": "node --version",
        "npx": "npx --version",
    }
    for name, cmd in tools.items():
        ok, _ = run_cmd(cmd)
        check(name, ok)


# ---------------------------------------------------------------------------
# 3. GWS auth
# ---------------------------------------------------------------------------

def check_gws_auth():
    print("\n=== 3. GWS AUTH ===")
    ok, output = run_cmd("gws auth status", timeout=15)
    if ok and output:
        try:
            info = json.loads(output)
            valid = info.get("token_valid", False) and info.get("has_refresh_token", False)
            check("gws auth", valid)
            if not valid:
                warn("gws", "Run 'gws auth login'")
        except json.JSONDecodeError:
            check("gws auth", False)
    else:
        check("gws auth", False)


# ---------------------------------------------------------------------------
# 4. MCP servers
# ---------------------------------------------------------------------------

def check_mcp_servers():
    print("\n=== 4. MCP SERVERS ===")

    claude_json = HOME / ".claude.json"
    cfg = {}
    if claude_json.exists():
        try:
            cfg = json.loads(claude_json.read_text(encoding="utf-8"))
        except Exception:
            warn("mcp", "Could not parse ~/.claude.json")

    # MySQL
    entry = cfg.get("mcpServers", {}).get("mcp_server_mysql", {})
    mysql_ok = (
        entry.get("command") == "npx"
        and "@benborla29/mcp-server-mysql" in " ".join(entry.get("args", []))
    )
    check("mysql mcp", mysql_ok)

    # Chrome DevTools (plugin-provided)
    cdt_mcp = (
        HOME / ".claude" / "plugins" / "cache"
        / "chrome-devtools-plugins" / "chrome-devtools-mcp" / "latest" / ".mcp.json"
    )
    cdt_ok = False
    if cdt_mcp.exists():
        try:
            cdt = json.loads(cdt_mcp.read_text(encoding="utf-8"))
            e = cdt.get("chrome-devtools", {})
            cdt_ok = e.get("command") == "npx" and "chrome-devtools-mcp" in " ".join(e.get("args", []))
        except Exception:
            pass
    check("chrome-devtools mcp", cdt_ok)


# ---------------------------------------------------------------------------
# 5. LSP plugins
# ---------------------------------------------------------------------------

# Plugin definitions: how each LSP is installed and patched on Windows.
#   type "node" — npm-installed JS server, patch command to node.exe + entry point
#   type "bat"  — Java server with .bat launcher, patch to cmd.exe /d /s /c <bat>
#   type "cmd"  — Native .cmd binary, patch command to full path

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
        "bat_path": str(HOME / ".local" / "bin" / "jdtls.bat"),
    },
    "kotlin-lsp@claude-plugins-official": {
        "type": "cmd",
        "server_name": "kotlin-lsp",
        "original_cmd": "kotlin-lsp",
        "check_cmd": str(HOME / ".local" / "kls-jetbrains" / "kotlin-lsp.cmd") + " --help",
        "cmd_path": str(HOME / ".local" / "kls-jetbrains" / "kotlin-lsp.cmd"),
    },
}

# Extra config applied to marketplace.json per server
LSP_EXTRA_CFG = {
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


def check_lsp_plugins():
    print("\n=== 5. LSP PLUGINS ===")

    settings_json = HOME / ".claude" / "settings.json"
    marketplace_json = (
        HOME / ".claude" / "plugins" / "marketplaces"
        / "claude-plugins-official" / ".claude-plugin" / "marketplace.json"
    )

    # Read enabled plugins
    enabled = {}
    if settings_json.exists():
        try:
            enabled = json.loads(settings_json.read_text(encoding="utf-8")).get("enabledPlugins", {})
        except Exception:
            pass

    # --- Check each plugin ---
    for key, info in LSP_PLUGINS.items():
        short = key.split("@")[0]

        if not enabled.get(key, False):
            check(f"{short} enabled", False)
            continue
        check(f"{short} enabled", True)

        # Verify prerequisite
        ok, _ = run_cmd(info["check_cmd"], timeout=15)
        check(f"{short} prereq", ok)

        # Verify launcher for bat/cmd types
        if info["type"] == "bat":
            check(f"{short} launcher", Path(info["bat_path"]).exists())
        elif info["type"] == "cmd":
            check(f"{short} launcher", Path(info["cmd_path"]).exists())

    # --- Windows auto-patch ---
    if sys.platform != "win32" or not marketplace_json.exists():
        return

    try:
        mkt = json.loads(marketplace_json.read_text(encoding="utf-8"))
    except Exception as e:
        warn("lsp patch", f"Cannot parse marketplace.json: {e}")
        return

    # Resolve node paths
    node_exe, npm_root = None, None
    r = subprocess.run(["node", "-e", "console.log(process.execPath)"],
                       capture_output=True, text=True, timeout=10, shell=True)
    if r.returncode == 0:
        node_exe = r.stdout.strip()
    r = subprocess.run(["npm", "root", "-g"],
                       capture_output=True, text=True, timeout=10, shell=True)
    if r.returncode == 0:
        npm_root = r.stdout.strip()

    patched = False
    for plugin_def in mkt.get("plugins", []):
        for srv_name, srv_cfg in plugin_def.get("lspServers", {}).items():
            cmd = srv_cfg.get("command", "")

            # Already patched?
            if cmd.lower().endswith(("node.exe", "cmd.exe", ".cmd")):
                check(f"{srv_name} patched", True)
            else:
                # Find matching definition and patch
                for info in LSP_PLUGINS.values():
                    if cmd != info["original_cmd"] or srv_name != info["server_name"]:
                        continue

                    if info["type"] == "node" and node_exe and npm_root:
                        entry = Path(npm_root) / info["node_entry"]
                        if entry.exists():
                            srv_cfg["command"] = node_exe
                            srv_cfg["args"] = [str(entry)] + srv_cfg.get("args", [])
                            patched = True
                            print(f"  [PATCH] {srv_name} → node.exe")

                    elif info["type"] == "bat":
                        bat = Path(info["bat_path"])
                        if bat.exists():
                            srv_cfg["command"] = "cmd.exe"
                            srv_cfg["args"] = ["/d", "/s", "/c", str(bat)] + srv_cfg.get("args", [])
                            patched = True
                            print(f"  [PATCH] {srv_name} → cmd.exe + {bat.name}")

                    elif info["type"] == "cmd":
                        cmd_path = Path(info["cmd_path"])
                        if cmd_path.exists():
                            srv_cfg["command"] = str(cmd_path)
                            patched = True
                            print(f"  [PATCH] {srv_name} → {cmd_path.name}")
                    break

            # Apply extra config (timeouts, initializationOptions)
            if srv_name in LSP_EXTRA_CFG:
                for k, v in LSP_EXTRA_CFG[srv_name].items():
                    if srv_cfg.get(k) != v:
                        srv_cfg[k] = v
                        patched = True

    if patched:
        marketplace_json.write_text(json.dumps(mkt, indent=2, ensure_ascii=False), encoding="utf-8")
        RESULTS["fixed"].append("marketplace.json patched")
        print("  [FIXED] marketplace.json — restart Claude Code to apply")
    else:
        check("marketplace.json", True)


# ---------------------------------------------------------------------------
# Run all checks
# ---------------------------------------------------------------------------

def main():
    check_python_packages()
    check_cli_tools()
    check_gws_auth()
    check_mcp_servers()
    check_lsp_plugins()

    # Summary
    print("\n=== SUMMARY ===")
    total = len(RESULTS["pass"]) + len(RESULTS["fail"])
    passed = len(RESULTS["pass"])
    failed = len(RESULTS["fail"])
    fixed = len(RESULTS["fixed"])

    print(f"\n  Total:  {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Fixed:  {fixed}")
    print(f"  Warns:  {len(RESULTS['warn'])}")

    if RESULTS["warn"]:
        print("\n  Warnings:")
        for w in RESULTS["warn"]:
            print(f"    - {w}")

    if RESULTS["fail"]:
        print("\n  Failed:")
        for f in RESULTS["fail"]:
            print(f"    - {f}")

    if failed > 0:
        print("\n  Status: SOME FAILURES")
        sys.exit(1 if failed < 3 else 2)
    else:
        print("\n  Status: ALL PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
