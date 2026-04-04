# Document Conversion — Pandoc Examples

Working code blocks for document conversion with pandoc CLI and Python integration.

---

## Basic Conversions

### Markdown to Word (.docx)

```bash
pandoc input.md -o output.docx
```

### Markdown to PDF

```bash
# Default (requires LaTeX: pdflatex)
pandoc input.md -o output.pdf

# With xelatex (better Unicode/font support)
pandoc input.md -o output.pdf --pdf-engine=xelatex

# With lualatex
pandoc input.md -o output.pdf --pdf-engine=lualatex

# With wkhtmltopdf (HTML intermediate, no LaTeX needed)
pandoc input.md -o output.pdf --pdf-engine=wkhtmltopdf

# With weasyprint (HTML intermediate, no LaTeX needed)
pandoc input.md -o output.pdf --pdf-engine=weasyprint
```

### Markdown to HTML (standalone with CSS)

```bash
# Standalone HTML (includes <head>, <body> tags)
pandoc input.md -o output.html --standalone

# With custom CSS
pandoc input.md -o output.html --standalone --css=style.css

# With multiple CSS files
pandoc input.md -o output.html --standalone --css=reset.css --css=main.css
```

### Markdown to PowerPoint (.pptx)

```bash
pandoc input.md -o output.pptx
```

### Word to Markdown

```bash
pandoc input.docx -o output.md

# Extract images to a media folder
pandoc input.docx -o output.md --extract-media=./media
```

### Word to PDF

```bash
pandoc input.docx -o output.pdf
pandoc input.docx -o output.pdf --pdf-engine=xelatex
```

### HTML to Word

```bash
pandoc input.html -o output.docx
```

### HTML to Markdown

```bash
pandoc input.html -o output.md

# From a URL
pandoc -f html -t markdown https://example.com/page.html -o output.md
```

### LaTeX to PDF

```bash
pandoc input.tex -o output.pdf
pandoc input.tex -o output.pdf --pdf-engine=xelatex
```

### RST to HTML

```bash
pandoc input.rst -o output.html --standalone
```

---

## Table of Contents

### PDF with TOC

```bash
pandoc input.md -o output.pdf --toc --toc-depth=3
```

### HTML with TOC

```bash
pandoc input.md -o output.html --standalone --toc --toc-depth=3
```

### Word with TOC

```bash
pandoc input.md -o output.docx --toc --toc-depth=3
```

### TOC with custom title

```bash
pandoc input.md -o output.pdf --toc --toc-depth=2 \
  --metadata toc-title="Contents"
```

---

## Custom Styling

### Word with custom reference template

```bash
# Generate default reference doc, then customize it in Word
pandoc -o custom-reference.docx --print-default-data-file reference.docx

# Use custom template for output
pandoc input.md -o output.docx --reference-doc=custom-reference.docx
```

### PowerPoint with custom reference template

```bash
# Generate default reference pptx, then customize it in PowerPoint
pandoc -o custom-reference.pptx --print-default-data-file reference.pptx

# Use custom template
pandoc input.md -o output.pptx --reference-doc=custom-reference.pptx
```

### HTML with custom CSS

```bash
pandoc input.md -o output.html --standalone --css=custom.css
```

### Syntax highlighting styles

```bash
# List available styles
pandoc --list-highlight-styles

# Use a specific style
pandoc input.md -o output.html --standalone --highlight-style=tango
pandoc input.md -o output.pdf --highlight-style=zenburn
pandoc input.md -o output.html --standalone --highlight-style=breezedark

# Dump a style for customization
pandoc --print-highlight-style=tango > my-style.theme
pandoc input.md -o output.html --standalone --highlight-style=my-style.theme
```

---

## Bibliography and Citations

### Basic citation processing

```bash
pandoc input.md -o output.pdf --citeproc --bibliography=refs.bib
```

### With CSL style

