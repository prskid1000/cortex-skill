#!/usr/bin/env python3
"""
Cortex Example: md-to-styled-docx
Description: Convert Markdown to styled Word via pandoc
Tags: markdown,docx,pandoc,conversion
Captured: 2026-03-25
Source: md-to-styled-docx.py

Usage:
  python ~/.claude/skills/cortex/cookbook/md-to-styled-docx.py
"""

#!/usr/bin/env python3
"""
Convert Markdown files to styled Word documents using pandoc.
Supports custom reference-doc for corporate branding, TOC, and numbered sections.

Usage:
    python md-to-styled-docx.py input.md [output.docx]
    python md-to-styled-docx.py input.md output.docx --reference-doc template.docx --toc
    python md-to-styled-docx.py input_dir/ output_dir/ --batch
"""

import sys
import argparse
import subprocess
from pathlib import Path


def convert_md_to_docx(md_path, docx_path, reference_doc=None, toc=False, number_sections=False):
    cmd = ["pandoc", str(md_path), "-o", str(docx_path)]

    if reference_doc and Path(reference_doc).exists():
        cmd += ["--reference-doc", str(reference_doc)]

    if toc:
        cmd.append("--toc")

    if number_sections:
        cmd.append("--number-sections")

    # Better defaults
    cmd += ["--wrap=none", "--highlight-style=tango"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {md_path.name}: {result.stderr[:200]}")
        return False

    print(f"  {md_path.name} → {docx_path.name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to styled Word via pandoc")
    parser.add_argument("input", help="Input .md file or directory")
    parser.add_argument("output", nargs="?", help="Output .docx file or directory")
    parser.add_argument("--reference-doc", help="Word template for styling")
    parser.add_argument("--toc", action="store_true", help="Include table of contents")
    parser.add_argument("--number-sections", action="store_true", help="Number headings")
    parser.add_argument("--batch", action="store_true", help="Convert all .md files in directory")
    args = parser.parse_args()

    input_path = Path(args.input)

    if args.batch and input_path.is_dir():
        output_dir = Path(args.output) if args.output else input_path / "docx"
        output_dir.mkdir(parents=True, exist_ok=True)
        md_files = sorted(input_path.glob("*.md"))
        print(f"Converting {len(md_files)} Markdown files...")
        for md in md_files:
            out = output_dir / md.with_suffix(".docx").name
            convert_md_to_docx(md, out, args.reference_doc, args.toc, args.number_sections)
        print(f"\nDone → {output_dir}")
    elif input_path.is_file():
        output = Path(args.output) if args.output else input_path.with_suffix(".docx")
        convert_md_to_docx(input_path, output, args.reference_doc, args.toc, args.number_sections)
    else:
        print(f"Error: {input_path} not found")
        sys.exit(1)


if __name__ == "__main__":
    main()
