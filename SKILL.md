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

## References

### [gws-cli.md](references/gws-cli.md) — Google Workspace CLI

- [Critical Rules](references/gws-cli.md#critical-rules-read-first--violations-cause-errors)
- [General Syntax](references/gws-cli.md#general-syntax)
- [Global CLI Flags](references/gws-cli.md#global-cli-flags)
- [`+helper` Commands](references/gws-cli.md#ergonomic-helper-commands)
- [Auth](references/gws-cli.md#auth)
- [Drive](references/gws-cli.md#drive)
- [Sheets](references/gws-cli.md#sheets)
- [Docs](references/gws-cli.md#docs)
- [Slides](references/gws-cli.md#slides)
- [Gmail](references/gws-cli.md#gmail)
- [Calendar](references/gws-cli.md#calendar)
- [Tasks](references/gws-cli.md#tasks)

### [document-creation.md](references/document-creation.md) — Excel / Word / PowerPoint

- **openpyxl:** [Workbook](references/document-creation.md#11-workbook--worksheet-operations) · [Cells](references/document-creation.md#12-cell-operations) · [Styling](references/document-creation.md#13-styling--formatting) · [Conditional Fmt](references/document-creation.md#14-conditional-formatting) · [Validation](references/document-creation.md#15-data-validation) · [Charts](references/document-creation.md#16-charts) · [Tables](references/document-creation.md#17-tables) · [Named Ranges](references/document-creation.md#18-defined-names--named-ranges) · [Filters](references/document-creation.md#19-auto-filter--sorting) · [Images](references/document-creation.md#110-images) · [Print](references/document-creation.md#111-print-settings) · [Formulas](references/document-creation.md#112-formula-reference) · [Protection](references/document-creation.md#113-protection) · [Comments](references/document-creation.md#114-comments)
- **python-docx:** [Document](references/document-creation.md#21-document-operations) · [Paragraphs](references/document-creation.md#22-paragraphs--runs) · [Tables](references/document-creation.md#23-tables) · [Styles](references/document-creation.md#24-styles) · [Images](references/document-creation.md#25-images) · [Headers/Footers](references/document-creation.md#26-headersfooters) · [Page Layout](references/document-creation.md#27-page-layout) · [Sections](references/document-creation.md#28-sections) · [Lists](references/document-creation.md#29-lists) · [Hyperlinks](references/document-creation.md#210-hyperlinks) · [TOC](references/document-creation.md#211-table-of-contents) · [Fields](references/document-creation.md#212-fields)
- **python-pptx:** [Presentation](references/document-creation.md#31-presentation-operations) · [Slides](references/document-creation.md#32-slides) · [Shapes](references/document-creation.md#33-shapes) · [Text](references/document-creation.md#34-text-frames--paragraphs) · [Tables](references/document-creation.md#35-tables) · [Charts](references/document-creation.md#36-charts) · [Images](references/document-creation.md#37-images) · [Layouts](references/document-creation.md#38-slide-layouts) · [Masters](references/document-creation.md#39-slide-masters) · [Placeholders](references/document-creation.md#310-placeholders) · [Animations](references/document-creation.md#311-notes--properties)

### [pdf-tools.md](references/pdf-tools.md) — PDF Read / Edit / Generate

- [PyMuPDF (fitz)](references/pdf-tools.md#1-pymupdf-fitz----pdf-read--edit--render)
- [PyPDF2](references/pdf-tools.md#2-pypdf2----pdf-merge--split--transform)
- [pdfplumber](references/pdf-tools.md#3-pdfplumber----pdf-data-extraction)
- [reportlab](references/pdf-tools.md#4-reportlab----pdf-generation)
- [Quick Selection Guide](references/pdf-tools.md#quick-selection-guide)

### [media-tools.md](references/media-tools.md) — Images / Video / Audio

- **Pillow:** [Formats](references/media-tools.md#11-supported-formats) · [Modes](references/media-tools.md#12-image-modes) · [Image Class](references/media-tools.md#13-image-class----all-methods-and-properties) · [ImageDraw](references/media-tools.md#14-imagedraw) · [ImageFont](references/media-tools.md#15-imagefont) · [ImageFilter](references/media-tools.md#16-imagefilter) · [ImageEnhance](references/media-tools.md#17-imageenhance) · [ImageOps](references/media-tools.md#18-imageops) · [ImageChops](references/media-tools.md#19-imagechops-channel-operations)
- **ImageMagick:** [CLI Reference](references/media-tools.md#21-identify) (2.1–2.16)
- **FFmpeg:** [CLI Reference](references/media-tools.md#31-basic-conversion) (3.1–3.11)

### [conversion-tools.md](references/conversion-tools.md) — Pandoc

- [Command Syntax](references/conversion-tools.md#command-syntax) · [Input Formats](references/conversion-tools.md#input-formats-45) · [Output Formats](references/conversion-tools.md#output-formats-60) · [Templates](references/conversion-tools.md#templates) · [TOC](references/conversion-tools.md#table-of-contents) · [Bibliography](references/conversion-tools.md#bibliography--citations) · [Math](references/conversion-tools.md#math-rendering) · [Filters](references/conversion-tools.md#filters) · [PDF Engines](references/conversion-tools.md#pdf-engines) · [Slides](references/conversion-tools.md#slide-shows) · [EPUB](references/conversion-tools.md#epub-creation) · [Metadata](references/conversion-tools.md#metadata)

### [web-parsing.md](references/web-parsing.md) — HTML / XML

- [lxml](references/web-parsing.md#lxml) (ElementTree, XPath, XSLT, validation)
- [BeautifulSoup4](references/web-parsing.md#beautifulsoup4) (CSS selectors, tree navigation)

### [email-reference.md](references/email-reference.md) — Email / MIME

- [Critical Rules](references/email-reference.md#critical-rules)
- [Python MIME](references/email-reference.md#python-mime-emailmime) (MIMEText, MIMEMultipart, attachments, inline images, threading)
- [Gmail CLI](references/email-reference.md#gmail-cli-gws-gmail) (`+send`, `+triage`, `+reply` — full API → gws-cli.md)

### [clickup-cli.md](references/clickup-cli.md) — ClickUp CLI

- [Conventions](references/clickup-cli.md#conventions-important) · [Setup](references/clickup-cli.md#setup) · [Output Flags](references/clickup-cli.md#output-flags-most-commands) · [Tasks](references/clickup-cli.md#task-management) · [Status](references/clickup-cli.md#status-management) · [Sprint](references/clickup-cli.md#sprint-management) · [Comments](references/clickup-cli.md#comments) · [Time](references/clickup-cli.md#time-tracking) · [Custom Fields](references/clickup-cli.md#custom-fields) · [Git](references/clickup-cli.md#git-integration)

### [setup.md](references/setup.md) — Installation Guide

- [Python Packages](references/setup.md#1-python-packages) · [CLI Tools](references/setup.md#2-cli-tools) · [GWS Auth](references/setup.md#3-google-workspace-gws-auth) · [MCP Servers](references/setup.md#4-mcp-servers) · [LSP Plugins](references/setup.md#5-lsp-plugins) · [Notes](references/setup.md#6-notes)

### [claude-patcher.md](references/claude-patcher.md) — Binary Patcher

- [What It Does](references/claude-patcher.md#what-it-does) · [Constants](references/claude-patcher.md#patchable-constants) · [Usage](references/claude-patcher.md#usage) · [How It Works](references/claude-patcher.md#how-it-works) · [Limitations](references/claude-patcher.md#limitations)

---

## Examples

### [office-documents.md](examples/office-documents.md) — Excel / Word / PowerPoint

- [Excel (openpyxl)](examples/office-documents.md#excel-openpyxl) · [Word (python-docx)](examples/office-documents.md#word-python-docx) · [PowerPoint (python-pptx)](examples/office-documents.md#powerpoint-python-pptx)

### [pdf-workflows.md](examples/pdf-workflows.md) — PDF Workflows

- [reportlab](examples/pdf-workflows.md#reportlab--generate-pdfs-from-scratch) · [PyMuPDF](examples/pdf-workflows.md#pymupdf-fitz--readeditmanipulate) · [PyPDF2](examples/pdf-workflows.md#pypdf2pypdf----mergesplittransform) · [pdfplumber](examples/pdf-workflows.md#pdfplumber----extract-data)

### [google-workspace.md](examples/google-workspace.md) — GWS CLI

- [Google Docs](examples/google-workspace.md#google-docs-gws-cli)

### [image-processing.md](examples/image-processing.md) — Image Processing

- [Pillow](examples/image-processing.md#pillow-python) · [ImageMagick](examples/image-processing.md#imagemagick-magick-cli)

### [video-audio.md](examples/video-audio.md) — Video / Audio

- [Conversion](examples/video-audio.md#video-conversion) · [Extraction](examples/video-audio.md#extraction--trimming) · [Merging](examples/video-audio.md#merging--concatenation) · [Thumbnails](examples/video-audio.md#thumbnails--frames) · [GIF](examples/video-audio.md#gif--animated-formats) · [Compression](examples/video-audio.md#compression--scaling) · [Overlays](examples/video-audio.md#overlays--effects) · [Speed](examples/video-audio.md#speed--direction) · [Audio](examples/video-audio.md#audio-operations) · [Advanced](examples/video-audio.md#advanced)

### [email-workflows.md](examples/email-workflows.md) — Email

- [Python MIME](examples/email-workflows.md#python-email-composition-mime) · [Gmail CLI](examples/email-workflows.md#gmail-via-gws-cli) · [Full Workflow](examples/email-workflows.md#full-workflow-generate-report-compose-email-send-with-attachment)

### [data-pipelines.md](examples/data-pipelines.md) — Data Pipelines

- [CSV→Excel→Sheets](examples/data-pipelines.md#csv-to-styled-excel-to-google-sheets) · [PDF→Tables→Excel](examples/data-pipelines.md#pdf-to-extract-tables-to-excel) · [Sheets↔Local](examples/data-pipelines.md#google-sheet-download-modify-upload-back) · [DB→Excel](examples/data-pipelines.md#database-to-excel-report-styled) · [DB→Sheets](examples/data-pipelines.md#database-to-google-sheets-direct) · [JSON→Excel](examples/data-pipelines.md#json-to-excel) · [HTML→Excel](examples/data-pipelines.md#html-table-to-excel-beautifulsoup) · [Excel→PDF](examples/data-pipelines.md#excel-to-pdf-reportlab-table) · [MD→PDF](examples/data-pipelines.md#markdown-to-pdf-pandoc) · [Full Pipeline](examples/data-pipelines.md#full-pipeline-db-query-to-process-to-excel--pdf-to-upload-drive-to-email)

### [document-conversion.md](examples/document-conversion.md) — Pandoc Conversions

- [Basic](examples/document-conversion.md#basic-conversions) · [TOC](examples/document-conversion.md#table-of-contents) · [Styling](examples/document-conversion.md#custom-styling) · [Bibliography](examples/document-conversion.md#bibliography-and-citations) · [Math](examples/document-conversion.md#math-support) · [Multi-File](examples/document-conversion.md#multi-file-input) · [Metadata](examples/document-conversion.md#metadata) · [Filters](examples/document-conversion.md#filters) · [Slides](examples/document-conversion.md#slide-shows) · [EPUB](examples/document-conversion.md#epub-creation) · [Python](examples/document-conversion.md#python-integration) · [PyMuPDF PDF](examples/document-conversion.md#pymupdf-as-pdf-alternative-no-latex-required)

### [clickup-workflows.md](examples/clickup-workflows.md) — ClickUp

- [Read](examples/clickup-workflows.md#read-a-task) · [Search](examples/clickup-workflows.md#search-tasks) · [List](examples/clickup-workflows.md#list-tasks-in-a-list) · [Create](examples/clickup-workflows.md#create-a-task) · [Update](examples/clickup-workflows.md#update-task-status) · [Sprint](examples/clickup-workflows.md#sprint-view) · [Comments](examples/clickup-workflows.md#comments) · [Time](examples/clickup-workflows.md#time-tracking) · [Fields](examples/clickup-workflows.md#custom-fields) · [Git](examples/clickup-workflows.md#git-integration) · [Workspace](examples/clickup-workflows.md#workspace) · [Dev Workflow](examples/clickup-workflows.md#development-workflow-pattern)

---

## Templates

| Template | Location | Structure |
|----------|----------|-----------|
| Reference | [references/_TEMPLATE.md](references/_TEMPLATE.md) | TOC → Critical Rules → API sections (tabular) → Quick Reference |
| Example | [examples/_TEMPLATE.md](examples/_TEMPLATE.md) | TOC → Numbered workflows (Basic → Styled → Pipeline) |

**To add a new file:** copy template → fill placeholders → add section links here → update healthcheck + setup.md if needed.

## Scripts

| Script | Purpose |
|--------|---------|
| [scripts/healthcheck.py](scripts/healthcheck.py) | Verify packages, CLI tools, MCP servers, LSP plugins; auto-fix Windows patches |
| [scripts/claude-patcher.js](scripts/claude-patcher.js) | Claude Code binary patcher (context window, output limits) |

## Decision Tree

- **CREATE a document**
  - Excel → [document-creation.md § openpyxl](references/document-creation.md#11-workbook--worksheet-operations) · [Ex](examples/office-documents.md#excel-openpyxl)
  - Word → [document-creation.md § python-docx](references/document-creation.md#21-document-operations) · [Ex](examples/office-documents.md#word-python-docx)
  - PowerPoint → [document-creation.md § python-pptx](references/document-creation.md#31-presentation-operations) · [Ex](examples/office-documents.md#powerpoint-python-pptx)
  - PDF → [pdf-tools.md § reportlab](references/pdf-tools.md#4-reportlab----pdf-generation) · [Ex](examples/pdf-workflows.md#reportlab--generate-pdfs-from-scratch)
  - Google Doc/Sheet/Slides → [gws-cli.md § Docs](references/gws-cli.md#docs) · [Sheets](references/gws-cli.md#sheets) · [Slides](references/gws-cli.md#slides) · [Ex](examples/google-workspace.md#google-docs-gws-cli)
- **READ / EXTRACT**
  - PDF → text → [pdf-tools.md § PyMuPDF](references/pdf-tools.md#1-pymupdf-fitz----pdf-read--edit--render) · [Ex](examples/pdf-workflows.md#pymupdf-fitz--readeditmanipulate)
  - PDF → tables → [pdf-tools.md § pdfplumber](references/pdf-tools.md#3-pdfplumber----pdf-data-extraction) · [Ex](examples/pdf-workflows.md#pdfplumber----extract-data)
  - PDF → images → [pdf-tools.md § PyMuPDF](references/pdf-tools.md#1-pymupdf-fitz----pdf-read--edit--render)
  - Excel → data → [document-creation.md § Cells](references/document-creation.md#12-cell-operations)
  - HTML/XML → [web-parsing.md § lxml](references/web-parsing.md#lxml) · [BS4](references/web-parsing.md#beautifulsoup4)
- **EDIT a document**
  - PDF annotate/redact → [pdf-tools.md § PyMuPDF](references/pdf-tools.md#1-pymupdf-fitz----pdf-read--edit--render)
  - PDF merge/split → [pdf-tools.md § PyPDF2](references/pdf-tools.md#2-pypdf2----pdf-merge--split--transform)
  - Excel/Word/PPT → same libs as CREATE
- **CONVERT format**
  - Any ↔ Any → [conversion-tools.md § Syntax](references/conversion-tools.md#command-syntax) · [Ex](examples/document-conversion.md#basic-conversions)
  - TOC/bibliography/styling → [conversion-tools.md § Templates](references/conversion-tools.md#templates) · [TOC](references/conversion-tools.md#table-of-contents) · [Bib](references/conversion-tools.md#bibliography--citations) · [Ex](examples/document-conversion.md#custom-styling)
  - PDF without LaTeX → [Ex § PyMuPDF](examples/document-conversion.md#pymupdf-as-pdf-alternative-no-latex-required)
- **SEND / COMPOSE email**
  - Build MIME → [email-reference.md § Python MIME](references/email-reference.md#python-mime-emailmime) · [Ex](examples/email-workflows.md#python-email-composition-mime)
  - Send Gmail → [email-reference.md § Gmail CLI](references/email-reference.md#gmail-cli-gws-gmail) · [Full API](references/gws-cli.md#gmail) · [Ex](examples/email-workflows.md#gmail-via-gws-cli)
  - Reply/forward → [email-reference.md § Gmail CLI](references/email-reference.md#gmail-cli-gws-gmail) (`+reply`, `+forward`)
- **PROCESS images**
  - Pillow → [media-tools.md § Image](references/media-tools.md#13-image-class----all-methods-and-properties) · [Draw](references/media-tools.md#14-imagedraw) · [Filter](references/media-tools.md#16-imagefilter) · [Enhance](references/media-tools.md#17-imageenhance) · [Ops](references/media-tools.md#18-imageops) · [Ex](examples/image-processing.md#pillow-python)
  - ImageMagick → [media-tools.md § ImageMagick](references/media-tools.md#21-identify) · [Ex](examples/image-processing.md#imagemagick-magick-cli)
- **PROCESS video / audio**
  - Convert/trim/merge → [media-tools.md § FFmpeg](references/media-tools.md#31-basic-conversion) · [Ex](examples/video-audio.md#video-conversion)
  - Extract → [Ex § Extraction](examples/video-audio.md#extraction--trimming)
  - GIF/thumbnails → [Ex § GIF](examples/video-audio.md#gif--animated-formats) · [Thumbnails](examples/video-audio.md#thumbnails--frames)
  - Effects/speed → [Ex § Overlays](examples/video-audio.md#overlays--effects) · [Speed](examples/video-audio.md#speed--direction)
  - Audio → [Ex § Audio](examples/video-audio.md#audio-operations)
- **GOOGLE WORKSPACE**
  - [Drive](references/gws-cli.md#drive) · [Sheets](references/gws-cli.md#sheets) · [Docs](references/gws-cli.md#docs) · [Slides](references/gws-cli.md#slides) · [Gmail](references/gws-cli.md#gmail) · [Calendar](references/gws-cli.md#calendar) · [Tasks](references/gws-cli.md#tasks)
  - [Auth](references/gws-cli.md#auth) · [+helpers](references/gws-cli.md#ergonomic-helper-commands) · [Critical Rules](references/gws-cli.md#critical-rules-read-first--violations-cause-errors)
- **MANAGE tasks (ClickUp)**
  - CRUD → [clickup-cli.md § Tasks](references/clickup-cli.md#task-management) · [Ex](examples/clickup-workflows.md#read-a-task)
  - Sprint/status → [clickup-cli.md § Sprint](references/clickup-cli.md#sprint-management) · [Status](references/clickup-cli.md#status-management)
  - Comments/time → [clickup-cli.md § Comments](references/clickup-cli.md#comments) · [Time](references/clickup-cli.md#time-tracking)
  - Git → [clickup-cli.md § Git](references/clickup-cli.md#git-integration) · [Ex](examples/clickup-workflows.md#git-integration)
- **DATA PIPELINE**
  - CSV → Excel → Sheets → [Ex](examples/data-pipelines.md#csv-to-styled-excel-to-google-sheets)
  - PDF → tables → Excel → [Ex](examples/data-pipelines.md#pdf-to-extract-tables-to-excel)
  - Sheets ↔ local → [Ex](examples/data-pipelines.md#google-sheet-download-modify-upload-back)
  - DB → report → email → [Ex](examples/data-pipelines.md#full-pipeline-db-query-to-process-to-excel--pdf-to-upload-drive-to-email)
- **QUERY database**
  - MySQL MCP → [setup.md § MCP](references/setup.md#4-mcp-servers)
- **SETUP / INSTALL**
  - [Python pkgs](references/setup.md#1-python-packages) · [CLI tools](references/setup.md#2-cli-tools) · [GWS auth](references/setup.md#3-google-workspace-gws-auth) · [MCP](references/setup.md#4-mcp-servers) · [LSP](references/setup.md#5-lsp-plugins) · [healthcheck.py](scripts/healthcheck.py)
- **PATCH Claude Code**
  - [claude-patcher.md § Usage](references/claude-patcher.md#usage)
