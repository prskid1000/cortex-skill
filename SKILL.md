---
name: claude-claw
description: >
  Reference guide for documents, spreadsheets, presentations, PDFs, images, video, audio,
  Google Workspace, ClickUp, MySQL, and media processing.
---

# Claude Claw — Productivity OS

- [Bootstrap](#bootstrap) · [Workflow](#workflow) · [Windows Notes](#windows-notes) · [Templates](#templates) · [Scripts](#scripts)

## Bootstrap

```bash
python ~/.claude/skills/claude-claw/scripts/healthcheck.py
```

## Workflow

`Source -> Transform (Python) -> Output (/tmp/) -> Deliver (gws)`

## Windows Notes

On Windows, `gws`/`clickup` are `.cmd` shims. Use `shutil.which()`:

```python
import shutil, subprocess
gws = shutil.which("gws")
subprocess.run([gws, "drive", "files", "list"], capture_output=True, text=True)
```

## File Map

- **CREATE a document**
  - Excel (.xlsx)
    - API: [document-creation.md § openpyxl](references/document-creation.md#11-workbook--worksheet-operations) — [Cells](references/document-creation.md#12-cell-operations) · [Styling](references/document-creation.md#13-styling--formatting) · [Cond.Fmt](references/document-creation.md#14-conditional-formatting) · [Validation](references/document-creation.md#15-data-validation) · [Charts](references/document-creation.md#16-charts) · [Tables](references/document-creation.md#17-tables) · [Named Ranges](references/document-creation.md#18-defined-names--named-ranges) · [Filters](references/document-creation.md#19-auto-filter--sorting) · [Images](references/document-creation.md#110-images) · [Print](references/document-creation.md#111-print-settings) · [Formulas](references/document-creation.md#112-formula-reference) · [Protection](references/document-creation.md#113-protection)
    - Ex: [office-documents.md § Excel](examples/office-documents.md#excel-openpyxl)
  - Word (.docx)
    - API: [document-creation.md § python-docx](references/document-creation.md#21-document-operations) — [Paragraphs](references/document-creation.md#22-paragraphs--runs) · [Tables](references/document-creation.md#23-tables) · [Styles](references/document-creation.md#24-styles) · [Images](references/document-creation.md#25-images) · [Headers](references/document-creation.md#26-headersfooters) · [Layout](references/document-creation.md#27-page-layout) · [Sections](references/document-creation.md#28-sections) · [Lists](references/document-creation.md#29-lists) · [Links](references/document-creation.md#210-hyperlinks) · [TOC](references/document-creation.md#211-table-of-contents)
    - Ex: [office-documents.md § Word](examples/office-documents.md#word-python-docx)
  - PowerPoint (.pptx)
    - API: [document-creation.md § python-pptx](references/document-creation.md#31-presentation-operations) — [Slides](references/document-creation.md#32-slides) · [Shapes](references/document-creation.md#33-shapes) · [Text](references/document-creation.md#34-text-frames--paragraphs) · [Tables](references/document-creation.md#35-tables) · [Charts](references/document-creation.md#36-charts) · [Images](references/document-creation.md#37-images) · [Layouts](references/document-creation.md#38-slide-layouts)
    - Ex: [office-documents.md § PowerPoint](examples/office-documents.md#powerpoint-python-pptx)
  - PDF from scratch
    - API: [pdf-tools.md § reportlab](references/pdf-tools.md#4-reportlab----pdf-generation)
    - Ex: [pdf-workflows.md § reportlab](examples/pdf-workflows.md#reportlab--generate-pdfs-from-scratch)
  - Google Doc / Sheet / Slides
    - API: [gws-cli.md § Docs](references/gws-cli.md#docs) · [Sheets](references/gws-cli.md#sheets) · [Slides](references/gws-cli.md#slides)
    - Ex: [google-workspace.md](examples/google-workspace.md#google-docs-gws-cli)
- **READ / EXTRACT**
  - PDF → text
    - API: [pdf-tools.md § PyMuPDF](references/pdf-tools.md#1-pymupdf-fitz----pdf-read--edit--render)
    - Ex: [pdf-workflows.md § PyMuPDF](examples/pdf-workflows.md#pymupdf-fitz--readeditmanipulate)
  - PDF → tables
    - API: [pdf-tools.md § pdfplumber](references/pdf-tools.md#3-pdfplumber----pdf-data-extraction)
    - Ex: [pdf-workflows.md § pdfplumber](examples/pdf-workflows.md#pdfplumber----extract-data)
  - PDF → images → [pdf-tools.md § PyMuPDF](references/pdf-tools.md#1-pymupdf-fitz----pdf-read--edit--render)
  - Excel → data → [document-creation.md § Cells](references/document-creation.md#12-cell-operations)
  - HTML/XML
    - [web-parsing.md § lxml](references/web-parsing.md#lxml) (XPath, XSLT, validation)
    - [web-parsing.md § BeautifulSoup4](references/web-parsing.md#beautifulsoup4) (CSS selectors)
- **EDIT a document**
  - PDF annotate/redact → [pdf-tools.md § PyMuPDF](references/pdf-tools.md#1-pymupdf-fitz----pdf-read--edit--render)
  - PDF merge/split → [pdf-tools.md § PyPDF2](references/pdf-tools.md#2-pypdf2----pdf-merge--split--transform)
  - Excel/Word/PPT → same libs as CREATE
  - Which PDF tool? → [pdf-tools.md § Quick Selection Guide](references/pdf-tools.md#quick-selection-guide)
- **CONVERT format**
  - Any ↔ Any (Pandoc)
    - API: [conversion-tools.md § Syntax](references/conversion-tools.md#command-syntax) — [Input](references/conversion-tools.md#input-formats-45) · [Output](references/conversion-tools.md#output-formats-60) · [Templates](references/conversion-tools.md#templates) · [TOC](references/conversion-tools.md#table-of-contents) · [Bib](references/conversion-tools.md#bibliography--citations) · [Math](references/conversion-tools.md#math-rendering) · [Filters](references/conversion-tools.md#filters) · [PDF Engines](references/conversion-tools.md#pdf-engines) · [Slides](references/conversion-tools.md#slide-shows) · [EPUB](references/conversion-tools.md#epub-creation) · [Metadata](references/conversion-tools.md#metadata)
    - Ex: [document-conversion.md § Basic](examples/document-conversion.md#basic-conversions) · [Styling](examples/document-conversion.md#custom-styling) · [Bib](examples/document-conversion.md#bibliography-and-citations) · [Math](examples/document-conversion.md#math-support) · [Slides](examples/document-conversion.md#slide-shows) · [EPUB](examples/document-conversion.md#epub-creation) · [Python](examples/document-conversion.md#python-integration)
  - PDF without LaTeX → [Ex § PyMuPDF](examples/document-conversion.md#pymupdf-as-pdf-alternative-no-latex-required)
- **SEND / COMPOSE email**
  - Build MIME (plain, HTML, attachments, inline images, threading)
    - API: [email-reference.md § Critical Rules](references/email-reference.md#critical-rules) · [Python MIME](references/email-reference.md#python-mime-emailmime)
    - Ex: [email-workflows.md § MIME](examples/email-workflows.md#python-email-composition-mime)
  - Send / reply / forward via Gmail
    - API: [email-reference.md § Gmail CLI](references/email-reference.md#gmail-cli-gws-gmail) (`+send`, `+reply`, `+forward`)
    - Full Gmail API: [gws-cli.md § Gmail](references/gws-cli.md#gmail)
    - Ex: [email-workflows.md § Gmail](examples/email-workflows.md#gmail-via-gws-cli) · [Full Workflow](examples/email-workflows.md#full-workflow-generate-report-compose-email-send-with-attachment)
- **PROCESS images**
  - Pillow (Python)
    - API: [media-tools.md § Formats](references/media-tools.md#11-supported-formats) · [Modes](references/media-tools.md#12-image-modes) · [Image](references/media-tools.md#13-image-class----all-methods-and-properties) · [Draw](references/media-tools.md#14-imagedraw) · [Font](references/media-tools.md#15-imagefont) · [Filter](references/media-tools.md#16-imagefilter) · [Enhance](references/media-tools.md#17-imageenhance) · [Ops](references/media-tools.md#18-imageops) · [Chops](references/media-tools.md#19-imagechops-channel-operations)
    - Ex: [image-processing.md § Pillow](examples/image-processing.md#pillow-python)
  - ImageMagick (CLI)
    - API: [media-tools.md § ImageMagick](references/media-tools.md#21-identify) (2.1–2.16)
    - Ex: [image-processing.md § ImageMagick](examples/image-processing.md#imagemagick-magick-cli)
- **PROCESS video / audio**
  - FFmpeg
    - API: [media-tools.md § FFmpeg](references/media-tools.md#31-basic-conversion) (3.1–3.11)
    - Ex: [video-audio.md](examples/video-audio.md#video-conversion) — [Conversion](examples/video-audio.md#video-conversion) · [Extraction](examples/video-audio.md#extraction--trimming) · [Merging](examples/video-audio.md#merging--concatenation) · [Thumbnails](examples/video-audio.md#thumbnails--frames) · [GIF](examples/video-audio.md#gif--animated-formats) · [Compression](examples/video-audio.md#compression--scaling) · [Overlays](examples/video-audio.md#overlays--effects) · [Speed](examples/video-audio.md#speed--direction) · [Audio](examples/video-audio.md#audio-operations)
- **GOOGLE WORKSPACE**
  - API: [gws-cli.md](references/gws-cli.md) — [Critical Rules](references/gws-cli.md#critical-rules-read-first--violations-cause-errors) · [Syntax](references/gws-cli.md#general-syntax) · [Flags](references/gws-cli.md#global-cli-flags) · [+helpers](references/gws-cli.md#ergonomic-helper-commands) · [Auth](references/gws-cli.md#auth)
  - Services: [Drive](references/gws-cli.md#drive) · [Sheets](references/gws-cli.md#sheets) · [Docs](references/gws-cli.md#docs) · [Slides](references/gws-cli.md#slides) · [Gmail](references/gws-cli.md#gmail) · [Calendar](references/gws-cli.md#calendar) · [Tasks](references/gws-cli.md#tasks)
  - Ex: [google-workspace.md](examples/google-workspace.md#google-docs-gws-cli)
- **MANAGE tasks (ClickUp)**
  - API: [clickup-cli.md](references/clickup-cli.md) — [Conventions](references/clickup-cli.md#conventions-important) · [Setup](references/clickup-cli.md#setup) · [Tasks](references/clickup-cli.md#task-management) · [Status](references/clickup-cli.md#status-management) · [Sprint](references/clickup-cli.md#sprint-management) · [Comments](references/clickup-cli.md#comments) · [Time](references/clickup-cli.md#time-tracking) · [Fields](references/clickup-cli.md#custom-fields) · [Git](references/clickup-cli.md#git-integration)
  - Ex: [clickup-workflows.md](examples/clickup-workflows.md#read-a-task) — [Read](examples/clickup-workflows.md#read-a-task) · [Search](examples/clickup-workflows.md#search-tasks) · [Create](examples/clickup-workflows.md#create-a-task) · [Update](examples/clickup-workflows.md#update-task-status) · [Sprint](examples/clickup-workflows.md#sprint-view) · [Comments](examples/clickup-workflows.md#comments) · [Time](examples/clickup-workflows.md#time-tracking) · [Git](examples/clickup-workflows.md#git-integration) · [Dev Workflow](examples/clickup-workflows.md#development-workflow-pattern)
- **DATA PIPELINE**
  - Ex: [data-pipelines.md](examples/data-pipelines.md) — [CSV→Excel→Sheets](examples/data-pipelines.md#csv-to-styled-excel-to-google-sheets) · [PDF→Tables→Excel](examples/data-pipelines.md#pdf-to-extract-tables-to-excel) · [Sheets↔Local](examples/data-pipelines.md#google-sheet-download-modify-upload-back) · [DB→Excel](examples/data-pipelines.md#database-to-excel-report-styled) · [DB→Sheets](examples/data-pipelines.md#database-to-google-sheets-direct) · [JSON→Excel](examples/data-pipelines.md#json-to-excel) · [HTML→Excel](examples/data-pipelines.md#html-table-to-excel-beautifulsoup) · [Excel→PDF](examples/data-pipelines.md#excel-to-pdf-reportlab-table) · [Full Pipeline](examples/data-pipelines.md#full-pipeline-db-query-to-process-to-excel--pdf-to-upload-drive-to-email)
- **QUERY database**
  - MySQL MCP → [setup.md § MCP](references/setup.md#4-mcp-servers)
- **SETUP / INSTALL**
  - [setup.md](references/setup.md) — [Python pkgs](references/setup.md#1-python-packages) · [CLI tools](references/setup.md#2-cli-tools) · [GWS auth](references/setup.md#3-google-workspace-gws-auth) · [MCP](references/setup.md#4-mcp-servers) · [LSP](references/setup.md#5-lsp-plugins) · [Notes](references/setup.md#6-notes)
  - [healthcheck.py](scripts/healthcheck.py) — verify + auto-fix all deps
- **PATCH Claude Code**
  - [claude-patcher.md](references/claude-patcher.md) — [What](references/claude-patcher.md#what-it-does) · [Constants](references/claude-patcher.md#patchable-constants) · [Usage](references/claude-patcher.md#usage) · [How](references/claude-patcher.md#how-it-works) · [Limits](references/claude-patcher.md#limitations)

## Templates

- Reference: [references/_TEMPLATE.md](references/_TEMPLATE.md) — Critical Rules → API sections → Quick Reference
- Example: [examples/_TEMPLATE.md](examples/_TEMPLATE.md) — Numbered workflows (Basic → Styled → Pipeline)
- To add: copy template → fill placeholders → add to File Map above → update healthcheck + setup.md

## Scripts

- [healthcheck.py](scripts/healthcheck.py) — verify packages, CLI tools, MCP servers, LSP plugins; auto-fix Windows patches
- [claude-patcher.js](scripts/claude-patcher.js) — Claude Code binary patcher (context window, output limits)
