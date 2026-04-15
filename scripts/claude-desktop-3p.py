#!/usr/bin/env python3
"""
Claude Desktop Custom 3P (BYOM) toggler — flips the registry policies that
make Claude Desktop run against a local-model gateway instead of claude.ai.

No binary modification. Pure HKCU + HKLM SOFTWARE\\Policies\\Claude writes,
so it survives MSIX updates and is fully reversible.

Usage:
    python ~/.claude/skills/claude-claw/scripts/claude-desktop-3p.py status
    python ~/.claude/skills/claude-claw/scripts/claude-desktop-3p.py enable [--url URL] [--model MODEL] [--api-key KEY] [--org-uuid UUID]
    python ~/.claude/skills/claude-claw/scripts/claude-desktop-3p.py disable

Defaults (when --url is omitted):
    1. Auto-detect Tailscale Funnel URL via `tailscale funnel status`
    2. Fall back to https://<tailscale-machine-name>.<tailnet>.ts.net
    3. Error out — Claude Desktop's gateway URL must be HTTPS, no localhost

Exit codes:
    0 = success / mode is as requested
    1 = registry write failed (UAC declined, etc.)
    2 = bad arguments / preflight failed
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
HIVES = ("HKCU", "HKLM")
KEY_PATH = r"SOFTWARE\Policies\Claude"
FIELDS = (
    "inferenceProvider",
    "inferenceGatewayBaseUrl",
    "inferenceGatewayApiKey",
    "fallbackModels",
    "deploymentOrganizationUuid",
)


def run(*args, check=False, capture=True):
    bin_path = shutil.which(args[0]) or args[0]
    return subprocess.run(
        [bin_path, *args[1:]],
        check=check,
        capture_output=capture,
        text=True,
    )


def reg_query(hive: str) -> dict[str, str]:
    """Read all values under the policy key for one hive. Empty dict if absent."""
    res = run("reg", "query", f"{hive}\\{KEY_PATH}")
    if res.returncode != 0:
        return {}
    out: dict[str, str] = {}
    for line in res.stdout.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) == 3 and parts[1].startswith("REG_"):
            out[parts[0]] = parts[2]
    return out


def detect_tailscale_funnel_url() -> str | None:
    """Try `tailscale funnel status --json` first, fall back to deriving from `tailscale status`."""
    res = run("tailscale", "funnel", "status", "--json")
    if res.returncode == 0 and res.stdout.strip():
        try:
            data = json.loads(res.stdout)
            for host_url in data.get("Web", {}):
                # host_url like "machine.tailnet.ts.net:443"
                host = host_url.rsplit(":", 1)[0]
                return f"https://{host}"
        except (json.JSONDecodeError, AttributeError):
            pass
    # fallback: derive from tailscale status
    res = run("tailscale", "status", "--json")
    if res.returncode == 0 and res.stdout.strip():
        try:
            data = json.loads(res.stdout)
            self_node = data.get("Self", {})
            dns = self_node.get("DNSName", "").rstrip(".")
            if dns:
                return f"https://{dns}"
        except (json.JSONDecodeError, AttributeError):
            pass
    return None


def build_admin_script(values: dict[str, str] | None) -> str:
    """Generate a PowerShell payload that runs elevated."""
    lines = ["$ErrorActionPreference = 'Stop'"]
    if values is None:
        for hive in HIVES:
            lines.append(f"reg delete '{hive}\\{KEY_PATH}' /f 2>$null")
    else:
        for hive in HIVES:
            for name, val in values.items():
                escaped = val.replace('"', '\\"')
                lines.append(
                    f'reg add "{hive}\\{KEY_PATH}" /v {name} /t REG_SZ /d "{escaped}" /f'
                )
    lines.append("Write-Host 'OK'")
    return "; ".join(lines)


def run_elevated(payload: str) -> int:
    """Spawn an elevated PowerShell that runs `payload`, return its exit code."""
    encoded = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            f"[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes(@'\n{payload}\n'@))",
        ],
        capture_output=True,
        text=True,
    ).stdout.strip()

    res = run(
        "powershell",
        "-NoProfile",
        "-Command",
        (
            f"$p = Start-Process powershell.exe "
            f"-ArgumentList '-NoProfile','-EncodedCommand','{encoded}' "
            f"-Verb RunAs -Wait -PassThru; exit $p.ExitCode"
        ),
    )
    return res.returncode


def cmd_status() -> int:
    print("=== HKCU\\SOFTWARE\\Policies\\Claude ===")
    hkcu = reg_query("HKCU")
    print(json.dumps(hkcu, indent=2) if hkcu else "(empty)")
    print("\n=== HKLM\\SOFTWARE\\Policies\\Claude ===")
    hklm = reg_query("HKLM")
    print(json.dumps(hklm, indent=2) if hklm else "(empty)")
    if hkcu.get("inferenceProvider") or hklm.get("inferenceProvider"):
        print("\n[PASS] 3P mode IS configured")
        return 0
    print("\n[WARN] 3P mode NOT configured")
    return 0


def cmd_enable(args: argparse.Namespace) -> int:
    url = args.url
    if not url:
        url = detect_tailscale_funnel_url()
        if not url:
            print(
                "[FAIL] No --url and could not auto-detect Tailscale URL.\n"
                "       Claude Desktop rejects http:// — gateway URL must be HTTPS.\n"
                "       Either start telecode (which auto-starts Tailscale Funnel)\n"
                "       or pass --url explicitly.",
                file=sys.stderr,
            )
            return 2
        print(f"[INFO] Auto-detected gateway URL: {url}")
    if not url.startswith("https://"):
        print(f"[FAIL] Gateway URL must be HTTPS (got {url!r})", file=sys.stderr)
        return 2

    values = {
        "inferenceProvider": "gateway",
        "inferenceGatewayBaseUrl": url,
        "inferenceGatewayApiKey": args.api_key,
        "fallbackModels": json.dumps([args.model]),
        "deploymentOrganizationUuid": args.org_uuid,
    }
    print(f"[INFO] Will write {len(values)} keys to HKCU + HKLM. Approve UAC.")
    rc = run_elevated(build_admin_script(values))
    if rc != 0:
        print(f"[FAIL] Elevated registry write failed (exit {rc})", file=sys.stderr)
        return 1
    print(
        "[PASS] 3P mode enabled. Fully quit Claude Desktop and relaunch.\n"
        "       Confirm via log: AppData\\Roaming\\Claude\\logs\\main.log\n"
        "       Look for: '[custom-3p] 3P mode active {provider: \"gateway\"}'"
    )
    return 0


def cmd_disable() -> int:
    print("[INFO] Will delete HKCU + HKLM policy keys. Approve UAC.")
    rc = run_elevated(build_admin_script(None))
    if rc != 0:
        print(f"[FAIL] Elevated registry delete failed (exit {rc})", file=sys.stderr)
        return 1
    print("[PASS] 3P mode disabled. Relaunch Claude Desktop to return to 1P mode.")
    return 0


def main() -> int:
    if sys.platform != "win32":
        print("[FAIL] This script only applies to Claude Desktop on Windows", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(
        description="Toggle Claude Desktop Custom 3P (BYOM) mode via registry policy."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    e = sub.add_parser("enable")
    e.add_argument("--url", help="Gateway URL (HTTPS). Auto-detects from Tailscale if omitted.")
    e.add_argument("--model", default="qwen3.5-35b-a3b", help="Model ID for fallbackModels")
    e.add_argument("--api-key", default="lmstudio", help="Gateway API key (any value)")
    e.add_argument(
        "--org-uuid",
        default="00000000-0000-0000-0000-000000000000",
        help="Synthetic deploymentOrganizationUuid",
    )
    sub.add_parser("disable")
    args = parser.parse_args()

    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "enable":
        return cmd_enable(args)
    return cmd_disable()


if __name__ == "__main__":
    sys.exit(main())
