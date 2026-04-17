# `claw xlsx` — Excel Operations Reference

> Source directory: [scripts/claw/src/claw/xlsx/](../../scripts/claw/src/claw/xlsx/)

CLI wrapper over `openpyxl` for spreadsheet work. Every verb is safe-by-default, emits structured output, and degrades gracefully on Windows-locked files.

Library API for escape hatches: see [When `claw xlsx` Isn't Enough](#when-claw-xlsx-isnt-enough).

## Contents

- **CREATE a workbook**
  - [New blank workbook](#11-new) · [From CSV](#12-from-csv) · [From JSON](#13-from-json) · [From HTML table](#14-from-html) · [From PDF tables](#15-from-pdf)
- **READ / EXTRACT data**
  - [Dump cells / ranges](#21-read) · [Export sheet to CSV](#22-to-csv) · [Export workbook to PDF](#23-to-pdf) · [SQL over sheets](#24-sql) · [Column statistics](#25-stat)
- **EDIT cells & objects**
  - [Append rows / sheets](#31-append) · [Rich text runs](#32-richtext-set) · [Embed images](#33-image-add)
- **FORMAT / STYLE**
  - [Apply styles](#41-style) · [Freeze panes](#42-freeze) · [Auto-filter](#43-filter) · [Conditional formatting](#44-conditional) · [Number format](#45-format) · [Excel tables](#46-table) · [Charts](#47-chart)
- **VALIDATE & structure**
  - [Dropdowns / constraints](#51-validate) · [Defined names](#52-name-add) · [Print setup](#53-print-setup)
- **PROTECT**
  - [Sheet / workbook passwords](#61-protect)
- **META**
  - [Get / set core properties](#71-meta) · [List pivots](#72-pivots-list)
- **When `claw xlsx` isn't enough** — [openpyxl escape hatches](#when-claw-xlsx-isnt-enough)

---

## Critical Rules

1. **Safe-by-default writes** — every mutating verb writes to `<out>.tmp`, fsyncs, then atomic-renames over the target. `--force` is required to overwrite an existing `--out` path that the caller didn't originate. `--backup` creates a `<out>.bak` sidecar before rename.
2. **Selectors** — `--sheet` accepts a sheet name or 1-based index; `--range` uses `A1:D10` (standard Excel notation); colors accept `#RRGGBB`, `#RRGGBBAA`, or CSS named colors.
3. **Structured output** — every verb supports `--json` for machine-readable results; long-running verbs stream NDJSON with `--progress=json`; errors go to stderr as `{error, code, hint}` under `--json`.
4. **Exit codes** — `0` success, `1` generic, `2` usage error, `3` partial (e.g. one sheet failed in a multi-sheet op), `4` bad input / missing file, `5` system error, `130` SIGINT.
5. **Help** — `claw xlsx --help`, `claw xlsx <verb> --help`, `claw help xlsx <verb>` alias, `--examples` prints runnable recipes.
6. **Stream mode** — pass `--stream` for files &gt;100 MB. It switches openpyxl into `write_only=True` (writes) or `read_only=True` (reads) so memory stays bounded. Not all verbs support `--stream`; see each section.
7. **Excel-locked file detection** — on Windows, `WinError 32` (sharing violation) surfaces as `{code: "EXCEL_LOCKED"}` with a hint to close Excel. `--retry N --retry-delay SEC` retries the atomic rename.
8. **Common output flags** — every mutating verb inherits `--force`, `--backup`, `--dry-run`, `--json`, `--quiet`, `--mkdir` via the shared `@common_output_options` decorator. Individual verb blocks only call them out when the verb overrides the default; run `claw xlsx <verb> --help` for the authoritative per-verb flag list.

---

## 1. CREATE

### 1.1 `new`

> Source: [scripts/claw/src/claw/xlsx/new.py](../../scripts/claw/src/claw/xlsx/new.py)

Create a blank `.xlsx`.

```
claw xlsx new <out.xlsx> [--sheet NAME]... [--force] [--backup]
```

Example:

```
claw xlsx new /tmp/report.xlsx --sheet Summary --sheet Details
```

### 1.2 `from-csv`

> Source: [scripts/claw/src/claw/xlsx/from_csv.py](../../scripts/claw/src/claw/xlsx/from_csv.py)

Build a workbook from one or more CSVs; one sheet per input.

```
claw xlsx from-csv <out.xlsx> <csv>... [--sheet NAME] [--delimiter ,] [--encoding utf-8]
                                       [--header-row 1] [--types infer|text]
                                       [--stream] [--force]
```

Example:

```
claw xlsx from-csv /tmp/sales.xlsx data/q1.csv data/q2.csv --types infer
```

### 1.3 `from-json`

> Source: [scripts/claw/src/claw/xlsx/from_json.py](../../scripts/claw/src/claw/xlsx/from_json.py)

Load a JSON array of rows (list of objects → columns keyed by first row's keys).

```
claw xlsx from-json <out.xlsx> --data FILE.json|- [--sheet Data] [--flatten] [--force]
```

Example:

```
curl -s api/reports | claw xlsx from-json /tmp/r.xlsx --data - --flatten
```

### 1.4 `from-html`

> Source: **NOT IMPLEMENTED** — no `xlsx/from_html.py` exists in the package.

Extract `<table>` elements from HTML (file or stdin); one sheet per table.

```
claw xlsx from-html <out.xlsx> --data FILE.html|URL|- [--select CSS]
                                                       [--sheet-from caption|h2|index]
```

Example:

```
claw xlsx from-html /tmp/scrape.xlsx --data report.html --sheet-from h2
```

### 1.5 `from-pdf`

> Source: **NOT IMPLEMENTED** — no `xlsx/from_pdf.py` exists in the package.

Convert PDF tables (via `pdfplumber`) to sheets.

```
claw xlsx from-pdf <out.xlsx> <in.pdf> [--pages all|1-5] [--strategy lines|text]
                                        [--sheet-per-page] [--snap-tol 3]
```

Example:

```
claw xlsx from-pdf /tmp/statement.xlsx 2024-q3.pdf --pages 2-end --sheet-per-page
```

---

## 2. READ / EXTRACT

### 2.1 `read`

> Source: [scripts/claw/src/claw/xlsx/read.py](../../scripts/claw/src/claw/xlsx/read.py)

Print cell values as JSON, CSV, or a TSV preview.

```
claw xlsx read <file.xlsx> [--sheet NAME] [--range A1:D10] [--values-only]
                           [--json|--csv|--tsv] [--formulas] [--stream]
```

Flags:

- `--formulas` — emit formula strings (`=SUM(B2:B10)`) instead of cached values.
- `--values-only` — omit cell coordinates; return just a 2D array.
- `--stream` — `read_only=True` underneath; required for multi-GB files.

Example:

```
claw xlsx read q3.xlsx --sheet Summary --range A1:F200 --json
```

### 2.2 `to-csv`

> Source: [scripts/claw/src/claw/xlsx/to_csv.py](../../scripts/claw/src/claw/xlsx/to_csv.py)

Export a single sheet to CSV.

```
claw xlsx to-csv <file.xlsx> --sheet NAME [--out FILE.csv|-] [--delimiter ,]
                             [--range A1:D10] [--encoding utf-8-sig] [--force]
```

Example:

```
claw xlsx to-csv sales.xlsx --sheet Q1 --out /tmp/q1.csv --encoding utf-8-sig
```

### 2.3 `to-pdf`

> Source: **NOT IMPLEMENTED** — no `xlsx/to_pdf.py` exists in the package.

Render sheets to PDF via print-area + page setup (uses LibreOffice headless if installed; falls back to PyMuPDF layout).

```
claw xlsx to-pdf <file.xlsx> --out FILE.pdf [--sheet NAME]... [--fit-to-width]
                             [--orientation portrait|landscape] [--force]
```

Example:

```
claw xlsx to-pdf dashboard.xlsx --out /tmp/dash.pdf --sheet Summary --fit-to-width
```

### 2.4 `sql`

> Source: **NOT IMPLEMENTED** — no `xlsx/sql.py` exists in the package.

Run SQL against sheets in place (csvkit / Miller-style, DuckDB engine).

```
claw xlsx sql <file.xlsx> "<SELECT …>" [--sheet-as-table] [--out FILE.xlsx|.csv] [--json]
```

Tables are named after sheets (`FROM "Sales Q1"`). Writing to `.xlsx` appends a result sheet.

Example:

```
claw xlsx sql books.xlsx 'SELECT author, SUM(copies) FROM Inventory GROUP BY 1' --json
```

### 2.5 `stat`

> Source: [scripts/claw/src/claw/xlsx/stat.py](../../scripts/claw/src/claw/xlsx/stat.py)

Per-column summary statistics — min / max / mean / stddev / distinct / null count.

```
claw xlsx stat <file.xlsx> --sheet NAME [--range A1:Z] [--columns A,C-F] [--json]
```

Example:

```
claw xlsx stat sales.xlsx --sheet Details --columns Amount,Qty,Region --json
```

---

## 3. EDIT

### 3.1 `append`

> Source: [scripts/claw/src/claw/xlsx/append.py](../../scripts/claw/src/claw/xlsx/append.py)

Append rows to a sheet (creates sheet if missing).

```
claw xlsx append <file.xlsx> --sheet NAME --data FILE.csv|FILE.json|- [--types infer]
                                                                       [--stream] [--backup]
```

Example:

```
claw xlsx append audit.xlsx --sheet Log --data today.csv --backup
```

### 3.2 `richtext set`

> Source: **NOT IMPLEMENTED** — no `xlsx/richtext.py` / `xlsx/richtext_set.py` exists.

Write a `CellRichText` run list to a cell. Each run is a `{text, bold?, italic?, color?, size?}` JSON object.

```
claw xlsx richtext set <file.xlsx> --sheet NAME --cell A1 --runs FILE.json|-
```

Example:

```
echo '[{"text":"OK"},{"text":" failed","color":"#C00","bold":true}]' \
  | claw xlsx richtext set report.xlsx --sheet Summary --cell B2 --runs -
```

### 3.3 `image add`

> Source: **NOT IMPLEMENTED** — no `xlsx/image.py` / `xlsx/image_add.py` exists.

Embed a PNG / JPEG anchored to a cell.

```
claw xlsx image add <file.xlsx> --sheet NAME --at A1 --image FILE
                                [--width PX] [--height PX] [--keep-aspect]
```

Example:

```
claw xlsx image add report.xlsx --sheet Summary --at B12 --image /tmp/chart.png --width 480
```

---

## 4. FORMAT / STYLE

### 4.1 `style`

> Source: **NOT IMPLEMENTED** — no `xlsx/style.py` exists.

Apply font / fill / border / alignment to a range.

```
claw xlsx style <file.xlsx> --sheet NAME --range A1:D1 \
  [--bold] [--italic] [--size N] [--font NAME] [--color #HEX] \
  [--fill #HEX] [--border thin|thick|double] [--border-color #HEX] \
  [--halign left|center|right] [--valign top|center|bottom] [--wrap]
```

Example:

```
claw xlsx style sales.xlsx --sheet Q1 --range A1:F1 \
  --bold --color "#FFFFFF" --fill "#4472C4" --halign center --border thin
```

### 4.2 `freeze`

> Source: [scripts/claw/src/claw/xlsx/freeze.py](../../scripts/claw/src/claw/xlsx/freeze.py)

Freeze the top N rows and/or left N columns.

```
claw xlsx freeze <file.xlsx> --sheet NAME [--rows N] [--cols N] [--at A2]
```

Example:

```
claw xlsx freeze sales.xlsx --sheet Q1 --rows 1 --cols 2
```

### 4.3 `filter`

> Source: [scripts/claw/src/claw/xlsx/filter_.py](../../scripts/claw/src/claw/xlsx/filter_.py)

Turn on auto-filter for a range.

```
claw xlsx filter <file.xlsx> --sheet NAME --range A1:F1000 [--off]
```

Example:

```
claw xlsx filter sales.xlsx --sheet Q1 --range A1:F1000
```

### 4.4 `conditional`

> Source: [scripts/claw/src/claw/xlsx/conditional.py](../../scripts/claw/src/claw/xlsx/conditional.py)

Add a conditional formatting rule. Exactly one of `--cell-is`, `--formula`, `--color-scale`, `--data-bar`, `--icon-set`.

```
claw xlsx conditional <file.xlsx> --sheet NAME --range A2:A500 \
  [--cell-is "greaterThan:100"] \
  [--formula "=ISBLANK(A2)"] \
  [--color-scale "min:#F8696B,max:#63BE7B"] \
  [--data-bar "#638EC6"] \
  [--icon-set "3TrafficLights1:percent:0,33,67"] \
  [--fill #HEX] [--color #HEX] [--bold] [--stop-if-true]
```

Example:

```
claw xlsx conditional sales.xlsx --sheet Q1 --range B2:B200 \
  --cell-is "lessThan:0" --fill "#FFC7CE" --color "#9C0006"
```

### 4.5 `format`

> Source: **NOT IMPLEMENTED** — no `xlsx/format.py` exists.

Set the Excel number format of a cell range.

```
claw xlsx format <file.xlsx> --sheet NAME --range B2:B500 --number-format "#,##0.00"
```

Common tokens: `0.00`, `#,##0`, `0%`, `$#,##0.00`, `yyyy-mm-dd`, `hh:mm:ss`, `@` (text).

Example:

```
claw xlsx format sales.xlsx --sheet Q1 --range D2:D500 --number-format '"$"#,##0.00'
```

### 4.6 `table`

> Source: **NOT IMPLEMENTED** — no `xlsx/table.py` exists.

Register an Excel Table (structured reference) over a range.

```
claw xlsx table <file.xlsx> --sheet NAME --range A1:F1000 --name SalesQ1 \
                            [--style TableStyleMedium9] [--totals]
```

Example:

```
claw xlsx table sales.xlsx --sheet Q1 --range A1:F1000 --name SalesQ1 --style TableStyleMedium2
```

### 4.7 `chart`

> Source: [scripts/claw/src/claw/xlsx/chart.py](../../scripts/claw/src/claw/xlsx/chart.py)

Add a chart to a sheet.

```
claw xlsx chart <file.xlsx> --sheet NAME --type bar|col|line|pie|scatter|area \
  --data A1:D100 [--categories A1:A100] [--title STR] \
  [--x-title STR] [--y-title STR] [--at F2] [--style N]
```

Example:

```
claw xlsx chart sales.xlsx --sheet Q1 --type line --data B1:D50 --categories A1:A50 \
  --title "Trend" --at F2 --style 12
```

---

## 5. VALIDATE & STRUCTURE

### 5.1 `validate`

> Source: [scripts/claw/src/claw/xlsx/validate.py](../../scripts/claw/src/claw/xlsx/validate.py)

Add a data-validation rule (dropdown, numeric range, custom formula).

```
claw xlsx validate <file.xlsx> --sheet NAME --range A2:A100 \
  --type list|whole|decimal|date|time|textLength|custom \
  [--values "Y,N,Maybe" | --source "=Lists!$A$1:$A$10"] \
  [--operator between|equal|greaterThan|lessThan|...] \
  [--formula1 V] [--formula2 V] \
  [--error-style stop|warning|information] [--prompt STR]
```

Example:

```
claw xlsx validate orders.xlsx --sheet Orders --range E2:E500 \
  --type list --values "Pending,Shipped,Delivered,Cancelled"
```

### 5.2 `name add`

> Source: **NOT IMPLEMENTED** — no `xlsx/name.py` / `xlsx/name_add.py` exists.

Create a defined name (workbook- or sheet-scoped).

```
claw xlsx name add <file.xlsx> --name TaxRate --refers-to "=Config!$B$1" [--scope SHEET|workbook]
```

Example:

```
claw xlsx name add cfg.xlsx --name DefaultRegion --refers-to '="APAC"'
```

### 5.3 `print-setup`

> Source: **NOT IMPLEMENTED** — no `xlsx/print_setup.py` exists.

Configure print titles, print area, and fit-to-page.

```
claw xlsx print-setup <file.xlsx> --sheet NAME [--print-area A1:F1000] \
  [--print-titles "rows:1:1" | "cols:A:A"] [--fit-width N] [--fit-height N] \
  [--orientation portrait|landscape] [--paper-size A4|Letter]
```

Example:

```
claw xlsx print-setup sales.xlsx --sheet Q1 --print-area A1:F1000 \
  --print-titles rows:1:1 --fit-width 1 --orientation landscape
```

---

## 6. PROTECT

### 6.1 `protect`

> Source: [scripts/claw/src/claw/xlsx/protect.py](../../scripts/claw/src/claw/xlsx/protect.py)

Protect a sheet or the workbook structure with a password and allow-list.

```
claw xlsx protect <file.xlsx> --scope sheet|workbook [--sheet NAME] \
  --password PASSWORD \
  [--allow select-locked,select-unlocked,format-cells,insert-rows,...]
```

Example:

```
claw xlsx protect sales.xlsx --scope sheet --sheet Q1 --password hunter2 \
  --allow select-unlocked,format-cells
```

Clear protection:

```
claw xlsx protect sales.xlsx --scope sheet --sheet Q1 --clear
```

---

## 7. META

### 7.1 `meta`

> Source: [scripts/claw/src/claw/xlsx/meta.py](../../scripts/claw/src/claw/xlsx/meta.py)

```
claw xlsx meta get <file.xlsx> [--json]
claw xlsx meta set <file.xlsx> [--title STR] [--author STR] [--subject STR] \
                                [--keywords a,b,c] [--description STR] [--company STR]
```

Example:

```
claw xlsx meta set sales.xlsx --author "Finance" --title "Q3 Sales Report"
```

### 7.2 `pivots list`

> Source: **NOT IMPLEMENTED** — no `xlsx/pivots.py` / `xlsx/pivots_list.py` exists.

List pivot tables present in the workbook (read-only — see escape hatches below).

```
claw xlsx pivots list <file.xlsx> [--json]
```

---

## When `claw xlsx` Isn't Enough

Drop into `openpyxl` directly for these scenarios:

| Use case | Why `claw` can't do it |
|---|---|
| Arbitrary chart construction (combo charts, dual axes, custom series shapes) | Covered flags can't express every chart topology |
| Overlapping conditional-formatting rule stacks with explicit `stopIfTrue` ordering | Ranges intersect; order matters |
| VBA-preserving round-trip (`keep_vba=True`) | No VBA authoring surface |
| Pivot-table creation (only read / preserve is supported) | `openpyxl` doesn't author pivots either — use a template `.xlsx` |
| Worksheet-scoped named styles with inheritance chains | Flag surface can't represent style hierarchies |

**openpyxl** — `pip install openpyxl` · [docs](https://openpyxl.readthedocs.io/)
- Writes don't commit until `wb.save(path)` — no context-manager auto-save; a script that dies between `cell.value = ...` and `save` loses everything.
- `data_only=True` returns `None` for formulas in workbooks Excel has never opened — the cached-value cell is blank until Excel writes one.
- Silently drops slicers, funnel/treemap charts, and ActiveX controls on round-trip. Audit via `claw xlsx meta get --json` `warnings` array.

## Footguns

- **Excel-locked file on Windows** — `WinError 32` surfaces as `{code: "EXCEL_LOCKED"}`. Close Excel or use `--retry`.
- **`data_only=True` caveat** — formula cached values are `None` in workbooks that were never opened by Excel. `claw xlsx read --formulas` gives the source formula instead.
- **Silent drop on round-trip** — slicers, some chart types (funnel, treemap), and ActiveX controls are silently dropped by `openpyxl` on save. `claw xlsx meta get --json` emits a `warnings` array when it detects unsupported features.
- **Number format locale** — `"#,##0.00"` uses the locale of the opener, not the writer. Use explicit format strings with literal separators only when a locale override is acceptable.
- **Merged cell writes** — writing to any cell except the top-left of a merged range raises. `claw xlsx style` detects merges and writes only the anchor.

---

## Quick Reference

| Task | One-liner |
|------|-----------|
| Blank workbook | `claw xlsx new out.xlsx --sheet Summary` |
| CSV → xlsx | `claw xlsx from-csv out.xlsx data.csv` |
| Dump range as JSON | `claw xlsx read f.xlsx --sheet S --range A1:D10 --json` |
| Export sheet → CSV | `claw xlsx to-csv f.xlsx --sheet S --out s.csv` |
| SQL over sheets | `claw xlsx sql f.xlsx 'SELECT * FROM "Sales"' --json` |
| Append rows | `claw xlsx append f.xlsx --sheet Log --data new.csv` |
| Bold header row | `claw xlsx style f.xlsx --sheet S --range A1:F1 --bold --fill "#4472C4" --color "#FFFFFF"` |
| Freeze header | `claw xlsx freeze f.xlsx --sheet S --rows 1` |
| Auto-filter | `claw xlsx filter f.xlsx --sheet S --range A1:F1000` |
| Dropdown | `claw xlsx validate f.xlsx --sheet S --range E2:E500 --type list --values "Y,N"` |
