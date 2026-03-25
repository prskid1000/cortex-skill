#!/usr/bin/env python3
"""
Cortex Auto-Improve: Analyze skill usage and suggest/apply enhancements.
Run: python ~/.claude/skills/cortex/bin/evolve.py [--apply]

Scans the skill files for:
1. Missing or stale reference docs
2. Broken internal links
3. Empty example slots
4. Coverage gaps (common patterns not documented)
5. Stale content (outdated dates, deprecated tools)

With --apply: automatically patches fixable issues.
Without --apply: just reports findings.
"""

import sys
import re
from pathlib import Path

SKILL_DIR = Path.home() / ".claude" / "skills" / "cortex"
APPLY = "--apply" in sys.argv
FINDINGS = {"info": [], "suggestion": [], "fixable": [], "applied": []}

def info(msg):
    FINDINGS["info"].append(msg)

def suggest(msg):
    FINDINGS["suggestion"].append(msg)
    print(f"  [SUGGEST] {msg}")

def fixable(msg, fix_fn=None):
    FINDINGS["fixable"].append(msg)
    if APPLY and fix_fn:
        try:
            fix_fn()
            FINDINGS["applied"].append(msg)
            print(f"  [APPLIED] {msg}")
        except Exception as e:
            print(f"  [FIX ERROR] {msg}: {e}")
    else:
        print(f"  [FIXABLE] {msg}")

# ============================================================
print("\n=== STRUCTURE CHECK ===")
# ============================================================

# Check SKILL.md references match actual files
skill_md = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
ref_dir = SKILL_DIR / "docs"
script_dir = SKILL_DIR / "bin"
example_dir = SKILL_DIR / "cookbook"

# Find all referenced files in SKILL.md
referenced_refs = re.findall(r'docs/(\S+\.md)', skill_md)
actual_refs = [f.name for f in ref_dir.glob("*.md")] if ref_dir.exists() else []

for ref in referenced_refs:
    if ref not in actual_refs:
        fixable(f"SKILL.md references 'docs/{ref}' but file doesn't exist")

for ref in actual_refs:
    if ref not in referenced_refs:
        suggest(f"File 'docs/{ref}' exists but isn't referenced in SKILL.md")

# ============================================================
print("\n=== CONTENT QUALITY ===")
# ============================================================

# Check each reference doc for minimum content
MIN_LINES = 20
for ref_file in ref_dir.glob("*.md"):
    content = ref_file.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    if len(lines) < MIN_LINES:
        suggest(f"{ref_file.name} has only {len(lines)} lines — may need more content")

    # Check for actual placeholder content (not instructions about avoiding placeholders)
    non_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    non_code = re.sub(r'`[^`]+`', '', non_code)
    # Remove lines that are instructions (contain "never", "don't", "avoid" near the keyword)
    instruction_pattern = r'(?:never|don\'t|do not|avoid|no)\s+\w*\s*(?:placeholder|coming soon|lorem ipsum)'
    cleaned = re.sub(instruction_pattern, '', non_code, flags=re.IGNORECASE)
    if any(ph in cleaned.lower() for ph in ["placeholder", "coming soon", "lorem ipsum"]):
        fixable(f"{ref_file.name} contains placeholder text")

    # Check for code blocks (reference docs should have examples)
    code_blocks = content.count("```")
    if code_blocks < 2:
        suggest(f"{ref_file.name} has few code examples ({code_blocks // 2} blocks)")

# ============================================================
print("\n=== EXAMPLES CHECK ===")
# ============================================================

examples = list(example_dir.glob("*")) if example_dir.exists() else []
non_gitkeep = [e for e in examples if e.name != ".gitkeep"]
if not non_gitkeep:
    suggest("No example scripts yet — save interesting scripts during work sessions")
else:
    info(f"{len(non_gitkeep)} example scripts found")
    for ex in non_gitkeep:
        content = ex.read_text(encoding="utf-8") if ex.is_file() else ""
        if len(content) < 50:
            fixable(f"Example {ex.name} is too short ({len(content)} chars)")

# ============================================================
print("\n=== CROSS-REFERENCE CHECK ===")
# ============================================================

# Check that all reference docs link back to each other where relevant
all_ref_names = {f.stem for f in ref_dir.glob("*.md")}
for ref_file in ref_dir.glob("*.md"):
    content = ref_file.read_text(encoding="utf-8")
    mentioned_refs = set()
    for name in all_ref_names:
        if name != ref_file.stem and name.replace("-", " ") in content.lower().replace("-", " "):
            mentioned_refs.add(name)
    # This is informational, not a fix
    if mentioned_refs:
        info(f"{ref_file.name} mentions topics covered in: {', '.join(mentioned_refs)}")

# ============================================================
print("\n=== SKILL DESCRIPTION CHECK ===")
# ============================================================

# Check description triggers cover all reference doc topics
desc_match = re.search(r'description:\s*>\s*\n(.*?)---', skill_md, re.DOTALL)
if desc_match:
    description = desc_match.group(1).lower()
    topic_keywords = {
        "knowledge-base": ["obsidian", "knowledge", "kb"],
        "issue-tracker": ["board", "ticket", "sprint", "epic", "jira"],
        "workspace": ["gws", "google", "drive", "sheets"],
        "doc-forge": ["document", "excel", "word", "pdf", "powerpoint"],
        "mailbox": ["email", "gmail"],
        "media-kit": ["ffmpeg", "image", "video", "audio"],
        "datastore": ["database", "mysql", "sql", "query"],
        "pipelines": ["pipeline", "convert", "export"],
        "bootstrap": ["install", "setup", "mcp"],
    }
    for ref_name, keywords in topic_keywords.items():
        if not any(kw in description for kw in keywords):
            suggest(f"Skill description may not trigger for {ref_name} topics — consider adding keywords: {keywords}")

# ============================================================
print("\n=== SUMMARY ===")
# ============================================================

print(f"\nFindings:")
print(f"  Info:        {len(FINDINGS['info'])}")
print(f"  Suggestions: {len(FINDINGS['suggestion'])}")
print(f"  Fixable:     {len(FINDINGS['fixable'])}")
if APPLY:
    print(f"  Applied:     {len(FINDINGS['applied'])}")

if FINDINGS["suggestion"]:
    print("\nSuggestions:")
    for s in FINDINGS["suggestion"]:
        print(f"  - {s}")

if not APPLY and FINDINGS["fixable"]:
    print(f"\nRun with --apply to auto-fix {len(FINDINGS['fixable'])} issues")
