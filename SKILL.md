---
name: claude-claw
description: >
  Create, edit, convert, and export documents, spreadsheets, presentations, PDFs, images, videos, and audio files.
  Manage Google Workspace (Drive, Sheets, Docs, Gmail), ClickUp tasks, and MySQL databases.
  TRIGGERS: Excel, Word, PowerPoint, PDF, spreadsheet, document, presentation, slide deck,
  report, invoice, letter, resume, certificate, chart, table, CSV export,
  image resize, crop, watermark, thumbnail, screenshot, photo edit,
  video trim, compress, convert, audio extract, ffmpeg, media processing,
  email send, Gmail, Google Drive upload, Google Sheets,
  database query, SQL, MySQL, data export, data pipeline,
  file conversion, pandoc, HTML to PDF, markdown to docx,
  ClickUp tasks, sprint, time tracking,
  openpyxl, python-docx, python-pptx, reportlab, Pillow, ImageMagick.
priority: critical
---

# Claude Claw — Productivity OS

> Always-on operating system layer for document creation, tool orchestration, and productivity automation.

---

## Bootstrap (every session)

On first `/claude-claw` invocation each session, run the healthcheck script:

```bash
python ~/.claude/skills/claude-claw/scripts/healthcheck.py
```

If any check fails, attempt auto-fix or warn the user.

---

## References

Detailed tool capabilities, commands, and API surfaces. Load when working with a specific tool.

| Need | Reference |
|------|-----------|
| Google Workspace CLI | [references/gws-cli.md](references/gws-cli.md) |
| Excel / Word / PowerPoint | [references/document-creation.md](references/document-creation.md) |
| PDF tools | [references/pdf-tools.md](references/pdf-tools.md) |
| Image / Video / Audio | [references/media-tools.md](references/media-tools.md) |
| Document conversion | [references/conversion-tools.md](references/conversion-tools.md) |
| HTML/XML parsing | [references/web-parsing.md](references/web-parsing.md) |
| Email / MIME | [references/email-reference.md](references/email-reference.md) |
| Database / MySQL | [references/database-reference.md](references/database-reference.md) |
| ClickUp CLI | [references/clickup-cli.md](references/clickup-cli.md) |
| Install / troubleshoot | [references/setup.md](references/setup.md) |

## Examples

Working code blocks for common tasks. Load when executing a specific workflow.

| Task | Examples |
|------|----------|
| Excel / Word / PPT creation | [examples/office-documents.md](examples/office-documents.md) |
| PDF generation & extraction | [examples/pdf-workflows.md](examples/pdf-workflows.md) |
| Image processing | [examples/image-processing.md](examples/image-processing.md) |
| Video / audio processing | [examples/video-audio.md](examples/video-audio.md) |
| Email composition & sending | [examples/email-workflows.md](examples/email-workflows.md) |
| Database query & export | [examples/database-export.md](examples/database-export.md) |
| End-to-end pipelines | [examples/data-pipelines.md](examples/data-pipelines.md) |
| Document conversion | [examples/document-conversion.md](examples/document-conversion.md) |
| ClickUp task management | [examples/clickup-workflows.md](examples/clickup-workflows.md) |

## Tool Selection Quick Guide

### Document Creation
| Format | Library | When to use |
|--------|---------|-------------|
| Excel .xlsx | `openpyxl` | Tables, charts, styled reports, data exports |
| Word .docx | `python-docx` | Narrative text, formatted reports, letters |
| PowerPoint .pptx | `python-pptx` | Slide decks, presentations with charts |
| PDF (generate) | `reportlab` | From-scratch PDFs with precise layout |
| PDF (edit/render) | `pymupdf` (fitz) | Read, annotate, merge, split, render pages |
| PDF (extract tables) | `pdfplumber` | Extract tabular data from PDFs |
| PDF (merge/split) | `PyPDF2` | Simple merge, split, rotate, encrypt |

### Media Processing
| Task | Tool |
|------|------|
| Image manipulation (Python) | `Pillow` (PIL) |
| Image manipulation (CLI) | `magick` (ImageMagick) |
| Video/audio processing | `ffmpeg` |
| Document conversion | `pandoc` |
| PDF page screenshots | `pymupdf` (fitz) |
| Web screenshots / browser automation | Chrome DevTools MCP (`mcp__plugin_chrome-devtools-mcp_chrome-devtools__*`) — provisioned by the claude-claw bootstrap |

### Data & Integration
| Task | Tool |
|------|------|
| Google Workspace | `gws` CLI |
| ClickUp tasks | `clickup` CLI (tasks, sprints, comments, time, git) |
| MySQL database | `mcp__mcp_server_mysql__mysql_query` — provisioned by the claude-claw bootstrap |
| HTML/XML parsing | `lxml`, `beautifulsoup4` |
| Email composition | Python `email.mime` + `gws gmail users messages send` |

## Core Workflow Pattern

```
Source -> Transform (Python) -> Output file (/tmp/) -> Upload/Send (gws)
```

1. **Source**: database query, CSV, JSON, API, user input, existing file
2. **Transform**: Python processing (openpyxl, python-docx, Pillow, etc.)
3. **Output**: save to `/tmp/` as .xlsx, .docx, .pdf, .png, etc.
4. **Deliver**: `gws drive +upload /tmp/file.xlsx` or `gws gmail +send --to ... --subject ... --body ...` (convenience helpers); for full control use `gws drive files create --upload` / `gws gmail users messages send`.

