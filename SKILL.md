---
name: claude-claw
description: >
  Productivity OS index for spreadsheets, documents, PDFs, media, and automation.
---

# Claude Claw — Productivity OS

> All Python deps + the `claw` CLI live in a skill-local venv at `~/.claude/skills/claude-claw/.venv/`. 
> Use `claw` on PATH as the primary entry point.

- [Bootstrap](#bootstrap) · [Workflow](#workflow) · [Documentation Index](#documentation-index) · [Scripts](#scripts)

## Bootstrap

```bash
python ~/.claude/skills/claude-claw/scripts/healthcheck.py --install     # create .venv + install everything
```

## Workflow

`Source -> Transform (claw) -> Output (/tmp/) -> Deliver (gws)`

## Documentation Index

### 📊 Excel (.xlsx) — [Full Ref](references/claw/xlsx.md)
- [new](references/claw/xlsx.md#11-new) — Create blank workbook
- [from-csv](references/claw/xlsx.md#12-from-csv) — Multi-CSV to sheets
- [from-json](references/claw/xlsx.md#13-from-json) — JSON array import
- [from-html](references/claw/xlsx.md#14-from-html) — Scrape HTML tables
- [from-pdf](references/claw/xlsx.md#15-from-pdf) — PDF table extraction
- [read](references/claw/xlsx.md#21-read) — Cells to JSON/CSV
- [to-csv](references/claw/xlsx.md#22-to-csv) — Sheet to CSV
- [to-pdf](references/claw/xlsx.md#23-to-pdf) — Render via LibreOffice
- [sql](references/claw/xlsx.md#24-sql) — Query sheets (DuckDB)
- [stat](references/claw/xlsx.md#25-stat) — Column summary stats
- [append](references/claw/xlsx.md#31-append) — Add rows to sheet
- [style](references/claw/xlsx.md#41-style) — Format font/fill/border
- [freeze](references/claw/xlsx.md#42-freeze) — Lock header panes
- [filter](references/claw/xlsx.md#43-filter) — Enable Excel auto-filter
- [conditional](references/claw/xlsx.md#44-conditional) — Cell-is/Formula rules
- [format](references/claw/xlsx.md#45-format) — Set number format
- [table](references/claw/xlsx.md#46-table) — Define structured tables
- [chart](references/claw/xlsx.md#47-chart) — Add Bar/Line/Pie
- [validate](references/claw/xlsx.md#51-validate) — Dropdowns & constraints
- [name](references/claw/xlsx.md#52-name) — Manage defined names

### 📝 Word (.docx) — [Full Ref](references/claw/docx.md)
- [new](references/claw/docx.md#11-new) — Create blank doc
- [from-md](references/claw/docx.md#12-from-md) — Markdown to docx
- [read](references/claw/docx.md#21-read) — Text/JSON structure extraction
- [add-heading](references/claw/docx.md#31-add-heading) — Insert level 1-9
- [add-paragraph](references/claw/docx.md#32-add-paragraph) — Insert formatted text
- [add-table](references/claw/docx.md#33-add-table) — Insert CSV/JSON data
- [add-image](references/claw/docx.md#34-add-image) — Insert scaled image
- [insert](references/claw/docx.md#35-insert) — Pagebreaks & structural
- [style](references/claw/docx.md#41-style) — Apply paragraph styles
- [header/footer](references/claw/docx.md#43-header) — Set section text
- [toc](references/claw/docx.md#45-toc) — Insert field code

### 📄 PDF — [Full Ref](references/claw/pdf.md)
- [from-html/md](references/claw/pdf.md#from-html) — Render source to PDF
- [qr/barcode](references/claw/pdf.md#qr) — Generate visual codes
- [extract-text](references/claw/pdf.md#extract-text) — Plain/JSON text dump
- [extract-tables](references/claw/pdf.md#extract-tables) — Grid data extraction
- [info](references/claw/pdf.md#info) — Metadata & encryption
- [search](references/claw/pdf.md#search) — Regex term search
- [merge](references/claw/pdf.md#merge) — Join multiple files
- [split](references/claw/pdf.md#split) — Explode by page
- [rotate/crop](references/claw/pdf.md#rotate) — Transform page geometry
- [render](references/claw/pdf.md#render) — Page to Image
- [watermark](references/claw/pdf.md#watermark) — Stamp text/logos
- [redact](references/claw/pdf.md#redact) — Sanitize sensitive info
- [encrypt/decrypt](references/claw/pdf.md#encrypt-decrypt) — Manage file security

### 🌐 Web & HTML — [Full Ref](references/claw/html.md)
- [fetch](references/claw/web.md#fetch) — HTTP download with retry
- [select](references/claw/html.md#select) — CSS/XPath query
- [text](references/claw/html.md#text) — Clean article extraction
- [strip/unwrap](references/claw/html.md#strip) — Tree cleanup/pruning
- [sanitize](references/claw/html.md#sanitize) — Allow-list HTML cleaning
- [xpath](references/claw/xml.md#xpath) — XML query engine
- [xslt](references/claw/xml.md#transform) — XML/XSL transformation
- [convert](references/claw/convert.md#convert) — Pandoc universal converter
- [md2pdf-nolatex](references/claw/convert.md#md2pdf-nolatex) — Fast PDF rendering

### 🎬 Media — [Full Ref](references/claw/media.md)
- [resize/fit](references/claw/img.md#resize-fit) — Scale images (geometry)
- [to-webp/jpeg](references/claw/img.md#convert) — Image format encoding
- [exif](references/claw/img.md#exif) — Metadata read/strip
- [info](references/claw/media.md#info) — FFprobe stream dump
- [extract-audio](references/claw/media.md#extract) — Video to MP3/WAV
- [thumbnail](references/claw/media.md#extract) — Frame/Contact sheet grab
- [trim/compress](references/claw/media.md#transform) — Cut/Shrink video

### ☁️ Google Drive — [Full Ref](references/claw/drive.md)
- [upload](references/claw/drive.md#11-upload) — Upload local file (auto-converts office formats)
- [download](references/claw/drive.md#21-download) — Fetch Drive file (binary blobs as-is; Google-native via `--as pdf|xlsx|docx|md|...`)
- [info](references/claw/drive.md#23-info) — File metadata (name/mime/size/parents/owners)
- [copy](references/claw/drive.md#12-copy) — Duplicate a Drive file
- [list](references/claw/drive.md#22-list) — Query Drive files
- [move](references/claw/drive.md#31-move) — Move file between folders
- [rename](references/claw/drive.md#32-rename) — Rename Drive file
- [delete](references/claw/drive.md#33-delete) — Permanently delete (no Trash)
- [share](references/claw/drive.md#41-share) — Grant access (user/domain/anyone)
- [share-list](references/claw/drive.md#42-share-list) — List permissions
- [share-revoke](references/claw/drive.md#43-share-revoke) — Remove user access

### 🚀 Automation
- [browser launch](references/claw/browser.md#launch) — CDP-enabled Chrome/Edge
- [pipeline run](references/claw/pipeline.md#run) — Execute YAML DAG
- [doc create](references/claw/doc.md#create) — New Google Doc
- [email send](references/claw/email.md#send) — Compose & send (Gmail)

---

## Scripts

- [scripts/claw/](scripts/claw/) — The core `claw` CLI package.
- [scripts/healthcheck.py](scripts/healthcheck.py) — Environment verification and install.
- [scripts/patchers/](scripts/patchers/) — System/binary patchers.
- [scripts/wrappers/](scripts/wrappers/) — Insiders/local-model launchers.
