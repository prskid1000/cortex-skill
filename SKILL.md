---
name: claude-claw
description: >
  Reference guide for documents, spreadsheets, presentations, PDFs, images, video, audio,
  Google Workspace, ClickUp, MySQL, and media processing.
---

# Claude Claw — Productivity OS

## Contents

1. [Bootstrap](#bootstrap)
2. [Workflow](#workflow)
3. [Windows Notes](#windows-notes)
4. [References](#references)
5. [Examples](#examples)
6. [Templates](#templates)
7. [Scripts](#scripts)
8. [Quick Decision Tree](#quick-decision-tree)

## Bootstrap

```bash
python ~/.claude/skills/claude-claw/scripts/healthcheck.py
```

## Workflow

`Source -> Transform (Python) -> Output (/tmp/) -> Deliver (gws)`

## Windows Notes

On Windows, `gws` and `clickup` are `.cmd` shims that `subprocess.run(["gws", ...])` cannot find directly. Use `shutil.which()` to resolve the full path first:

```python
import shutil, subprocess
gws = shutil.which("gws")
subprocess.run([gws, "drive", "files", "list"], capture_output=True, text=True)
```

Alternatively, call `node` with the JS entry point directly.

## References

### [gws-cli.md](references/gws-cli.md) — Google Workspace CLI

| Section | Topics |
|---------|--------|
| Critical Rules | Params vs JSON, positional args, Gmail users path |
| General Syntax / Global Flags | Command structure, output formats |
| Ergonomic `+helper` Commands | `+send`, `+triage`, `+reply` shortcuts |
| Auth | Login, status, refresh, multiple accounts |
| Drive | Files, folders, upload, download, permissions, sharing |
| Sheets | Read, write, append, formatting, named ranges |
| Docs | Create, read, update, insert, export |
| Slides | Create, pages, shapes, text, images |
| Gmail | Messages, drafts, labels, threads, search operators |
| Calendar | Events, list, create, update, attendees |
| Tasks | Task lists, tasks, create, complete |

### [document-creation.md](references/document-creation.md) — Excel / Word / PowerPoint

| Section | Topics |
|---------|--------|
| **openpyxl** (1.1–1.14) | Workbook, cells, styling, conditional formatting, charts, tables, images, print, formulas, protection |
| **python-docx** (2.1–2.12) | Document, paragraphs, tables, styles, images, headers/footers, page layout, sections |
| **python-pptx** (3.1–3.11) | Presentation, slides, shapes, text, tables, charts, images, layouts, masters |

### [pdf-tools.md](references/pdf-tools.md) — PDF Read / Edit / Generate

| Section | Topics |
|---------|--------|
| PyMuPDF (fitz) | Document, pages, text extraction, rendering, annotations, forms, merge, split, redaction |
| PyPDF2 | Merge, split, rotate, encrypt/decrypt, metadata, bookmarks |
| pdfplumber | Table extraction, text with positional data, visual debugging |
| reportlab | Canvas, PLATYPUS, SimpleDocTemplate, tables, paragraphs, styles, charts |
| Quick Selection Guide | Which tool for which task |

### [media-tools.md](references/media-tools.md) — Images / Video / Audio

| Section | Topics |
|---------|--------|
| **Pillow** (1.1–1.10) | Formats, modes, Image class, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps, ImageChops |
| **ImageMagick** (2.1–2.16) | Resize, crop, rotate, format convert, composite, effects, batch, montage |
| **FFmpeg** (3.1–3.11) | Convert, extract, trim, merge, compress, stream, filters, subtitles |

### [conversion-tools.md](references/conversion-tools.md) — Pandoc

| Section | Topics |
|---------|--------|
| Command Syntax | Input/output formats (~45 in, ~60+ out) |
| Templates / TOC / Bibliography | Custom styling, citations, math rendering |
| Filters / PDF Engines / Slides | Lua filters, weasyprint/wkhtmltopdf, reveal.js/beamer |

### [web-parsing.md](references/web-parsing.md) — HTML / XML

| Section | Topics |
|---------|--------|
| lxml | ElementTree API, XPath, XSLT, validation (XSD, RelaxNG) |
| BeautifulSoup4 | CSS selectors, tree navigation, modification, encoding |

### [email-reference.md](references/email-reference.md) — Email / MIME

| Section | Topics |
|---------|--------|
| Critical Rules | MIME encoding, Content-ID, Gmail API gotchas |
| Python MIME | MIMEText, MIMEMultipart, attachments, inline images, reply threading |
| Gmail CLI | `+send`, `+triage`, `+reply` helpers (full API → gws-cli.md) |

### [clickup-cli.md](references/clickup-cli.md) — ClickUp CLI

| Section | Topics |
|---------|--------|
| Conventions / Setup | Task IDs positional, priority integers, date formats |
| Task / Status / Sprint | View, create, edit, search, status transitions |
| Comments / Time / Custom Fields | Add, list, log time, set fields |
| Git Integration | Branch auto-detection, commit linking |

### [setup.md](references/setup.md) — Installation Guide

| Section | Topics |
|---------|--------|
| Python Packages | 10 pip packages (openpyxl, pymupdf, reportlab, etc.) |
| CLI Tools | gws, clickup, git, ffmpeg, pandoc, magick, node |
| GWS Auth | Login, verify, token refresh, multiple accounts |
| MCP Servers | MySQL, Chrome DevTools, ClickUp |
| LSP Plugins | Pyright, TypeScript, jdtls, JetBrains kotlin-lsp + Windows fix |

### [claude-patcher.md](references/claude-patcher.md) — Binary Patcher

| Section | Topics |
|---------|--------|
| Patchable Constants | Context window, max output, autocompact, summary max |
| Usage / Limitations | Scan, patch, restore; re-run after Claude Code updates |

---

## Examples

### [office-documents.md](examples/office-documents.md) — Excel / Word / PowerPoint

| Section | What it builds |
|---------|---------------|
| Excel (openpyxl) | Basic workbook, styled report, conditional formatting, charts |
| Word (python-docx) | Document with tables, styles, images, headers |
| PowerPoint (python-pptx) | Presentation with slides, shapes, charts |

### [pdf-workflows.md](examples/pdf-workflows.md) — PDF Workflows

| Section | What it builds |
|---------|---------------|
| reportlab | Simple PDF, styled report, tables |
| PyMuPDF (fitz) | Text extraction, splitting, merging, annotations |
| PyPDF2/pypdf | Merge, split, transform |
| pdfplumber | Table extraction to data |

### [google-workspace.md](examples/google-workspace.md) — GWS CLI

| Section | What it builds |
|---------|---------------|
| Google Docs | Create and populate via gws CLI |

### [image-processing.md](examples/image-processing.md) — Image Processing

| Section | What it builds |
|---------|---------------|
| Pillow | Resize, crop, rotate, filters, watermark, logo overlay, enhancement |
| ImageMagick | CLI batch processing, compositing |

### [video-audio.md](examples/video-audio.md) — Video / Audio

| Section | What it builds |
|---------|---------------|
| Video | Conversion, extraction, trimming, merging, compression |
| Effects | Overlays, speed changes, thumbnails, GIF creation |

### [email-workflows.md](examples/email-workflows.md) — Email

| Section | What it builds |
|---------|---------------|
| Python MIME | Plain text, HTML, attachments, inline images, reply threading |
| Gmail CLI | Sending, reading, complex workflows |
| Full Workflow | Generate report → compose email → send with attachment |

### [data-pipelines.md](examples/data-pipelines.md) — Data Pipelines

| Section | What it builds |
|---------|---------------|
| CSV → Excel → Sheets | Styled Excel upload to Google Sheets |
| PDF → Tables → Excel | Extract PDF tables to spreadsheet |
| Sheets ↔ Local | Download, modify, re-upload |
| DB → Excel/Sheets | Database query to styled report |
| JSON/HTML → Excel | Parse and convert to spreadsheet |

### [document-conversion.md](examples/document-conversion.md) — Pandoc Conversions

| Section | What it builds |
|---------|---------------|
| Basic Conversions | Markdown ↔ Word ↔ PDF ↔ HTML ↔ PowerPoint |
| Advanced | TOC, custom styling, bibliography, math, multi-file, metadata, filters |

### [clickup-workflows.md](examples/clickup-workflows.md) — ClickUp

| Section | What it builds |
|---------|---------------|
| Task CRUD | Read, search, list, create, update status |
| Sprint / Comments / Time | Sprint view, add comments, log time |
| Git Integration | Branch workflow, commit linking |

---

## Templates

Use these when adding new reference or example files to the skill.

| Template | Location | Structure |
|----------|----------|-----------|
| Reference | [references/_TEMPLATE.md](references/_TEMPLATE.md) | TOC → Critical Rules → API sections (tabular) → Quick Reference cheatsheet |
| Example | [examples/_TEMPLATE.md](examples/_TEMPLATE.md) | TOC → Numbered workflows (Basic → Styled → Pipeline), each copy-paste runnable |

**To add a new file:**

1. Copy the template → `references/[topic].md` or `examples/[topic].md`
2. Replace all `[bracketed]` placeholders
3. Add the file to the matching section above (with section index table)
4. If it needs a new pip/npm package, add to `scripts/healthcheck.py` and `references/setup.md`

## Scripts

| Script | Purpose |
|--------|---------|
| [scripts/healthcheck.py](scripts/healthcheck.py) | Verify packages, CLI tools, MCP servers, LSP plugins; auto-fix Windows LSP patches |
| [scripts/claude-patcher.js](scripts/claude-patcher.js) | Claude Code binary patcher (context window, output limits) |

## Quick Decision Tree

- **CREATE a document?** → [document-creation.md](references/document-creation.md) (Excel/Word/PPT) or [pdf-tools.md](references/pdf-tools.md) (PDF)
- **CONVERT between formats?** → [conversion-tools.md](references/conversion-tools.md) (Pandoc)
- **SEND email?** → [email-reference.md](references/email-reference.md) (MIME + Gmail)
- **USE Google Drive/Sheets/Docs?** → [gws-cli.md](references/gws-cli.md)
- **PROCESS images?** → [media-tools.md](references/media-tools.md) (Pillow section)
- **PROCESS video/audio?** → [media-tools.md](references/media-tools.md) (FFmpeg section)
- **PARSE HTML/XML?** → [web-parsing.md](references/web-parsing.md)
- **MANAGE tasks?** → [clickup-cli.md](references/clickup-cli.md)
- **Need WORKING CODE?** → `examples/` folder (matching topic name)
