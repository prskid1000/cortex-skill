#!/usr/bin/env python3
"""
Cortex Example: batch-format-converter
Description: Batch convert documents between formats via pandoc
Tags: pandoc,conversion,batch,documents
Captured: 2026-03-25
Source: batch-format-converter.py

Usage:
  python ~/.claude/skills/cortex/cookbook/batch-format-converter.py
"""

#!/usr/bin/env python3
"""
Batch convert documents between formats using pandoc.
Supports: MD, DOCX, HTML, PDF, RST, LaTeX, EPUB.

Usage:
    python batch-format-converter.py input_dir/ --from md --to docx
    python batch-format-converter.py input_dir/ --from docx --to md --output output_dir/
    python batch-format-converter.py input_dir/ --from html --to pdf --extract-media
"""

import argparse
import subprocess
from pathlib import Path

FORMAT_EXTS = {
    "md": ".md", "markdown": ".md",
    "docx": ".docx",
    "html": ".html",
    "pdf": ".pdf",
    "rst": ".rst",
    "latex": ".tex", "tex": ".tex",
    "epub": ".epub",
    "txt": ".txt",
}


def convert_file(input_path, output_path, from_fmt, to_fmt, extract_media=False, extra_args=None):
    cmd = ["pandoc", str(input_path), "-o", str(output_path)]

    if from_fmt:
        cmd += ["-f", from_fmt]
    if to_fmt:
        cmd += ["-t", to_fmt]

    if extract_media:
        media_dir = output_path.parent / f"{output_path.stem}_media"
        cmd += [f"--extract-media={media_dir}"]

    if to_fmt == "pdf":
        cmd += ["--pdf-engine=xelatex"]

    cmd += ["--wrap=none"]

    if extra_args:
        cmd += extra_args

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {input_path.name}: {result.stderr[:200]}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Batch convert documents with pandoc")
    parser.add_argument("input_dir", help="Input directory")
    parser.add_argument("--from", dest="from_fmt", required=True, help="Source format")
    parser.add_argument("--to", dest="to_fmt", required=True, help="Target format")
    parser.add_argument("--output", help="Output directory (default: input_dir/converted)")
    parser.add_argument("--extract-media", action="store_true", help="Extract images to subfolder")
    parser.add_argument("--toc", action="store_true", help="Add table of contents")
    parser.add_argument("--number-sections", action="store_true", help="Number sections")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    src_ext = FORMAT_EXTS.get(args.from_fmt, f".{args.from_fmt}")
    dst_ext = FORMAT_EXTS.get(args.to_fmt, f".{args.to_fmt}")
    output_dir = Path(args.output) if args.output else input_dir / "converted"
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(input_dir.glob(f"*{src_ext}"))
    if not files:
        print(f"No {src_ext} files found in {input_dir}")
        return

    extra = []
    if args.toc:
        extra.append("--toc")
    if args.number_sections:
        extra.append("--number-sections")

    print(f"Converting {len(files)} files: {src_ext} → {dst_ext}")
    success = 0
    for f in files:
        out = output_dir / f"{f.stem}{dst_ext}"
        if convert_file(f, out, args.from_fmt, args.to_fmt, args.extract_media, extra):
            print(f"  {f.name} → {out.name}")
            success += 1

    print(f"\nDone: {success}/{len(files)} converted → {output_dir}")


if __name__ == "__main__":
    main()
