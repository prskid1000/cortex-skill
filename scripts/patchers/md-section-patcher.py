"""Idempotent markdown section patcher — inject, update, or remove a named
block of content in a markdown file.

Sections are delimited by HTML comment markers, so Markdown viewers don't
render them. Content outside the markers is untouched; content between them
is fully owned by this patcher.

    <!-- SECTION:begin -->
    ...managed content...
    <!-- SECTION:end -->

Use cases: bootstrapping `~/.claude/CLAUDE.md` with skill-managed blocks,
maintaining auto-generated tables of contents, syncing license headers, etc.

Usage:
    md-section-patcher.py apply  --target FILE --section NAME --source CONTENT_FILE
    md-section-patcher.py status --target FILE --section NAME [--source CONTENT_FILE]
    md-section-patcher.py remove --target FILE --section NAME

Exit codes:
    0 = success / in-sync / nothing to do
    1 = handled error
    3 = status: drifted or missing (for CI / scripting)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def markers(section: str) -> tuple[str, str]:
    return f'<!-- {section}:begin -->', f'<!-- {section}:end -->'


def find_block(text: str, section: str) -> tuple[int, int] | None:
    """Return (start_index_of_begin_marker, end_index_after_end_marker) or None."""
    begin, end = markers(section)
    pattern = re.compile(
        r'(?P<begin>' + re.escape(begin) + r')\s*(?P<body>.*?)\s*(?P<end>' + re.escape(end) + r')',
        re.DOTALL,
    )
    m = pattern.search(text)
    if not m:
        return None
    return m.start(), m.end()


def extract_body(text: str, section: str) -> str | None:
    begin, end = markers(section)
    pattern = re.compile(
        r'' + re.escape(begin) + r'\s*(.*?)\s*' + re.escape(end),
        re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def compose_block(section: str, body: str) -> str:
    begin, end = markers(section)
    return f'{begin}\n{body.strip()}\n{end}'


def cmd_apply(target: Path, section: str, source: Path) -> int:
    if not source.exists():
        print(f'[FAIL] source not found: {source}')
        return 1
    desired_body = source.read_text(encoding='utf-8').strip()
    desired_block = compose_block(section, desired_body)

    if not target.exists():
        target.write_text(desired_block + '\n', encoding='utf-8')
        print(f'[PASS] created {target} with "{section}" block ({len(desired_body)} chars)')
        return 0

    current = target.read_text(encoding='utf-8')
    span = find_block(current, section)

    if span is None:
        prefix = desired_block + '\n\n'
        new_text = prefix + current.lstrip('\n') if current else desired_block + '\n'
        target.write_text(new_text, encoding='utf-8')
        print(f'[PASS] prepended "{section}" block to {target}')
        return 0

    current_body = extract_body(current, section) or ''
    if current_body == desired_body:
        print(f'[PASS] "{section}" block in {target} is already in sync')
        return 0

    start, end_idx = span
    new_text = current[:start] + desired_block + current[end_idx:]
    target.write_text(new_text, encoding='utf-8')
    print(f'[PASS] updated "{section}" block in {target} ({len(desired_body)} chars)')
    return 0


def cmd_status(target: Path, section: str, source: Path | None) -> int:
    if not target.exists():
        print(f'[MISSING] {target} does not exist')
        return 3
    text = target.read_text(encoding='utf-8')
    body = extract_body(text, section)
    if body is None:
        print(f'[MISSING] "{section}" block not found in {target}')
        return 3
    print(f'[PRESENT] "{section}" block in {target} ({len(body)} chars)')
    if source is None:
        return 0
    if not source.exists():
        print(f'[WARN] source not found for comparison: {source}')
        return 0
    desired = source.read_text(encoding='utf-8').strip()
    if body == desired:
        print('[IN-SYNC] content matches source')
        return 0
    print('[DRIFTED] content differs from source — run `apply` to update')
    return 3


def cmd_remove(target: Path, section: str) -> int:
    if not target.exists():
        print(f'[PASS] {target} does not exist — nothing to remove')
        return 0
    current = target.read_text(encoding='utf-8')
    span = find_block(current, section)
    if span is None:
        print(f'[PASS] "{section}" block not present in {target}')
        return 0
    start, end_idx = span
    new_text = current[:start] + current[end_idx:]
    new_text = re.sub(r'\n{3,}', '\n\n', new_text)
    target.write_text(new_text, encoding='utf-8')
    print(f'[PASS] removed "{section}" block from {target}')
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or '').split('\n\n')[0])
    sub = ap.add_subparsers(dest='command', required=True)

    a = sub.add_parser('apply', help='inject or update a section')
    a.add_argument('--target', required=True, type=Path)
    a.add_argument('--section', required=True)
    a.add_argument('--source', required=True, type=Path)

    s = sub.add_parser('status', help='check whether section is present / in-sync')
    s.add_argument('--target', required=True, type=Path)
    s.add_argument('--section', required=True)
    s.add_argument('--source', type=Path)

    r = sub.add_parser('remove', help='strip the named section from target')
    r.add_argument('--target', required=True, type=Path)
    r.add_argument('--section', required=True)

    args = ap.parse_args()

    target = args.target.expanduser()
    if args.command == 'apply':
        return cmd_apply(target, args.section, args.source.expanduser())
    if args.command == 'status':
        src = args.source.expanduser() if args.source else None
        return cmd_status(target, args.section, src)
    if args.command == 'remove':
        return cmd_remove(target, args.section)
    return 1


if __name__ == '__main__':
    sys.exit(main())
