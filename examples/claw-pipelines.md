# `claw pipeline` Recipes — YAML Cookbook

> Multi-step, declarative recipes for `claw pipeline run`. Each recipe is a complete YAML file — drop it into `recipe.yaml` and run.

**Reference:** [references/claw/pipeline.md](../references/claw/pipeline.md) — DSL syntax, interpolation, caching, retries. For single-line recipes see [claw-recipes.md](claw-recipes.md).

## Contents

- **REPORT — build + deliver** (DB/API → styled artefact → Drive/email)
  - [DB → styled XLSX + PDF → Drive → Gmail (marquee)](#db-to-styled-xlsx--pdf-to-drive-to-gmail)
  - [CSV → styled XLSX → Google Sheet (shared link)](#csv-to-styled-xlsx-to-google-sheet)
  - [Scheduled DB snapshot → Google Sheet (upload-replace)](#scheduled-db-snapshot-to-google-sheet)
- **EXTRACT + DELIVER** (ingest unstructured → structured → consumers)
  - [PDF tables → multi-sheet XLSX → PDF summary](#pdf-tables-to-multi-sheet-xlsx-to-pdf-summary)
  - [HTML page → XLSX → email](#html-page-to-xlsx-to-email)
  - [JSON API → flattened XLSX → Drive](#json-api-to-flattened-xlsx-to-drive)
- **ETL — round-trip & enrich**
  - [Google Sheet → download → enrich → upload-back](#google-sheet-download-enrich-upload-back)
  - [Excel → SQL transform → styled XLSX](#excel-to-sql-transform-to-styled-xlsx)
- **PUBLISH — multi-format output**
  - [Markdown → HTML + PDF + DOCX + EPUB](#markdown-to-html--pdf--docx--epub)
  - [Slide deck build: outline → pptx + PDF + images](#slide-deck-build-outline-to-pptx--pdf--images)
- **MEDIA — image and video pipelines**
  - [Photo batch: strip EXIF + resize + watermark + upload](#photo-batch-strip-exif--resize--watermark--upload)
  - [Video → trim + compress + thumbnail contact sheet](#video-trim--compress--thumbnail-contact-sheet)
- **ORCHESTRATION primitives**
  - [Parallel fan-out / fan-in](#parallel-fan-out--fan-in)
  - [Conditional step with `when:`](#conditional-step-with-when)
  - [Retry on transient HTTP failure](#retry-on-transient-http-failure)
  - [Resume after partial failure](#resume-after-partial-failure)

---

## DB to Styled XLSX + PDF to Drive to Gmail

> Step types: `shell` · [xlsx.from-json](../scripts/claw/src/claw/xlsx/from_json.py) · `xlsx.to-pdf` (**NOT IMPLEMENTED**) · [drive.upload](../scripts/claw/src/claw/drive/upload.py) · `doc.upload` (**NOT IMPLEMENTED**) · [email.send](../scripts/claw/src/claw/email/send.py)

The marquee recipe. Queries a database, builds a styled Excel workbook with a chart, renders a PDF summary, uploads both to Google Drive, and emails them as attachments. Replaces the ~200-line Python orchestration in the original [data-pipelines.md](../references/claw/pipeline.md) full-pipeline example with declarative YAML.

**Outputs:**
- `${outdir}/raw.json` — raw query result
- `${outdir}/regional_sales.xlsx` — styled workbook with chart
- `${outdir}/regional_sales.pdf` — PDF summary
- Drive: two files named "Regional Sales Report.*"
- One email with both attachments to `${recipient}` (cc `${cc}`)

```yaml
name: regional-sales-report
description: DB → styled XLSX + PDF → Drive upload → Gmail with both attachments

vars:
  outdir: /tmp
  recipient: manager@company.com
  cc: team@company.com
  quarter: Q3

defaults:
  retries: 2
  backoff: exponential
  on-error: stop

steps:
  - id: query
    run: shell
    args:
      cmd:
        - claw
        - mysql
        - query
        - --host
        - "${env:DB_HOST}"
        - --db
        - sales
        - --sql-file
        - queries/regional.sql
        - --format
        - json
        - --out
        - "${vars.outdir}/raw.json"

  - id: build-xlsx
    run: xlsx.from-json
    needs: [query]
    args:
      data: "${vars.outdir}/raw.json"
      out: "${vars.outdir}/regional_sales.xlsx"
      sheet: "Regional Sales"
      types: infer
      style: corporate
      freeze: A2
      autofilter: true
      chart:
        type: bar
        title: "Quarterly Revenue by Region"
        data-range: "B1:E5"
        categories: "A2:A5"

  - id: build-pdf
    run: xlsx.to-pdf
    needs: [build-xlsx]
    args:
      path: "${build-xlsx.out}"
      out: "${vars.outdir}/regional_sales.pdf"
      title: "Regional Sales Report"
      fit-to-width: true
      orientation: landscape

  - id: upload-xlsx
    run: sheet.upload
    needs: [build-xlsx]
    args:
      path: "${build-xlsx.out}"
      name: "Regional Sales Report.xlsx"
      convert: false

  - id: upload-pdf
    run: doc.upload
    needs: [build-pdf]
    args:
      path: "${build-pdf.out}"
      name: "Regional Sales Report.pdf"

  - id: mail
    run: email.send
    needs: [build-xlsx, build-pdf, upload-xlsx, upload-pdf]
    cache: false
    args:
      to: "${vars.recipient}"
      cc: "${vars.cc}"
      subject: "Regional Sales Report — ${vars.quarter}"
      body: |
        Hi Team,

        Attached is the regional sales report. Both the Excel workbook (with charts)
        and a PDF summary are included; the same files are also on Google Drive.

        Best regards
      attachments:
        - "${build-xlsx.out}"
        - "${build-pdf.out}"
      oauth: "${env:GMAIL_OAUTH_JSON}"
```

Run:

```bash
claw pipeline run recipe.yaml --var quarter=Q4
```

---

## CSV to Styled XLSX to Google Sheet

> Step types: [xlsx.from-csv](../scripts/claw/src/claw/xlsx/from_csv.py) · `xlsx.style` (**NOT IMPLEMENTED**) · [drive.upload](../scripts/claw/src/claw/drive/upload.py)

Turns a local CSV into a branded XLSX and uploads it as a native Google Sheet shared with a public read-only link. Replaces [data-pipelines.md § CSV → Styled Excel → Google Sheets](../references/claw/pipeline.md).

**Outputs:**
- `/tmp/sales.xlsx` — styled workbook
- Google Sheet "Sales Data Import" shared read-only publicly

```yaml
name: csv-to-sheet
description: CSV → styled XLSX → Google Sheet with public share

vars:
  src: /tmp/sales_data.csv

steps:
  - id: build
    run: xlsx.from-csv
    args:
      data: "${vars.src}"
      out: /tmp/sales.xlsx
      sheet: "Sales Data"
      types: infer
      style: corporate
      freeze: A2
      autofilter: true

  - id: header-style
    run: xlsx.style
    needs: [build]
    args:
      path: "${build.out}"
      sheet: "Sales Data"
      range: A1:Z1
      bold: true
      color: "#FFFFFF"
      fill: "#2C3E50"
      halign: center

  - id: upload
    run: sheet.upload
    needs: [header-style]
    args:
      path: "${build.out}"
      name: "Sales Data Import"
      convert: true
      share:
        type: anyone
        role: reader
```

---

## Scheduled DB Snapshot to Google Sheet

> Step types: `shell` · [drive.upload](../scripts/claw/src/claw/drive/upload.py)

Daily DB snapshot that overwrites a fixed Google Sheet in place (useful for dashboard data sources). Designed to be triggered by cron / scheduled task.

**Outputs:**
- `/tmp/snapshot.csv` — intermediate
- Existing Sheet `${sheet_id}` — contents replaced

```yaml
name: daily-db-snapshot
description: DB query → CSV → upload-replace existing Google Sheet

vars:
  sheet_id: "${env:DASHBOARD_SHEET_ID}"
  outdir: /tmp

steps:
  - id: query
    run: shell
    retries: 3
    backoff: exponential
    args:
      cmd:
        - claw
        - mysql
        - query
        - --db
        - analytics
        - --sql-file
        - queries/dashboard.sql
        - --format
        - csv
        - --out
        - "${vars.outdir}/snapshot.csv"

  - id: upload
    run: sheet.upload
    needs: [query]
    cache: false
    args:
      path: "${query.out}"
      replace: "${vars.sheet_id}"
      convert: true
```

---

## PDF Tables to Multi-Sheet XLSX to PDF Summary

> Step types: [pdf.extract-tables](../scripts/claw/src/claw/pdf/extract_tables.py) · [xlsx.from-json](../scripts/claw/src/claw/xlsx/from_json.py) · `xlsx.to-pdf` (**NOT IMPLEMENTED**)

Extracts every table in a multi-page PDF (one sheet per page), styles them, and produces a landscape PDF summary of the structured output. Replaces [data-pipelines.md § PDF → Extract Tables → Excel](../references/claw/pipeline.md) + [XLSX → PDF](../references/claw/pipeline.md).

**Outputs:**
- `/tmp/tables.json` — structured table data
- `/tmp/extracted_tables.xlsx` — one sheet per source page
- `/tmp/summary.pdf` — printable summary

```yaml
name: pdf-tables-roundtrip
description: PDF → extract tables → multi-sheet XLSX → landscape PDF

vars:
  src: /tmp/financial_report.pdf
  outdir: /tmp

steps:
  - id: extract
    run: pdf.extract-tables
    args:
      path: "${vars.src}"
      out: "${vars.outdir}/tables.json"
      by-page: true
      strategy: lines

  - id: build-xlsx
    run: xlsx.from-json
    needs: [extract]
    args:
      data: "${extract.out}"
      out: "${vars.outdir}/extracted_tables.xlsx"
      sheet-per: "${group}"
      style: corporate

  - id: summarize
    run: xlsx.to-pdf
    needs: [build-xlsx]
    args:
      path: "${build-xlsx.out}"
      out: "${vars.outdir}/summary.pdf"
      title: "Extracted Financials"
      orientation: landscape
      fit-to-width: true
```

---

## HTML Page to XLSX to Email

> Step types: [web.fetch](../scripts/claw/src/claw/web/fetch.py) · `xlsx.from-html` (**NOT IMPLEMENTED**) · `xlsx.style` (**NOT IMPLEMENTED**) · [email.send](../scripts/claw/src/claw/email/send.py)

Fetches a web page, pulls every `<table>` into a workbook, and mails the result to a distribution list. Useful for scraping published numbers from regulator / exchange / partner pages.

**Outputs:**
- `/tmp/page.html` — raw HTML (cached)
- `/tmp/scrape.xlsx` — one sheet per table
- Email to `${recipient}` with XLSX attached

```yaml
name: scrape-to-mail
description: HTML page → every `<table>` → XLSX → Gmail

vars:
  url: https://example.com/daily-prices
  recipient: desk@example.com
  outdir: /tmp

steps:
  - id: fetch
    run: web.fetch
    retries: 3
    backoff: exponential
    args:
      url: "${vars.url}"
      out: "${vars.outdir}/page.html"
      cache: true

  - id: build
    run: xlsx.from-html
    needs: [fetch]
    args:
      data: "${fetch.out}"
      out: "${vars.outdir}/scrape.xlsx"
      sheet-from: h2

  - id: style
    run: xlsx.style
    needs: [build]
    args:
      path: "${build.out}"
      sheet: 1
      range: A1:Z1
      bold: true
      fill: "#34495E"
      color: "#FFFFFF"

  - id: mail
    run: email.send
    needs: [style]
    cache: false
    args:
      to: "${vars.recipient}"
      subject: "Daily price scrape — $(date -I)"
      body: "Auto-generated workbook attached."
      attachments:
        - "${build.out}"
```

---

## JSON API to Flattened XLSX to Drive

> Step types: [web.fetch](../scripts/claw/src/claw/web/fetch.py) · [xlsx.from-json](../scripts/claw/src/claw/xlsx/from_json.py) · [drive.upload](../scripts/claw/src/claw/drive/upload.py)

Hits a JSON endpoint, flattens nested records into a wide-table XLSX, and uploads to a designated Drive folder. `web.fetch` caches the response so retries don't hammer the API.

**Outputs:**
- `/tmp/api.json` — raw response (cached)
- `/tmp/records.xlsx` — flattened workbook
- Drive file in folder `${parent}`

```yaml
name: api-to-drive
description: JSON API → flatten → XLSX → Drive upload

vars:
  endpoint: https://api.example.com/v2/reports
  parent: "${env:DRIVE_FOLDER_ID}"

steps:
  - id: fetch
    run: web.fetch
    retries: 5
    backoff: exponential
    timeout: 30s
    args:
      url: "${vars.endpoint}"
      headers:
        Authorization: "Bearer ${env:API_TOKEN}"
      out: /tmp/api.json
      cache: true

  - id: build
    run: xlsx.from-json
    needs: [fetch]
    args:
      data: "${fetch.out}"
      out: /tmp/records.xlsx
      flatten: true
      types: infer

  - id: upload
    run: sheet.upload
    needs: [build]
    args:
      path: "${build.out}"
      name: "API Records $(date -I).xlsx"
      parent: "${vars.parent}"
      convert: false
```

---

## Google Sheet Download, Enrich, Upload Back

> Step types: [drive.download](../scripts/claw/src/claw/drive/download.py) · `xlsx.sql` (**NOT IMPLEMENTED**) · [xlsx.conditional](../scripts/claw/src/claw/xlsx/conditional.py) · [drive.upload](../scripts/claw/src/claw/drive/upload.py)

Downloads an existing Google Sheet, adds a computed "Status" column based on a revenue threshold, and uploads the modified content back to the same file id. Replaces [data-pipelines.md § Google Sheet → download → modify → upload back](../references/claw/pipeline.md).

**Outputs:**
- `/tmp/downloaded.xlsx` — pristine download
- `/tmp/modified.xlsx` — with new column
- `${sheet_id}` — overwritten with modified content

```yaml
name: sheet-enrich-roundtrip
description: Download Google Sheet → add Status column → upload back

vars:
  sheet_id: "${env:SALES_SHEET_ID}"
  threshold: 100000

steps:
  - id: download
    run: sheet.download
    args:
      file-id: "${vars.sheet_id}"
      out: /tmp/downloaded.xlsx
      format: xlsx

  - id: enrich
    run: xlsx.sql
    needs: [download]
    args:
      path: "${download.out}"
      query: |
        SELECT *,
               CASE WHEN Revenue > ${vars.threshold} THEN 'High' ELSE 'Normal' END AS Status
        FROM "Sheet1"
      out: /tmp/modified.xlsx

  - id: style
    run: xlsx.conditional
    needs: [enrich]
    args:
      path: "${enrich.out}"
      sheet: 1
      range: "F2:F1000"
      cell-is: "equal:\"High\""
      fill: "#D5F5E3"
      color: "#186A3B"

  - id: upload
    run: sheet.upload
    needs: [style]
    cache: false
    args:
      path: "${enrich.out}"
      replace: "${vars.sheet_id}"
      convert: true
```

---

## Excel to SQL Transform to Styled XLSX

> Step types: `xlsx.sql` (**NOT IMPLEMENTED**) · `xlsx.style` (**NOT IMPLEMENTED**) · [xlsx.chart](../scripts/claw/src/claw/xlsx/chart.py)

Run a DuckDB SQL transform over existing sheets (grouping, joins, aggregates) and emit a fresh styled workbook without leaving the `claw` substrate.

**Outputs:**
- `/tmp/summary.xlsx` — grouped / aggregated output with header styling + chart

```yaml
name: xlsx-sql-transform
description: Aggregate sheets with SQL → styled output XLSX

vars:
  src: /tmp/transactions.xlsx
  out: /tmp/summary.xlsx

steps:
  - id: aggregate
    run: xlsx.sql
    args:
      path: "${vars.src}"
      query: |
        SELECT Region,
               SUM(Amount) AS Total,
               COUNT(*)   AS OrderCount,
               AVG(Amount) AS AvgOrder
        FROM "Transactions"
        GROUP BY Region
        ORDER BY Total DESC
      out: "${vars.out}"

  - id: header-style
    run: xlsx.style
    needs: [aggregate]
    args:
      path: "${aggregate.out}"
      sheet: 1
      range: A1:D1
      bold: true
      color: "#FFFFFF"
      fill: "#1A5276"
      halign: center

  - id: chart
    run: xlsx.chart
    needs: [header-style]
    args:
      path: "${aggregate.out}"
      sheet: 1
      type: bar
      data: B1:B20
      categories: A1:A20
      title: "Total by Region"
      at: F2
```

---

## Markdown to HTML + PDF + DOCX + EPUB

> Step types: `convert.any` uses [convert convert](../scripts/claw/src/claw/convert/convert.py) (note: the step-type alias `convert.any` in these recipes is aspirational; in the pipeline runner, use the verb name directly)

A single markdown source, four output formats in parallel — useful for documentation releases. Replaces the scattered per-format recipes in [document-conversion.md](../references/claw/pipeline.md).

**Outputs:**
- `dist/book.html`, `dist/book.pdf`, `dist/book.docx`, `dist/book.epub`

```yaml
name: mdbook-fanout
description: One markdown source → HTML + PDF + DOCX + EPUB (parallel)

vars:
  src: manuscript/*.md
  outdir: dist

steps:
  - id: html
    run: convert.any
    args:
      inputs: "${vars.src}"
      out: "${vars.outdir}/book.html"
      standalone: true
      toc: true
      css: styles/book.css

  - id: pdf
    run: convert.any
    args:
      inputs: "${vars.src}"
      out: "${vars.outdir}/book.pdf"
      toc: true
      highlight: tango
      engine: xelatex

  - id: docx
    run: convert.any
    args:
      inputs: "${vars.src}"
      out: "${vars.outdir}/book.docx"
      reference-doc: templates/corp.docx
      toc: true

  - id: epub
    run: convert.any
    args:
      inputs: "${vars.src}"
      out: "${vars.outdir}/book.epub"
      toc: true
      metadata-file: book.yaml
```

All four steps have no `needs:`, so they run in parallel up to `--jobs`.

---

## Slide Deck Build: Outline to PPTX + PDF + Images

> Step types: `pptx.from-outline` (**NOT IMPLEMENTED**) · [convert convert](../scripts/claw/src/claw/convert/convert.py) · [pdf.render](../scripts/claw/src/claw/pdf/render.py)

Builds a branded slide deck from a markdown outline, exports to PDF, and rasterizes each slide to PNG for embedding in docs / emails / thumbnails.

**Outputs:**
- `/tmp/deck.pptx` — branded deck
- `/tmp/deck.pdf` — PDF version
- `/tmp/slides/slide_*.png` — one PNG per slide

```yaml
name: deck-build
description: Markdown outline → branded pptx → PDF → slide PNGs

vars:
  outline: content/deck.md
  brand: templates/brand.pptx
  outdir: /tmp

steps:
  - id: build
    run: pptx.from-outline
    args:
      data: "${vars.outline}"
      out: "${vars.outdir}/deck.pptx"
      template: "${vars.brand}"
      notes-from-blockquote: true

  - id: pdf
    run: convert.any
    needs: [build]
    args:
      inputs: "${build.out}"
      out: "${vars.outdir}/deck.pdf"

  - id: thumbs
    run: pdf.render
    needs: [pdf]
    args:
      path: "${pdf.out}"
      pages: all
      dpi: 150
      out-dir: "${vars.outdir}/slides"
      pattern: "slide_{n:03}.png"
```

---

## Photo Batch: Strip EXIF + Resize + Watermark + Upload

> Step types: [img.batch](../scripts/claw/src/claw/img/batch.py) · `shell` · [drive.upload](../scripts/claw/src/claw/drive/upload.py)

A classic photographer pipeline: auto-rotate, strip identifying EXIF, resize to web-friendly dimensions, watermark, and upload the result to a shared Drive folder.

**Outputs:**
- `./web/*.jpg` — processed images
- Shared Drive folder populated

```yaml
name: photo-batch-publish
description: Auto-rotate + strip EXIF + resize + watermark + upload

vars:
  srcdir: ./raw
  webdir: ./web
  parent: "${env:PHOTOS_FOLDER_ID}"

steps:
  - id: rotate
    run: img.batch
    args:
      dir: "${vars.srcdir}"
      op: "rotate:auto|strip|resize:2048x|jpeg:85"
      out: "${vars.webdir}"
      recursive: true
      workers: 8

  - id: watermark
    run: img.batch
    needs: [rotate]
    args:
      dir: "${vars.webdir}"
      op: "watermark:© 2026:BR:0.35"
      backup: true

  - id: upload
    run: shell
    needs: [watermark]
    cache: false
    args:
      cmd:
        - bash
        - -c
        - |
          for f in ${vars.webdir}/*.jpg; do
            claw drive upload --name "$(basename "$f")" --from "$f" --parent "${vars.parent}"
          done
```

---

## Video Trim + Compress + Thumbnail Contact Sheet

> Step types: [media.trim](../scripts/claw/src/claw/media/trim.py) · [media.compress](../scripts/claw/src/claw/media/compress.py) · [media.thumbnail](../scripts/claw/src/claw/media/thumbnail.py)

Snap a range out of a long recording, compress it to a target size, and produce a 4×4 contact sheet for the trimmed clip. Useful for sharing a segment over Slack / email.

**Outputs:**
- `/tmp/clip.mp4` — trimmed raw clip
- `/tmp/clip-small.mp4` — compressed for sharing
- `/tmp/contact.jpg` — 4×4 thumbnail grid

```yaml
name: video-snip-share
description: Trim → compress → 4x4 thumbnail grid

vars:
  src: /tmp/long-lecture.mp4
  start: "00:12:30"
  end: "00:18:45"

steps:
  - id: trim
    run: media.trim
    args:
      path: "${vars.src}"
      from: "${vars.start}"
      to: "${vars.end}"
      out: /tmp/clip.mp4

  - id: compress
    run: media.compress
    needs: [trim]
    args:
      path: "${trim.out}"
      target-size: "100MB"
      codec: h265
      out: /tmp/clip-small.mp4

  - id: contact
    run: media.thumbnail
    needs: [trim]
    args:
      path: "${trim.out}"
      count: 16
      grid: "4x4"
      width: 320
      out: /tmp/contact.jpg
```

---

## Parallel Fan-Out / Fan-In

Illustrates how empty `needs:` lists schedule work in parallel, then a final step fans in. The "sheets" branch and the "pdf" branch are independent until the mail step pulls both together.

```yaml
name: fanout-fanin
description: Two independent branches converge at a single email send

vars:
  csv: /tmp/data.csv

steps:
  # ---- Wave 1 (parallel) ----
  - id: xlsx
    run: xlsx.from-csv
    args:
      data: "${vars.csv}"
      out: /tmp/out.xlsx
      types: infer

  - id: thumb
    run: img.resize
    args:
      input: /tmp/logo.png
      geometry: 200x200
      out: /tmp/logo-small.png

  # ---- Wave 2 (parallel, each depending on one wave-1 step) ----
  - id: pdf
    run: xlsx.to-pdf
    needs: [xlsx]
    args:
      path: "${xlsx.out}"
      out: /tmp/out.pdf

  - id: banner
    run: img.watermark
    needs: [thumb]
    args:
      input: "${thumb.out}"
      text: "BRAND"
      position: BR
      out: /tmp/banner.png

  # ---- Wave 3 (fan-in) ----
  - id: mail
    run: email.send
    needs: [pdf, banner]
    cache: false
    args:
      to: team@example.com
      subject: "Report"
      body-file: /tmp/msg.txt
      attachments: ["${pdf.out}"]
      inline: ["banner=@${banner.out}"]
```

Run with `claw pipeline graph recipe.yaml --format ascii` to see the DAG.

---

## Conditional Step with `when:`

Only send the email in `prod`; in `dev`, stop after the artefact is built. `--var env=prod` at the CLI flips the behavior.

```yaml
name: conditional-publish
vars:
  env: dev

steps:
  - id: build
    run: xlsx.from-csv
    args:
      data: /tmp/rows.csv
      out: /tmp/out.xlsx

  - id: mail
    run: email.send
    needs: [build]
    when: "${vars.env} == prod"
    cache: false
    args:
      to: team@example.com
      subject: "Nightly build"
      attachments: ["${build.out}"]
```

Run:

```bash
claw pipeline run recipe.yaml --var env=prod
```

---

## Retry on Transient HTTP Failure

Flaky endpoints get exponential backoff with a hard timeout. Only exit codes 4 (HTTP 4xx) and 5 (HTTP 5xx / timeout) retry — usage errors (exit 2) never do.

```yaml
name: retry-fetch
vars:
  endpoint: https://flaky.example.com/data.json

steps:
  - id: fetch
    run: web.fetch
    retries: 5
    backoff: exponential
    timeout: 30s
    retry-on: [4, 5, 130]
    args:
      url: "${vars.endpoint}"
      out: /tmp/data.json
      cache: true

  - id: process
    run: xlsx.from-json
    needs: [fetch]
    args:
      data: "${fetch.out}"
      out: /tmp/processed.xlsx
```

---

## Resume After Partial Failure

When `mail` fails (network glitch, OAuth expiry), `claw pipeline run recipe.yaml --resume` picks up from the cache-hit steps and only re-runs `mail` (which has `cache: false` so it always re-executes).

```yaml
name: resumable
defaults:
  retries: 1
  on-error: stop

steps:
  - id: build
    run: xlsx.from-csv
    args: { data: /tmp/rows.csv, out: /tmp/out.xlsx, types: infer }
    # cached by default

  - id: pdf
    run: xlsx.to-pdf
    needs: [build]
    args: { path: "${build.out}", out: /tmp/out.pdf }
    # cached by default

  - id: mail
    run: email.send
    needs: [build, pdf]
    cache: false
    args:
      to: manager@example.com
      subject: "Daily"
      attachments: ["${build.out}", "${pdf.out}"]
```

After a failure:

```bash
claw pipeline run recipe.yaml --resume
# build and pdf are cache hits; only `mail` re-executes
```

Inspect cache state at any time:

```bash
claw cache stats
claw pipeline graph recipe.yaml --format ascii
```