```bash
pandoc input.md -o output.pdf \
  --citeproc \
  --bibliography=refs.bib \
  --csl=apa.csl
```

### Example markdown with citations

```markdown
---
title: "My Paper"
bibliography: refs.bib
csl: chicago-author-date.csl
---

According to @smith2020, the results are significant.
Multiple sources agree [@jones2019; @doe2021, pp. 33-35].
```

### Example .bib entry

```bibtex
@article{smith2020,
  author = {Smith, John},
  title = {Important Findings},
  journal = {Journal of Examples},
  year = {2020},
  volume = {42},
  pages = {1--15}
}
```

---

## Math Support

### HTML with MathJax

```bash
pandoc input.md -o output.html --standalone --mathjax
```

### HTML with KaTeX (faster rendering)

```bash
pandoc input.md -o output.html --standalone --katex
```

### Markdown with math to PDF (LaTeX handles it natively)

```bash
pandoc input.md -o output.pdf --pdf-engine=xelatex
```

### Example markdown with math

```markdown
Inline math: $E = mc^2$

Display math:

$$
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
$$

Aligned equations:

$$
\begin{aligned}
  a &= b + c \\
  d &= e + f
\end{aligned}
$$
```

---

## Multi-File Input

### Concatenate multiple markdown files into one document

```bash
pandoc ch01.md ch02.md ch03.md -o book.pdf --toc

pandoc ch01.md ch02.md ch03.md -o book.docx --toc

# With a title page via metadata
pandoc --metadata title="My Book" \
  ch01.md ch02.md ch03.md -o book.pdf --toc
```

### Using a file list

```bash
# files.txt contains one filename per line
pandoc $(cat files.txt) -o combined.pdf
```

---

## Metadata

### YAML metadata block in markdown

```markdown
---
title: "Quarterly Report"
author: "Jane Doe"
date: "2025-01-15"
abstract: |
  This report covers Q4 performance metrics
  and projections for the coming year.
lang: en-GB
fontsize: 12pt
geometry: margin=1in
---

# Introduction

Report content here...
```

### Metadata via command-line flags

```bash
pandoc input.md -o output.pdf \
  --metadata title="My Document" \
  --metadata author="John Smith" \
  --metadata date="2025-03-15"
```

### Metadata file (separate YAML)

```bash
pandoc input.md -o output.pdf --metadata-file=meta.yaml
```

```yaml
# meta.yaml
title: "Project Docs"
author:
  - "Alice"
  - "Bob"
date: "2025-01-01"
keywords:
  - documentation
  - project
```

---

## Filters

### Lua filter example — convert all text to uppercase in headings

```bash
pandoc input.md -o output.html --standalone --lua-filter=uppercase-headings.lua
```

```lua
-- uppercase-headings.lua
function Header(el)
  el.content = pandoc.walk_inline(el.content, {
    Str = function(s)
      return pandoc.Str(string.upper(s.text))
    end
  })
  return el
end
```

### pandoc-crossref for numbered figures, tables, equations

```bash
# Install: pip install pandoc-crossref  (or OS package manager)
pandoc input.md -o output.pdf --filter pandoc-crossref --citeproc
```

```markdown
<!-- crossref example -->
See @fig:chart for details.

![Sales chart](chart.png){#fig:chart}

As shown in @tbl:data:

| Year | Revenue |
|------|---------|
| 2023 | 100M    |
| 2024 | 120M    |

: Revenue data {#tbl:data}

From @eq:energy:

$$ E = mc^2 $$ {#eq:energy}
```

---

## Slide Shows

### Markdown to reveal.js

```bash
# Basic
pandoc slides.md -o slides.html -t revealjs --standalone

# With slide level and incremental lists
pandoc slides.md -o slides.html -t revealjs --standalone \
  --slide-level=2 --incremental

# With a reveal.js theme
pandoc slides.md -o slides.html -t revealjs --standalone \
  --variable theme=moon

# Available themes: beige, black, blood, league, moon, night, serif, simple, sky, solarized, white
```

