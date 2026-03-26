#!/usr/bin/env python3
"""
Cortex Self-Test: Verify all tools, packages, MCPs, and services are available.
Run: python ~/.claude/skills/cortex/bin/healthcheck.py

Exit codes: 0 = all pass, 1 = some failures (auto-fix attempted), 2 = critical failures
"""

import subprocess
import sys
import json
from pathlib import Path

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
    "git": "git --version",
    "ffmpeg": "ffmpeg -version",
    "pandoc": "pandoc --version",
    "magick (ImageMagick)": "magick --version",
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
print("\n=== SKILL STRUCTURE ===")
# ============================================================

root = Path.home() / ".claude" / "skills"
cortex_dir = root / "cortex"

check("Skill: cortex/SKILL.md exists", (cortex_dir / "SKILL.md").exists())
check("Skill: cortex/bin/ exists", (cortex_dir / "bin").is_dir())

if (cortex_dir / "docs").is_dir():
    check("Skill: cortex/docs/ exists", True)
else:
    warn("Skill", "cortex/docs/ missing (ok if fully split into sub-skills)")

# Legacy monolith docs (may be removed once fully split into sub-skills)
legacy_docs = [
    "workspace.md",
    "doc-forge.md", "mailbox.md", "media-kit.md",
    "datastore.md", "pipelines.md", "bootstrap.md",
]
for f in legacy_docs:
    p = cortex_dir / "docs" / f
    if p.exists():
        check(f"Doc: cortex/docs/{f}", True)
    else:
        warn("Docs", f"Missing cortex/docs/{f} (ok if migrated to sub-skills)")

# Sub-skills (optional but recommended)
subskills = [
    "cortex-workspace",
    "cortex-doc-forge",
    "cortex-mailbox",
    "cortex-media-kit",
    "cortex-datastore",
    "cortex-pipelines",
    "cortex-bootstrap",
]
for s in subskills:
    d = root / s
    if not d.exists():
        warn("Sub-skill", f"{s} not found (ok if not installed yet)")
        continue
    check(f"Sub-skill: {s}/SKILL.md exists", (d / "SKILL.md").exists())
    if (d / "docs").is_dir():
        idx = d / "docs" / "index.md"
        if idx.exists():
            check(f"Sub-skill doc: {s}/docs/index.md", True)
        else:
            warn("Sub-skill docs", f"Missing {s}/docs/index.md")
    else:
        warn("Sub-skill docs", f"Missing {s}/docs/ directory")

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
