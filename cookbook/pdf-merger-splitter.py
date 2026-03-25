#!/usr/bin/env python3
"""
Cortex Example: pdf-merger-splitter
Description: Merge or split PDF files with bookmarks
Tags: pdf,merge,split,PyPDF2
Captured: 2026-03-25
Source: pdf-merger-splitter.py

Usage:
  python ~/.claude/skills/cortex/cookbook/pdf-merger-splitter.py
"""

#!/usr/bin/env python3
"""
Merge multiple PDFs into one (with bookmarks) or split a PDF by page ranges.

Usage:
    python pdf-merger-splitter.py merge file1.pdf file2.pdf -o combined.pdf
    python pdf-merger-splitter.py split input.pdf --pages 1-5,10-15 -o output_dir/
"""

import sys
import argparse
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter, PdfMerger


def merge_pdfs(files, output_path):
    merger = PdfMerger()
    for pdf_path in files:
        p = Path(pdf_path)
        if not p.exists():
            print(f"  SKIP: {p} not found")
            continue
        merger.append(str(p), outline_item=p.stem)
        print(f"  Added: {p.name}")

    merger.write(str(output_path))
    merger.close()
    print(f"\nMerged → {output_path}")


def split_pdf(input_path, page_ranges, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(input_path))
    total_pages = len(reader.pages)

    for range_str in page_ranges.split(","):
        range_str = range_str.strip()
        if "-" in range_str:
            start, end = range_str.split("-")
            start, end = int(start) - 1, int(end)
        else:
            start = int(range_str) - 1
            end = start + 1

        start = max(0, start)
        end = min(total_pages, end)

        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(reader.pages[i])

        out_name = f"pages_{start+1}-{end}.pdf"
        out_path = output_dir / out_name
        with open(out_path, "wb") as f:
            writer.write(f)
        print(f"  {out_name} ({end - start} pages)")

    print(f"\nSplit → {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Merge or split PDF files")
    sub = parser.add_subparsers(dest="command")

    merge_p = sub.add_parser("merge", help="Merge multiple PDFs")
    merge_p.add_argument("files", nargs="+", help="PDF files to merge")
    merge_p.add_argument("-o", "--output", default="merged.pdf")

    split_p = sub.add_parser("split", help="Split a PDF by page ranges")
    split_p.add_argument("file", help="Input PDF")
    split_p.add_argument("--pages", required=True, help="Page ranges: 1-5,10-15")
    split_p.add_argument("-o", "--output", default="./split_output")

    args = parser.parse_args()
    if args.command == "merge":
        merge_pdfs(args.files, args.output)
    elif args.command == "split":
        split_pdf(args.file, args.pages, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