### Markdown to Beamer (LaTeX slides)

```bash
pandoc slides.md -o slides.pdf -t beamer

# With a Beamer theme
pandoc slides.md -o slides.pdf -t beamer \
  --variable theme=Madrid

# With colortheme
pandoc slides.md -o slides.pdf -t beamer \
  --variable theme=Warsaw --variable colortheme=dolphin
```

### Markdown to PowerPoint

```bash
pandoc slides.md -o slides.pptx

# With custom template
pandoc slides.md -o slides.pptx --reference-doc=template.pptx
```

### Example slide markdown

```markdown
---
title: "Project Update"
author: "Team Alpha"
date: "2025-03-15"
---

# Section One

## Slide Title

- Bullet point one
- Bullet point two

## Slide with Image

![Description](image.png)

# Section Two

## Code Slide

```python
print("Hello from the presentation")
```

## Two-Column Slide (reveal.js)

:::::::::::::: {.columns}
::: {.column width="50%"}
Left content
:::
::: {.column width="50%"}
Right content
:::
::::::::::::::
```

---

## EPUB Creation

### Basic EPUB

```bash
pandoc input.md -o book.epub
```

### Full-featured EPUB

```bash
pandoc input.md -o book.epub \
  --epub-cover-image=cover.jpg \
  --epub-metadata=metadata.xml \
  --css=epub-style.css \
  --toc --toc-depth=2 \
  --split-level=2
```

### EPUB metadata XML

```xml
<!-- metadata.xml -->
<dc:rights>Copyright 2025 Author Name</dc:rights>
<dc:language>en-US</dc:language>
<dc:subject>Technology</dc:subject>
```

### Multi-chapter EPUB

```bash
pandoc metadata.yaml ch01.md ch02.md ch03.md \
  -o book.epub \
  --epub-cover-image=cover.png \
  --css=epub.css \
  --toc --toc-depth=2
```

---

## Advanced Options

### Self-contained HTML (single file, all resources embedded)

```bash
# Pandoc 2.19+
pandoc input.md -o output.html --standalone --embed-resources

# Older pandoc
pandoc input.md -o output.html --standalone --self-contained
```

### Extract media from a docx

```bash
pandoc input.docx -o output.md --extract-media=./images
```

### Numbered sections

```bash
pandoc input.md -o output.pdf --number-sections
pandoc input.md -o output.html --standalone --number-sections
```

### Shift heading levels

```bash
# Demote all headings by 1 level (h1 becomes h2, etc.)
pandoc input.md -o output.md --shift-heading-level-by=1

# Promote all headings by 1 level (h2 becomes h1, etc.)
pandoc input.md -o output.md --shift-heading-level-by=-1
```

### Line wrapping control

```bash
# No wrapping (one paragraph per line)
pandoc input.md -o output.md --wrap=none

# Wrap at 80 columns
pandoc input.md -o output.md --wrap=auto --columns=80

# Preserve original wrapping
pandoc input.md -o output.md --wrap=preserve
```

### Standalone vs fragment

```bash
# Standalone: full document with <html>, <head>, <body>
pandoc input.md -o output.html --standalone

# Fragment: just the body content (for embedding in another page)
pandoc input.md -o output.html
```

---

## Python Integration

### Basic conversion with subprocess

```python
import subprocess
from pathlib import Path

def convert_document(input_path: str, output_path: str, extra_args: list[str] | None = None):
    """Convert a document using pandoc."""
    cmd = ["pandoc", input_path, "-o", output_path]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Pandoc failed: {result.stderr}")
    return Path(output_path)

# Markdown to PDF with TOC
convert_document("report.md", "/tmp/report.pdf", ["--toc", "--pdf-engine=xelatex"])

# Markdown to Word with custom template
convert_document("report.md", "/tmp/report.docx", ["--reference-doc=template.docx"])
```

