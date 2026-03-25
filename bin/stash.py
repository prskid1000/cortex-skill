#!/usr/bin/env python3
"""
Cortex Script Capture: Save interesting scripts to cookbook/ for reuse.

Usage:
  python ~/.claude/skills/cortex/bin/stash.py --name "csv_to_excel" --source /tmp/my_script.py
  python ~/.claude/skills/cortex/bin/stash.py --name "pdf_merger" --source /tmp/merge.py --tags "pdf,merge"
  python ~/.claude/skills/cortex/bin/stash.py --list
  python ~/.claude/skills/cortex/bin/stash.py --search "excel"

The script will:
1. Copy the source file to cookbook/
2. Add a header comment with metadata
3. Genericize project-specific values (paths, IDs, etc.)
4. Update the cookbook index
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime

EXAMPLES_DIR = Path.home() / ".claude" / "skills" / "cortex" / "cookbook"
INDEX_FILE = EXAMPLES_DIR / "_index.md"

def ensure_dir():
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)

def list_examples():
    ensure_dir()
    examples = sorted(EXAMPLES_DIR.glob("*.py"))
    if not examples:
        print("No examples saved yet.")
        return

    print(f"\n{'Name':<30} {'Tags':<20} {'Date':<12} {'Lines':<6}")
    print("-" * 70)
    for ex in examples:
        content = ex.read_text(encoding="utf-8")
        # Parse header
        tags = ""
        date = ""
        tag_match = re.search(r'Tags:\s*(.+)', content)
        date_match = re.search(r'Captured:\s*(.+)', content)
        if tag_match:
            tags = tag_match.group(1).strip()
        if date_match:
            date = date_match.group(1).strip()
        lines = len(content.split("\n"))
        print(f"  {ex.stem:<30} {tags:<20} {date:<12} {lines:<6}")

def search_examples(query):
    ensure_dir()
    query_lower = query.lower()
    matches = []
    for ex in EXAMPLES_DIR.glob("*.py"):
        content = ex.read_text(encoding="utf-8").lower()
        if query_lower in content or query_lower in ex.stem.lower():
            matches.append(ex)

    if not matches:
        print(f"No examples matching '{query}'")
    else:
        print(f"\nFound {len(matches)} matching examples:")
        for m in matches:
            print(f"  - {m.name}")

def genericize(content):
    """Replace project-specific values with placeholders."""
    # Replace absolute paths with generic ones
    content = re.sub(r'C:\\Users\\[^\\]+', r'C:\\Users\\<USER>', content)
    content = re.sub(r'/home/[^/]+', '/home/<USER>', content)

    # Replace Google Drive IDs (long alphanumeric strings)
    content = re.sub(r'["\']([a-zA-Z0-9_-]{25,})["\']', '"<FILE_ID>"', content)

    # Replace email addresses (but keep domain)
    content = re.sub(r'[\w.]+@([\w.]+)', r'user@\1', content)

    # Replace dates with placeholder
    content = re.sub(r'\d{4}-\d{2}-\d{2}', '<YYYY-MM-DD>', content)

    return content

def capture(name, source, tags="", description=""):
    ensure_dir()
    source_path = Path(source)
    if not source_path.exists():
        print(f"Error: Source file not found: {source}")
        sys.exit(1)

    content = source_path.read_text(encoding="utf-8")

    # Genericize
    generic_content = genericize(content)

    # Add header
    header = f'''#!/usr/bin/env python3
"""
Cortex Example: {name}
Description: {description or f"Reusable script for {name.replace('_', ' ')}"}
Tags: {tags}
Captured: {datetime.now().strftime("%Y-%m-%d")}
Source: {source_path.name}

Usage:
  python ~/.claude/skills/cortex/cookbook/{name}.py
"""

'''

    # Write
    dest = EXAMPLES_DIR / f"{name}.py"
    dest.write_text(header + generic_content, encoding="utf-8")
    print(f"Saved: {dest}")

    # Update index
    update_index()

def update_index():
    """Rebuild the examples index."""
    ensure_dir()
    examples = sorted(EXAMPLES_DIR.glob("*.py"))

    lines = ["# Cortex Examples Index\n"]
    lines.append(f"Updated: {datetime.now().strftime('%Y-%m-%d')}\n")
    lines.append(f"| Name | Tags | Description |")
    lines.append(f"|------|------|-------------|")

    for ex in examples:
        content = ex.read_text(encoding="utf-8")
        tags = ""
        desc = ""
        tag_match = re.search(r'Tags:\s*(.+)', content)
        desc_match = re.search(r'Description:\s*(.+)', content)
        if tag_match:
            tags = tag_match.group(1).strip()
        if desc_match:
            desc = desc_match.group(1).strip()
        lines.append(f"| [{ex.stem}]({ex.name}) | {tags} | {desc} |")

    INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Index updated: {INDEX_FILE}")

def main():
    parser = argparse.ArgumentParser(description="Capture reusable scripts to Cortex examples")
    parser.add_argument("--name", help="Name for the example (no extension)")
    parser.add_argument("--source", help="Source file path")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--description", default="", help="Brief description")
    parser.add_argument("--list", action="store_true", help="List all examples")
    parser.add_argument("--search", help="Search examples by keyword")
    parser.add_argument("--rebuild-index", action="store_true", help="Rebuild the index")

    args = parser.parse_args()

    if args.list:
        list_examples()
    elif args.search:
        search_examples(args.search)
    elif args.rebuild_index:
        update_index()
    elif args.name and args.source:
        capture(args.name, args.source, args.tags, args.description)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
