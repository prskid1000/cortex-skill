# `claw` Recipes — One-Liner Cookbook

> Single-line (and occasionally two-line) shell recipes over `claw`. Grouped by user intent. For multi-step flows see [claw-pipelines.md](claw-pipelines.md); for API detail see [references/claw/](../references/claw/).

## Contents

- **CREATE a file** — `claw xlsx|docx|pptx|pdf|img|doc|sheet` ([§xlsx](../references/claw/xlsx.md) · [§docx](../references/claw/docx.md) · [§pptx](../references/claw/pptx.md) · [§pdf](../references/claw/pdf.md) · [§img](../references/claw/img.md) · [§doc](../references/claw/doc.md))
  - [New blank workbook / doc / deck / PDF](#create-blank)
  - [From data — CSV / JSON / Markdown / HTML / PDF tables](#create-from-data)
  - [Build a PDF from HTML or Markdown](#create-pdf-from-source)
- **READ / EXTRACT** — `claw xlsx read`, `claw pdf extract-*`, `claw docx read`, `claw html select`
  - [Dump cells, ranges, tables, text](#read-cells-and-text)
  - [Pull tables, images, forms out of PDFs](#read--extract-from-pdf)
  - [Scrape HTML / query XML](#read-web-and-xml)
  - [Inspect metadata, EXIF, media streams](#read-metadata)
- **TRANSFORM / EDIT** — `claw xlsx style|filter|freeze`, `claw pdf merge|split|rotate`, `claw img resize|crop|watermark`
  - [Style, freeze, filter, chart a workbook](#transform-workbook)
  - [Merge, split, rotate, watermark, redact PDFs](#transform-pdf)
  - [Resize, crop, watermark, convert images](#transform-image)
  - [Insert headings, tables, images into docs/decks](#transform-docs-and-decks)
- **CONVERT format** — `claw convert`, `claw xlsx to-*`, `claw doc export`, `claw img convert`
  - [Any ↔ Any via pandoc](#convert-via-pandoc)
  - [Office ↔ PDF / HTML / CSV / Markdown](#convert-office)
  - [Image / media format swaps](#convert-image--media)
- **PROCESS video / audio** — `claw media`
  - [Trim, concat, scale, compress, gif, subs](#media-ops)
- **SEND / PUBLISH** — `claw email`, `claw doc|sheet share`, `gws drive`
  - [Send mail with attachments / HTML / inline images](#send-email)
  - [Upload to Drive, share links, round-trip Sheets](#send-via-drive-and-sheets)
- **AUTOMATE browser** — `claw browser`
  - [Launch Chrome/Edge with remote debugging](#browser-ops)
- **PIPELINES** — `claw pipeline run` ([§pipeline](../references/claw/pipeline.md))
  - [Run, validate, graph a recipe](#pipeline-ops)
- **DIAGNOSE / CONFIG**
  - [`claw doctor`, `claw schema`, `--examples`, `--dry-run`](#diagnose)
- **Quick Reference** — [top 20 cheat sheet](#quick-reference-cheat-sheet)

---

## CREATE

### Create blank

> Uses: [xlsx new](../scripts/claw/src/claw/xlsx/new.py) · [docx new](../scripts/claw/src/claw/docx/new.py) · [pptx new](../scripts/claw/src/claw/pptx/new.py) · [doc create](../scripts/claw/src/claw/doc/create.py) · `pdf new` (**NOT IMPLEMENTED**)

New empty artefacts on disk. Use `--force` to overwrite, `--mkdir` to auto-create parents. See [claw/xlsx](../references/claw/xlsx.md), [claw/docx](../references/claw/docx.md), [claw/pptx](../references/claw/pptx.md).

```bash
# Blank xlsx with two named sheets
claw xlsx new /tmp/report.xlsx --sheet Summary --sheet Details

# Blank docx, inherit brand styles from a template
claw docx new /tmp/brief.docx --template ~/templates/corporate.docx

# Blank 16:9 deck
claw pptx new /tmp/deck.pptx --template ~/templates/brand.pptx --16:9

# Blank PDF (single empty A4 page)
claw pdf new /tmp/cover.pdf --pages 1 --size A4

# Brand-new Google Doc (optionally populated + shared in one shot)
claw doc create --title "Q3 Report"
```

### Create from data

> Uses: [xlsx from-csv](../scripts/claw/src/claw/xlsx/from_csv.py) · [xlsx from-json](../scripts/claw/src/claw/xlsx/from_json.py) · [docx from-md](../scripts/claw/src/claw/docx/from_md.py) · [doc create](../scripts/claw/src/claw/doc/create.py) · `xlsx from-html` / `xlsx from-pdf` / `pptx from-outline` (**NOT IMPLEMENTED**)

One-shot ingestion from CSV / JSON / Markdown / HTML / PDF. Body text lives in a file or stdin; pipe into `--data -` to skip the temp file. See [claw/xlsx §CREATE](../references/claw/xlsx.md#1-create).

```bash
# CSV(s) → xlsx (one sheet per input)
claw xlsx from-csv /tmp/sales.xlsx data/q1.csv data/q2.csv --types infer

# JSON array of records → xlsx, flattening nested keys with dots
curl -s api/reports | claw xlsx from-json /tmp/r.xlsx --data - --flatten

# HTML `<table>` elements → xlsx, one sheet per table named by caption/h2
claw xlsx from-html /tmp/scrape.xlsx --data report.html --sheet-from h2

# PDF tables → xlsx via pdfplumber (one sheet per page)
claw xlsx from-pdf /tmp/statement.xlsx 2024-q3.pdf --pages 2-end --sheet-per-page

# Markdown → docx with corporate styles + TOC
claw docx from-md /tmp/spec.docx --data spec.md --reference ~/templates/corp.docx --toc

# Markdown outline → slide deck (# → title, ## → content slide)
claw pptx from-outline /tmp/kickoff.pptx --data agenda.md --template brand.pptx

# New Google Doc from markdown, shared with the team
claw doc create --title "Spec" --from spec.md --share user:alice@x.com:writer --share anyone:reader
```

### Create PDF from source

> Uses: [pdf from-html](../scripts/claw/src/claw/pdf/from_html.py) · [pdf from-md](../scripts/claw/src/claw/pdf/from_md.py) · [convert convert](../scripts/claw/src/claw/convert/convert.py)

Skip LaTeX: generate PDFs straight from HTML or Markdown via the bundled engines. See [claw/pdf](../references/claw/pdf.md) and [claw/convert](../references/claw/convert.md).

```bash
# HTML → PDF (PyMuPDF Story; no LaTeX dependency)
claw pdf from-html /tmp/report.pdf --data report.html

# Markdown → PDF without LaTeX (same engine)
claw pdf from-md /tmp/doc.pdf --data README.md

# Markdown → PDF via pandoc + xelatex (when you want full TeX features)
claw convert book.md --out /tmp/book.pdf --toc --highlight tango

# Any Pandoc-supported format via one command
claw convert input.rst --out /tmp/out.html --standalone --css style.css
```

---

## READ / EXTRACT

### Read cells and text

> Uses: [xlsx read](../scripts/claw/src/claw/xlsx/read.py) · [xlsx stat](../scripts/claw/src/claw/xlsx/stat.py) · [docx read](../scripts/claw/src/claw/docx/read.py) · [doc read](../scripts/claw/src/claw/doc/read.py) · `xlsx sql` (**NOT IMPLEMENTED**)

Quickly pull values as JSON / CSV / text without writing Python. See [claw/xlsx §READ](../references/claw/xlsx.md#2-read--extract), [claw/docx §READ](../references/claw/docx.md#2-read--inspect).

```bash
# Dump a cell range as JSON
claw xlsx read q3.xlsx --sheet Summary --range A1:F200 --json

# Column-level stats (min/max/mean/distinct/null) in one call
claw xlsx stat sales.xlsx --sheet Details --columns Amount,Qty,Region --json

# Run SQL over sheets (DuckDB under the hood)
claw xlsx sql books.xlsx 'SELECT author, SUM(copies) FROM Inventory GROUP BY 1' --json

# Plain text of a docx; outline-only; or structured JSON
claw docx read report.docx --text
claw docx read report.docx --headings
claw docx read report.docx --json --tables

# Extract a Google Doc's body as Markdown
claw doc read <DOC_ID> --format md --out /tmp/doc.md
```

### Read / extract from PDF

> Uses: [pdf extract-text](../scripts/claw/src/claw/pdf/extract_text.py) · [pdf extract-tables](../scripts/claw/src/claw/pdf/extract_tables.py) · [pdf extract-images](../scripts/claw/src/claw/pdf/extract_images.py) · [pdf render](../scripts/claw/src/claw/pdf/render.py) · [pdf search](../scripts/claw/src/claw/pdf/search.py) · `pdf form-list` (**NOT IMPLEMENTED**)

Text, tables, images, form fields — one verb each. See [claw/pdf](../references/claw/pdf.md).

```bash
# Plain text with paragraph breaks (all modes: text|blocks|dict|html)
claw pdf extract-text report.pdf --mode text --out /tmp/report.txt

# Tables → CSV or JSON via pdfplumber
claw pdf extract-tables report.pdf --pages 2-5 --out /tmp/tables.json --json

# All embedded images into a directory
claw pdf extract-images report.pdf --out /tmp/imgs/ --prefix fig

# Render one page to PNG (for thumbnails, previews)
claw pdf render report.pdf --page 1 --dpi 150 --out /tmp/cover.png

# Read all AcroForm fields
claw pdf form-list invoice.pdf --json

# Search for a phrase; return page + bbox hits
claw pdf search report.pdf --query "net revenue" --json
```

### Read web and XML

> Uses: [web fetch](../scripts/claw/src/claw/web/fetch.py) · [html select](../scripts/claw/src/claw/html/select.py) · [html strip](../scripts/claw/src/claw/html/strip.py) · [xml xpath](../scripts/claw/src/claw/xml/xpath.py) · [xml to-json](../scripts/claw/src/claw/xml/to_json.py)

Fetch, parse, query without writing a scraper. See [claw/web](../references/claw/web.md), [claw/html](../references/claw/html.md), [claw/xml](../references/claw/xml.md).

```bash
# HTTP GET with retry/backoff, save body
claw web fetch https://example.com/report --out /tmp/page.html

# Grab just the title text
claw web fetch https://example.com --extract title --json

# CSS-select on a saved HTML file
claw html select page.html --css 'table.data tbody tr' --json

# Strip a selector (ads, nav) and emit clean HTML
claw html strip page.html --css 'nav,.ad,aside' --out clean.html

# XPath on an XML/HTML file
claw xml xpath feed.xml --query '//item/title/text()' --json

# Convert XML → JSON (jc-style normalized keys)
claw xml to-json feed.xml --out feed.json
```

### Read metadata

> Uses: [xlsx meta](../scripts/claw/src/claw/xlsx/meta.py) · [pdf info](../scripts/claw/src/claw/pdf/info.py) · [img exif](../scripts/claw/src/claw/img/exif.py) · [media info](../scripts/claw/src/claw/media/info.py) · `docx comments dump` / `docx diff` / `pdf toc` / `pdf words` (**NOT IMPLEMENTED**)

```bash
# xlsx core properties
claw xlsx meta get sales.xlsx --json

# docx comments / tracked changes
claw docx comments dump review.docx --author "Reviewer A" --json
claw docx diff manuscript.docx --since 2026-01-01 --json

# PDF metadata, TOC, chars/words/shapes counts
claw pdf info report.pdf --json
claw pdf toc report.pdf --json
claw pdf words report.pdf --json

# Image EXIF (jc-style keys, *_utc for timestamps)
claw img exif DSC_0001.NEF --json | jq '.exif.DateTimeOriginal_utc'

# Media streams (ffprobe normalized)
claw media info lecture.mp4 --json
```

---

## TRANSFORM / EDIT

### Transform workbook

> Uses: [xlsx freeze](../scripts/claw/src/claw/xlsx/freeze.py) · [xlsx filter](../scripts/claw/src/claw/xlsx/filter_.py) · [xlsx conditional](../scripts/claw/src/claw/xlsx/conditional.py) · [xlsx validate](../scripts/claw/src/claw/xlsx/validate.py) · [xlsx chart](../scripts/claw/src/claw/xlsx/chart.py) · [xlsx append](../scripts/claw/src/claw/xlsx/append.py) · [xlsx protect](../scripts/claw/src/claw/xlsx/protect.py) · `xlsx style` / `xlsx format` / `xlsx table` / `xlsx image add` (**NOT IMPLEMENTED**)

Apply styling, conditional formatting, filters, charts, validation to an existing xlsx in place (or with `--backup`). See [claw/xlsx §FORMAT](../references/claw/xlsx.md#4-format--style).

```bash
# Bold white-on-navy header row
claw xlsx style sales.xlsx --sheet Q1 --range A1:F1 --bold --color "#FFFFFF" --fill "#4472C4" --halign center --border thin

# Freeze header + first two columns
claw xlsx freeze sales.xlsx --sheet Q1 --rows 1 --cols 2

# Auto-filter over the table range
claw xlsx filter sales.xlsx --sheet Q1 --range A1:F1000

# Red fill on negative values (conditional formatting)
claw xlsx conditional sales.xlsx --sheet Q1 --range B2:B200 --cell-is "lessThan:0" --fill "#FFC7CE" --color "#9C0006"

# Currency number format on a column
claw xlsx format sales.xlsx --sheet Q1 --range D2:D500 --number-format '"$"#,##0.00'

# Dropdown data validation (list type)
claw xlsx validate orders.xlsx --sheet Orders --range E2:E500 --type list --values "Pending,Shipped,Delivered,Cancelled"

# Add a line chart referencing a data range
claw xlsx chart sales.xlsx --sheet Q1 --type line --data B1:D50 --categories A1:A50 --title "Trend" --at F2

# Register a named Excel Table
claw xlsx table sales.xlsx --sheet Q1 --range A1:F1000 --name SalesQ1 --style TableStyleMedium2

# Append rows from a CSV
claw xlsx append audit.xlsx --sheet Log --data today.csv --backup

# Embed a PNG anchored at B12
claw xlsx image add report.xlsx --sheet Summary --at B12 --image /tmp/chart.png --width 480

# Password-protect a sheet (allow format-cells)
claw xlsx protect sales.xlsx --scope sheet --sheet Q1 --password hunter2 --allow select-unlocked,format-cells
```

### Transform PDF

> Uses: [pdf merge](../scripts/claw/src/claw/pdf/merge.py) · [pdf split](../scripts/claw/src/claw/pdf/split.py) · [pdf rotate](../scripts/claw/src/claw/pdf/rotate.py) · [pdf watermark](../scripts/claw/src/claw/pdf/watermark.py) · [pdf redact](../scripts/claw/src/claw/pdf/redact.py) · [pdf encrypt](../scripts/claw/src/claw/pdf/encrypt.py) · [pdf flatten](../scripts/claw/src/claw/pdf/flatten.py) · [pdf ocr](../scripts/claw/src/claw/pdf/ocr.py) · `pdf stamp` / `pdf form-fill` / `pdf bookmark` (**NOT IMPLEMENTED**)

Merge, split, rotate, watermark, redact, annotate — without a line of Python. See [claw/pdf](../references/claw/pdf.md).

```bash
# Merge PDFs into one (order follows argv)
claw pdf merge part1.pdf part2.pdf part3.pdf --out /tmp/combined.pdf

# Split into per-page files
claw pdf split big.pdf --out-dir /tmp/pages/ --pattern 'page_{n:03}.pdf'

# Extract pages 3–7 and 10
claw pdf split big.pdf --pages 3-7,10 --out /tmp/slice.pdf

# Rotate every page 90° clockwise
claw pdf rotate scanned.pdf --angle 90 --out /tmp/rotated.pdf

# Add a diagonal "DRAFT" watermark
claw pdf watermark contract.pdf --text DRAFT --opacity 0.2 --rotate 45 --out /tmp/draft.pdf

# Stamp a logo in the top-right corner
claw pdf stamp invoice.pdf --image logo.png --position TR --out /tmp/stamped.pdf

# Redact matches of a regex (burn-in; irreversible)
claw pdf redact leak.pdf --regex '\b\d{3}-\d{2}-\d{4}\b' --out /tmp/redacted.pdf

# Password-encrypt (AES-256) with user + owner passwords
claw pdf encrypt report.pdf --user-pw readonly --owner-pw topsecret --out /tmp/enc.pdf

# Flatten form fields into static content
claw pdf flatten filled.pdf --out /tmp/flat.pdf

# Fill AcroForm fields from a JSON map
claw pdf form-fill blank.pdf --data fields.json --out /tmp/filled.pdf

# OCR a scanned PDF into a searchable one (Tesseract)
claw pdf ocr scan.pdf --lang eng --out /tmp/searchable.pdf

# Add a bookmark at page 12
claw pdf bookmark manual.pdf --title "Chapter 3" --page 12 --out /tmp/bookmarked.pdf
```

### Transform image

> Uses: [img resize](../scripts/claw/src/claw/img/resize.py) · [img fit](../scripts/claw/src/claw/img/fit.py) · [img pad](../scripts/claw/src/claw/img/pad.py) · [img thumb](../scripts/claw/src/claw/img/thumb.py) · [img crop](../scripts/claw/src/claw/img/crop.py) · [img sharpen](../scripts/claw/src/claw/img/sharpen.py) · [img enhance](../scripts/claw/src/claw/img/enhance.py) · [img exif](../scripts/claw/src/claw/img/exif.py) · [img watermark](../scripts/claw/src/claw/img/watermark.py) · [img overlay](../scripts/claw/src/claw/img/overlay.py) · [img composite](../scripts/claw/src/claw/img/composite.py) · [img batch](../scripts/claw/src/claw/img/batch.py)

Resize, crop, watermark, convert — single verbs. See [claw/img](../references/claw/img.md).

```bash
# Shrink to fit 1200×630 (Lanczos on downscale)
claw img resize hero.png --geometry 1200x630 --out hero-og.png

# Shrink-only (never upscale)
claw img resize photo.jpg --geometry '2048x>' --out photo-shrunk.jpg

# Crop-to-fill square avatar, bias slightly above center
claw img fit portrait.jpg --size 400x400 --center 0.5,0.3 --out avatar.jpg

# Letterbox 9:16 into 16:9 with dark grey bars
claw img pad 9x16.jpg --size 1920x1080 --color '#111111' --out 16x9-padded.jpg

# Fast feed thumbnail (respects EXIF rotation)
claw img thumb raw-12mp.jpg --max 512 --out thumb.jpg

# Explicit box crop
claw img crop screenshot.png --box 100,200,800,600 --out region.png

# Unsharp mask — the only sharpen worth shipping
claw img sharpen portrait.jpg --radius 1.5 --amount 120 --threshold 2 --out portrait-sharp.jpg

# Auto-tone: autocontrast + EXIF rotate bake-in
claw img enhance scan.jpg --autocontrast --cutoff 1 --out scan-clean.jpg
claw img exif auto-rotate phone-pic.jpg --out upright.jpg

# Text watermark bottom-right
claw img watermark report.jpg --text '© 2026' --position BR --opacity 0.4 --out wm.jpg

# Logo overlay at 12% of shortest edge, bottom-left
claw img overlay hero.jpg --logo brand.png --scale 0.12 --position BL --out hero-branded.jpg

# Composite two images with an offset
claw img composite --bg card.png --fg stamp.png --at 40,40 --out stamped.png

# Strip EXIF before upload
claw img exif strip upload.jpg --out upload-clean.jpg

# Batch: resize+strip+webp over a directory
claw img batch ./photos --op 'resize:2048x|strip|webp:85' --out ./web --recursive
```

### Transform docs and decks

> Uses: [docx add-heading](../scripts/claw/src/claw/docx/add_heading.py) · [docx add-paragraph](../scripts/claw/src/claw/docx/add_paragraph.py) · [docx add-table](../scripts/claw/src/claw/docx/add_table.py) · [docx add-image](../scripts/claw/src/claw/docx/add_image.py) · [docx toc](../scripts/claw/src/claw/docx/toc.py) · [pptx add-slide](../scripts/claw/src/claw/pptx/add_slide.py) · [pptx add-chart](../scripts/claw/src/claw/pptx/add_chart.py) · [pptx brand](../scripts/claw/src/claw/pptx/brand.py) · [pptx notes](../scripts/claw/src/claw/pptx/notes.py) · `docx insert pagebreak` / `docx hyperlink add` / `pptx fill` / `doc replace` (**NOT IMPLEMENTED**)

Insert content into existing docx / pptx at specific anchors. See [claw/docx §EDIT](../references/claw/docx.md#3-edit), [claw/pptx §EDIT](../references/claw/pptx.md#2-edit).

```bash
# Insert a heading after another heading's text
claw docx add-heading spec.docx --text "3. API" --level 2 --after "2. Architecture"

# Add a centered red note paragraph
claw docx add-paragraph notice.docx --text "Confidential — do not distribute." --bold --color "#C00" --align center

# Insert a table from CSV with a Word built-in style
claw docx add-table report.docx --data results.csv --header --style "Light Grid Accent 1"

# Drop an image after a "Figure 1" anchor
claw docx add-image report.docx --image /tmp/chart.png --width 5 --align center --after "Figure 1"

# Page break before "Chapter 2"
claw docx insert pagebreak spec.docx --before "Chapter 2"

# TOC placeholder (Word computes on open)
claw docx toc insert spec.docx --before "1. Introduction" --levels 1-2

# Wrap a run in a hyperlink
claw docx hyperlink add report.docx --text "methodology" --url https://wiki/methodology

# Append a slide with title + body
claw pptx add-slide deck.pptx --layout 1 --title "Roadmap" --body /tmp/roadmap.md

# Add a bar chart to an existing slide
claw pptx add-chart deck.pptx --slide 3 --type bar --data /tmp/revenue.csv --title "Revenue"

# Apply a brand palette deck-wide
claw pptx brand deck.pptx --palette corp.json --font Inter

# Fill a placeholder (e.g. subtitle) without rewriting the deck
claw pptx fill deck.pptx --slide 1 --placeholder 1 --text "Q3 2026"

# Set speaker notes from a file
claw pptx notes set deck.pptx --slide 3 --from /tmp/notes.md

# Replace a string across a Google Doc
claw doc replace <DOC_ID> --find "{{QUARTER}}" --with "Q3 2025"
```

---

## CONVERT format

### Convert via pandoc

> Uses: [convert convert](../scripts/claw/src/claw/convert/convert.py) · [convert book](../scripts/claw/src/claw/convert/book.py) · [convert slides](../scripts/claw/src/claw/convert/slides.py) · [convert md2pdf-nolatex](../scripts/claw/src/claw/convert/md2pdf_nolatex.py) · [convert list-formats](../scripts/claw/src/claw/convert/list_formats.py)

`claw convert` wraps pandoc end-to-end; the `book` / `slides` / `md2pdf-nolatex` presets skip the flag-soup for the three most common tasks. See [claw/convert](../references/claw/convert.md).

```bash
# Anything pandoc handles → anything (format sniffed from extensions)
claw convert manuscript.md --out manuscript.docx --reference-doc corp.docx
claw convert doc.docx --out doc.md
claw convert article.rst --out article.html --standalone --mathjax
claw convert chapters/*.md --out book.epub --toc --metadata-file book.yaml
claw convert slides.md --out slides.pptx --reference-doc brand.pptx

# Multi-file concatenation + TOC
claw convert ch1.md ch2.md ch3.md --out book.pdf --toc --toc-depth 3

# List supported formats
claw convert --list-input-formats
claw convert --list-output-formats

# Book preset (EPUB + PDF + HTML in one go)
claw convert book manuscript/*.md --out dist/ --title "My Book" --author "Me"

# Slide preset (reveal.js by default)
claw convert slides slides.md --out slides.html --theme night

# Markdown → PDF without LaTeX (PyMuPDF Story)
claw convert md2pdf-nolatex README.md --out README.pdf --css style.css
```

### Convert office

> Uses: [xlsx to-csv](../scripts/claw/src/claw/xlsx/to_csv.py) · [doc export](../scripts/claw/src/claw/doc/export.py) · `xlsx to-pdf` (**NOT IMPLEMENTED**)

Office ↔ other formats via the per-noun export verbs. See [claw/xlsx §2](../references/claw/xlsx.md#2-read--extract), [claw/doc §EXPORT](../references/claw/doc.md#4-export).

```bash
# Sheet → CSV (single sheet)
claw xlsx to-csv sales.xlsx --sheet Q1 --out /tmp/q1.csv --encoding utf-8-sig

# Workbook → PDF (LibreOffice headless, else PyMuPDF fallback)
claw xlsx to-pdf dashboard.xlsx --out /tmp/dash.pdf --sheet Summary --fit-to-width --orientation landscape

# Google Doc → PDF / DOCX / MD / HTML / TXT / EPUB
claw doc export <DOC_ID> --as pdf --out report.pdf
claw doc export <DOC_ID> --as docx --out report.docx --force
claw doc export <DOC_ID> --as md --out report.md
```

### Convert image / media

> Uses: [img convert](../scripts/claw/src/claw/img/convert_.py) · [img to-jpeg](../scripts/claw/src/claw/img/to_jpeg.py) · [img to-webp](../scripts/claw/src/claw/img/to_webp.py) · [media compress](../scripts/claw/src/claw/media/compress.py) · `media remux` (**NOT IMPLEMENTED**)

```bash
# Image format swap by extension
claw img convert logo.png logo.webp --quality 90
claw img convert screenshot.png screenshot.pdf

# Alpha-safe PNG → JPEG (flattens onto white; avoids black background)
claw img to-jpeg screenshot.png --bg white --out screenshot.jpg

# Animated GIF → animated WebP
claw img to-webp spin.gif --animated --out spin.webp

# Video container change (no re-encode)
claw media remux clip.mkv --out clip.mp4

# Encode to H.265 CRF 23
claw media compress big.mov --codec h265 --crf 23 --out small.mp4
```

---

## PROCESS video / audio

### Media ops

> Uses: [media extract-audio](../scripts/claw/src/claw/media/extract_audio.py) · [media thumbnail](../scripts/claw/src/claw/media/thumbnail.py) · [media gif](../scripts/claw/src/claw/media/gif.py) · [media trim](../scripts/claw/src/claw/media/trim.py) · [media compress](../scripts/claw/src/claw/media/compress.py) · [media concat](../scripts/claw/src/claw/media/concat.py) · [media burn-subs](../scripts/claw/src/claw/media/burn_subs.py) · [media loudnorm](../scripts/claw/src/claw/media/loudnorm.py) · [media speed](../scripts/claw/src/claw/media/speed.py) · [media fade](../scripts/claw/src/claw/media/fade.py) · [media crop-auto](../scripts/claw/src/claw/media/crop_auto.py)

All via `claw media` (ffmpeg under the hood). See [claw/media](../references/claw/media.md).

```bash
# Extract MP3 audio at VBR q:a=2
claw media extract-audio interview.mp4 --format mp3 --quality 2 --out interview.mp3

# Single poster frame at 30s
claw media thumbnail clip.mp4 --at 00:00:30 --width 1280 --out poster.jpg

# 4x4 contact sheet of evenly-spaced stills
claw media thumbnail lecture.mkv --count 16 --grid 4x4 --width 320 --out contact.jpg

# Palette-correct animated GIF (two-step palettegen / paletteuse)
claw media gif clip.mp4 --start 10 --duration 5 --width 480 --fps 15 --out out.gif

# Trim a range (keyframe-fast; --precise re-encodes)
claw media trim long.mp4 --from 00:01:30 --to 00:02:00 --out snip.mp4

# Compress to a target size (two-pass)
claw media compress lecture.mp4 --target-size 500MB --out lecture-small.mp4

# Concat multiple clips (demuxer, no re-encode if codecs match)
claw media concat intro.mp4 body.mp4 outro.mp4 --out full.mp4

# Burn SRT subtitles into the video
claw media burn-subs video.mp4 --subs captions.srt --out subtitled.mp4

# EBU R128 loudness normalize (two-pass)
claw media loudnorm podcast.wav --target -16 --out podcast-norm.wav

# 2× speed (audio tempo preserved)
claw media speed clip.mp4 --factor 2 --out fast.mp4

# 3s fade-in + 2s fade-out (video + audio together)
claw media fade clip.mp4 --in 3 --out-dur 2 --out faded.mp4

# Auto-detect + crop black bars
claw media crop-auto letterboxed.mp4 --out cropped.mp4
```

---

## SEND / PUBLISH

### Send email

> Uses: [email send](../scripts/claw/src/claw/email/send.py) · [email draft](../scripts/claw/src/claw/email/draft.py) · [email reply](../scripts/claw/src/claw/email/reply.py) · [email forward](../scripts/claw/src/claw/email/forward.py) · [email search](../scripts/claw/src/claw/email/search.py) · [email download-attachment](../scripts/claw/src/claw/email/download_attachment.py)

`claw email` handles MIME, threading headers, base64url — the common footguns in raw `gws gmail`. See [claw/email](../references/claw/email.md).

```bash
# Plain send
claw email send --to alice@x.com --subject "Q3 numbers" --body "Attached." --attach @/tmp/q3.xlsx

# HTML + inline image + plain-text fallback
claw email send --to team@x.com --subject "Release" --body-file notes.txt --html notes.html --inline logo=@/tmp/logo.png

# Multi-recipient, multi-attachment
claw email send --to a@x.com --to b@x.com --cc boss@x.com --subject S --body B \
  --attach @/tmp/report.xlsx --attach @/tmp/report.pdf

# Preview without sending (prints RFC 2822 + headers)
claw email send --to a@x.com --subject S --body hi --dry-run

# Save as draft instead of sending
claw email draft --to alice@x.com --subject "Follow up" --body "Let me know." --attach @/tmp/agenda.pdf

# Reply in-thread (auto In-Reply-To + References — Gmail doesn't break the thread)
claw email reply <MSG_ID> --body "Thanks, confirmed."

# Reply-all minus one addressee
claw email reply <MSG_ID> --all --remove bob@x.com --body-file response.txt --attach @/tmp/updated.pdf

# Forward without original attachments
claw email forward <MSG_ID> --to dave@x.com --body "FYI — original below." --no-attachments

# Search with Gmail operators; NDJSON out
claw email search --q "from:boss@x.com newer_than:7d has:attachment" --format json

# Download one attachment by message + attachment id
claw email download-attachment <MSG_ID> <ATT_ID> --out /tmp/invoice.pdf
```

### Send via Drive and Sheets

> Uses: [sheet upload](../scripts/claw/src/claw/sheet/upload.py) · [sheet download](../scripts/claw/src/claw/sheet/download.py) · [sheet share](../scripts/claw/src/claw/sheet/share.py) · [sheet list](../scripts/claw/src/claw/sheet/list_.py) · `doc share` (**NOT IMPLEMENTED**)

```bash
# Share an existing Doc publicly (reader)
claw doc share <DOC_ID> --anyone --role reader

# Share with a named user and notify by email
claw doc share <DOC_ID> --user alice@x.com --role writer --notify --message "Please review by Friday."

# Upload a CSV as a new Google Sheet (auto-convert)
claw sheet upload --name "DB Export" --from /tmp/rows.csv --convert

# Round-trip: export Sheet → xlsx → local edits → upload over the original
claw sheet download <SHEET_ID> --out /tmp/w.xlsx
# …edit /tmp/w.xlsx with claw xlsx style / append / chart …
claw sheet upload --replace <SHEET_ID> --from /tmp/w.xlsx

# List your Sheets in a folder
claw sheet list --parent <FOLDER_ID> --json
```

---

## AUTOMATE browser

### Browser ops

> Uses: [browser launch](../scripts/claw/src/claw/browser/launch.py)

Launches Chromium-family browsers with remote debugging so Chrome DevTools MCP can attach. See [claw/browser](../references/claw/browser.md) (includes a manual-launch escape hatch for custom flags).

```bash
# Launch Edge on the real profile (preserves cookies/logins)
claw browser launch --engine edge --profile default --port 9222

# Isolated throwaway profile (no kill needed)
claw browser launch --engine edge --profile /tmp/edge-session --port 9223

# Chrome with a specific URL at launch
claw browser launch --engine chrome --url https://example.com --port 9222
```

---

## PIPELINES

### Pipeline ops

> Uses: [pipeline run](../scripts/claw/src/claw/pipeline/run.py) · [pipeline validate](../scripts/claw/src/claw/pipeline/validate.py) · [pipeline list-steps](../scripts/claw/src/claw/pipeline/list_steps.py) · [pipeline graph](../scripts/claw/src/claw/pipeline/graph.py)

`claw pipeline` runs YAML recipes as a parallel DAG with resumable cache. See [claw-pipelines.md](claw-pipelines.md) for complete recipes, [claw/pipeline](../references/claw/pipeline.md) for DSL details.

```bash
# Run a recipe end-to-end
claw pipeline run recipe.yaml

# Validate schema + topology without executing
claw pipeline validate recipe.yaml

# List all steps and their dependencies
claw pipeline list-steps recipe.yaml

# Render the DAG as a Graphviz dot file
claw pipeline graph recipe.yaml --out /tmp/dag.dot

# Resume from the last successful step (after exit 3)
claw pipeline run recipe.yaml --resume

# Override a variable at the CLI
claw pipeline run recipe.yaml --set quarter=Q3 --set year=2026
```

---

## DIAGNOSE

> Uses: [doctor](../scripts/claw/src/claw/doctor.py) · [completion](../scripts/claw/src/claw/completion.py)

```bash
# Verify all external deps (gws auth, pandoc, ffmpeg, magick, ...)
claw doctor

# Version + bundled library versions
claw --version

# JSON schema of a verb's --json output (for pipeline consumers)
claw schema xlsx.read

# Standalone examples for any verb
claw xlsx new --examples
claw email send --examples

# See what *would* happen without writing anything
claw xlsx from-csv out.xlsx data.csv --dry-run

# Cache status / cleanup
claw cache stats
claw cache clear --older-than 7d
```

---

## Quick Reference (Cheat Sheet)

| Task | One-liner |
|------|-----------|
| CSV → xlsx | `claw xlsx from-csv out.xlsx data.csv --types infer` |
| xlsx → CSV | `claw xlsx to-csv f.xlsx --sheet S --out s.csv` |
| SQL over sheets | `claw xlsx sql f.xlsx 'SELECT * FROM "Sales"' --json` |
| Bold styled header | `claw xlsx style f.xlsx --sheet S --range A1:F1 --bold --fill "#4472C4" --color "#FFFFFF"` |
| Freeze header + filter | `claw xlsx freeze f.xlsx --sheet S --rows 1 && claw xlsx filter f.xlsx --sheet S --range A1:F1000` |
| Dropdown validation | `claw xlsx validate f.xlsx --sheet S --range E2:E500 --type list --values "Y,N"` |
| MD → docx w/ template | `claw docx from-md out.docx --data spec.md --reference corp.docx --toc` |
| MD → PDF (no LaTeX) | `claw pdf from-md out.pdf --data README.md` |
| MD → pptx | `claw pptx from-outline out.pptx --data agenda.md --template brand.pptx` |
| PDF merge | `claw pdf merge a.pdf b.pdf --out merged.pdf` |
| PDF split by pages | `claw pdf split big.pdf --pages 3-7,10 --out slice.pdf` |
| PDF watermark | `claw pdf watermark f.pdf --text DRAFT --opacity 0.2 --rotate 45 --out out.pdf` |
| PDF tables → JSON | `claw pdf extract-tables f.pdf --pages all --out tables.json --json` |
| Image resize | `claw img resize in.jpg --geometry 1200x630 --out out.jpg` |
| Alpha-safe PNG→JPEG | `claw img to-jpeg in.png --bg white --out out.jpg` |
| Send mail + attach | `claw email send --to a@x --subject S --body B --attach @f.pdf` |
| Reply in-thread | `claw email reply <MSG_ID> --body "thanks"` |
| Upload to Drive | `claw sheet upload --name "X" --from data.csv --convert` |
| Video trim | `claw media trim in.mp4 --from 00:01:00 --to 00:02:00 --out snip.mp4` |
| Run pipeline | `claw pipeline run recipe.yaml` |
| Doctor | `claw doctor` |