### Convert markdown string to HTML (stdin/stdout)

```python
import subprocess

def md_to_html(markdown_text: str) -> str:
    """Convert a markdown string to HTML."""
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html"],
        input=markdown_text,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Pandoc failed: {result.stderr}")
    return result.stdout

html = md_to_html("# Hello\n\nThis is **bold** and *italic*.")
print(html)
# <h1 id="hello">Hello</h1>
# <p>This is <strong>bold</strong> and <em>italic</em>.</p>
```

### Batch convert all markdown files in a directory

```python
import subprocess
from pathlib import Path

def batch_convert(input_dir: str, output_dir: str, output_format: str = "pdf"):
    """Convert all .md files in a directory."""
    in_path = Path(input_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    for md_file in sorted(in_path.glob("*.md")):
        output_file = out_path / f"{md_file.stem}.{output_format}"
        subprocess.run(
            ["pandoc", str(md_file), "-o", str(output_file), "--standalone"],
            check=True,
        )
        print(f"Converted: {md_file.name} -> {output_file.name}")

batch_convert("./docs", "/tmp/converted", "html")
```

### Chain pandoc with other tools

```python
import subprocess
from pathlib import Path

def md_to_styled_pdf(md_path: str, css_path: str, output_path: str):
    """Markdown -> HTML (with CSS) -> styled output."""
    subprocess.run(
        [
            "pandoc", md_path, "-o", output_path,
            "--standalone",
            "--css", css_path,
            "--pdf-engine=weasyprint",
        ],
        check=True,
    )
    return Path(output_path)
```

---

## PyMuPDF as PDF Alternative (No LaTeX Required)

When pandoc PDF output requires a LaTeX installation you do not have, use pandoc to
produce HTML and then render to PDF with PyMuPDF's `fitz.Story` API.

### pandoc Markdown to HTML, then fitz Story to PDF

```python
import subprocess
import fitz  # PyMuPDF

def md_to_pdf_no_latex(md_path: str, output_pdf: str, css: str = ""):
    """Convert Markdown to PDF without LaTeX using pandoc + PyMuPDF."""
    # Step 1: Markdown -> HTML fragment via pandoc
    result = subprocess.run(
        ["pandoc", md_path, "-t", "html"],
        capture_output=True, text=True, check=True,
    )
    html_body = result.stdout

    # Step 2: Wrap in full HTML with optional CSS
    html = f"""
    <html>
    <head><style>
    body {{ font-family: sans-serif; font-size: 11pt; line-height: 1.5; }}
    h1 {{ font-size: 20pt; margin-top: 12pt; }}
    h2 {{ font-size: 16pt; margin-top: 10pt; }}
    h3 {{ font-size: 13pt; margin-top: 8pt; }}
    code {{ font-family: monospace; background: #f4f4f4; padding: 2px 4px; }}
    pre {{ background: #f4f4f4; padding: 8px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
    th {{ background: #f0f0f0; }}
    {css}
    </style></head>
    <body>{html_body}</body>
    </html>
    """

    # Step 3: Render HTML to PDF with fitz.Story
    story = fitz.Story(html)
    writer = fitz.DocumentWriter(output_pdf)
    mediabox = fitz.paper_rect("A4")
    content_rect = mediabox + (36, 36, -36, -36)  # 0.5-inch margins

    while True:
        device = writer.begin_page(mediabox)
        more, _ = story.place(content_rect)
        story.draw(device)
        writer.end_page()
        if not more:
            break

    writer.close()
    print(f"PDF written to {output_pdf}")

# Usage
md_to_pdf_no_latex("report.md", "/tmp/report.pdf")
```

### With custom CSS passed in

```python
custom_css = """
body { font-family: 'Georgia', serif; color: #333; }
h1 { color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 4pt; }
"""
md_to_pdf_no_latex("report.md", "/tmp/styled-report.pdf", css=custom_css)
```
