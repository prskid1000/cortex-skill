# `claw docx` — Word Operations Reference

> Source directory: [scripts/claw/src/claw/docx/](../../scripts/claw/src/claw/docx/)

CLI wrapper over `python-docx` (plus pandoc for markdown ingestion). Authoring and light editing of `.docx` files.

Library API for escape hatches: see [When `claw docx` Isn't Enough](#when-claw-docx-isnt-enough).

## Contents

- **CREATE a document**
  - [New blank doc](#11-new) · [Markdown → docx](#12-from-md)
- **READ / INSPECT**
  - [Extract text / structure](#21-read) · [Dump comments](#22-comments-dump) · [Show tracked revisions](#23-diff)
- **EDIT body content**
  - [Headings](#31-add-heading) · [Paragraphs](#32-add-paragraph) · [Tables](#33-add-table) · [Images](#34-add-image) · [Insert page break](#35-insert-pagebreak) · [Hyperlinks](#36-hyperlink-add)
- **FORMAT / STYLE**
  - [Define / apply styles](#41-style) · [Sections (orientation, columns)](#42-section-add) · [Headers](#43-header-set) · [Footers](#44-footer-set) · [Table of contents](#45-toc-insert)
- **META**
  - [Core / custom properties](#51-meta) · [Attach custom XML](#52-custom-xml-attach)
- **TABLES**
  - [Autofit vs fixed width](#61-table-fit)
- **When `claw docx` isn't enough** — [python-docx escape hatches](#when-claw-docx-isnt-enough)

---

## Critical Rules

1. **Safe-by-default writes** — every mutating verb writes to `<out>.tmp`, fsyncs, then atomic-renames. `--force` overwrites existing `--out`; `--backup` creates `<out>.bak` first.
2. **Selectors** — anchors use `--at "<search text>"` to locate insertion points; `--before` / `--after` select which side of the anchor; `--style` matches style name or `Heading N` / `Normal`; colors accept `#RRGGBB` / `#RRGGBBAA` / named.
3. **Structured output** — `--json` for machine output; progress via `--progress=json` NDJSON; errors to stderr as `{error, code, hint}` under `--json`.
4. **Exit codes** — `0` success, `1` generic, `2` usage, `3` partial, `4` input, `5` system, `130` SIGINT.
5. **Help** — `claw docx --help`, `claw docx <verb> --help`, `claw help docx <verb>` alias, `--examples` for recipes.
6. **Stream mode** — `--stream` is a no-op for `.docx` (format loads fully into memory). Use pandoc (`claw docx from-md --engine pandoc-stream`) for docs &gt; 100 MB.
7. **Anchor safety** — `--at "..."` requires exactly one match; zero matches returns exit 4, multiple matches exit 2 unless `--match-nth N` is passed.
8. **Common output flags** — every mutating verb inherits `--force`, `--backup`, `--dry-run`, `--json`, `--quiet`, `--mkdir` via the shared `@common_output_options` decorator. Individual verb blocks only call them out when the verb overrides the default; run `claw docx <verb> --help` for the authoritative per-verb flag list.

---

## 1. CREATE

### 1.1 `new`

> Source: [scripts/claw/src/claw/docx/new.py](../../scripts/claw/src/claw/docx/new.py)

Create a blank `.docx`.

```
claw docx new <out.docx> [--template FILE.docx] [--force] [--backup]
```

`--template` copies an existing file and clears its body so custom styles survive.

Example:

```
claw docx new /tmp/report.docx --template ~/templates/corporate.docx
```

### 1.2 `from-md`

> Source: [scripts/claw/src/claw/docx/from_md.py](../../scripts/claw/src/claw/docx/from_md.py)

Convert Markdown (or any pandoc input format) into `.docx` using bundled pandoc.

```
claw docx from-md <out.docx> --data FILE.md|- [--reference FILE.docx]
                              [--toc] [--number-sections] [--force]
```

`--reference` provides a reference doc whose styles are inherited.

Example:

```
claw docx from-md /tmp/spec.docx --data spec.md --reference ~/templates/corporate.docx --toc
```

---

## 2. READ / INSPECT

### 2.1 `read`

> Source: [scripts/claw/src/claw/docx/read.py](../../scripts/claw/src/claw/docx/read.py)

Extract structured text / JSON from a document.

```
claw docx read <file.docx> [--text] [--json] [--tables] [--headings] [--style NAME]
```

- `--text` (default) — plain text with paragraph breaks.
- `--json` — structured `{paragraphs: [{text, style, level, runs}], tables: [...]}`.
- `--tables` — emit only tables as JSON arrays.
- `--headings` — print headings in outline form.
- `--style NAME` — keep only paragraphs using that style (e.g. `Heading 2`).

Example:

```
claw docx read report.docx --headings
```

### 2.2 `comments dump`

> Source: **NOT IMPLEMENTED** — no `docx/comments.py` exists.

Extract inline comments (`w:comment` + anchor text).

```
claw docx comments dump <file.docx> [--json] [--author NAME]
```

Example:

```
claw docx comments dump review.docx --author "Reviewer A" --json
```

### 2.3 `diff`

> Source: **NOT IMPLEMENTED** — no `docx/diff.py` exists.

Show tracked changes (`w:ins` / `w:del` revisions).

```
claw docx diff <file.docx> [--author NAME] [--since YYYY-MM-DD] [--json]
```

Example:

```
claw docx diff manuscript.docx --author "editor@..."
```

---

## 3. EDIT

### 3.1 `add-heading`

> Source: [scripts/claw/src/claw/docx/add_heading.py](../../scripts/claw/src/claw/docx/add_heading.py)

Append (or insert at anchor) a heading.

```
claw docx add-heading <file.docx> --text STR [--level 1..9] [--at "anchor"] [--before|--after]
                                  [--style NAME] [--backup]
```

Example:

```
claw docx add-heading spec.docx --text "3. API" --level 2 --after "2. Architecture"
```

### 3.2 `add-paragraph`

> Source: [scripts/claw/src/claw/docx/add_paragraph.py](../../scripts/claw/src/claw/docx/add_paragraph.py)

Add a paragraph with optional run-level formatting.

```
claw docx add-paragraph <file.docx> --text STR [--style NAME] [--bold] [--italic]
                                    [--size N] [--color #HEX] [--at "anchor"] [--before|--after]
                                    [--align left|center|right|justify]
```

Example:

```
claw docx add-paragraph notice.docx --text "Confidential — do not distribute." \
  --bold --color "#C00" --align center
```

### 3.3 `add-table`

> Source: [scripts/claw/src/claw/docx/add_table.py](../../scripts/claw/src/claw/docx/add_table.py)

Insert a table from CSV / JSON.

```
claw docx add-table <file.docx> --data FILE.csv|FILE.json|- [--style TableGrid]
                                [--header] [--at "anchor"] [--before|--after]
                                [--widths "1in,2in,1in"] [--backup]
```

Example:

```
claw docx add-table report.docx --data results.csv --header --style "Light Grid Accent 1"
```

### 3.4 `add-image`

> Source: [scripts/claw/src/claw/docx/add_image.py](../../scripts/claw/src/claw/docx/add_image.py)

Insert an inline or floating image.

```
claw docx add-image <file.docx> --image FILE [--width IN] [--height IN]
                                [--at "anchor"] [--before|--after] [--align left|center|right]
```

Example:

```
claw docx add-image report.docx --image /tmp/chart.png --width 5 --align center --after "Figure 1"
```

### 3.5 `insert pagebreak`

> Source: **NOT IMPLEMENTED** — no `docx/insert.py` / `docx/insert_pagebreak.py` exists.

Insert a page break before (default) or after a paragraph anchor.

```
claw docx insert pagebreak <file.docx> --before "anchor" [--backup]
claw docx insert pagebreak <file.docx> --after  "anchor" [--backup]
```

Example:

```
claw docx insert pagebreak spec.docx --before "Chapter 2"
```

### 3.6 `hyperlink add`

> Source: **NOT IMPLEMENTED** — no `docx/hyperlink.py` exists.

Wrap an existing text run in a hyperlink (adds run-level XML — see footgun).

```
claw docx hyperlink add <file.docx> --text "click here" --url https://example.com
                                    [--at "anchor"] [--match-nth N]
```

Example:

```
claw docx hyperlink add report.docx --text "methodology" --url https://wiki/methodology
```

---

## 4. FORMAT / STYLE

### 4.1 `style`

> Source: **NOT IMPLEMENTED** — no `docx/style.py` exists.

Define a new paragraph or character style, or apply one to matched paragraphs.

```
claw docx style define <file.docx> --name NAME --base "Normal" [--font NAME] [--size N]
                                    [--bold] [--italic] [--color #HEX] [--space-before PT] [--space-after PT]

claw docx style apply  <file.docx> --name NAME --to "anchor" [--match-nth N]
claw docx style apply  <file.docx> --name NAME --all-matching-style "Body Text"
```

Examples:

```
claw docx style define report.docx --name Caption --base Normal --italic --size 9 --color "#555"
claw docx style apply  report.docx --name Caption --all-matching-style "Body Text"
```

### 4.2 `section add`

> Source: **NOT IMPLEMENTED** — no `docx/section.py` exists.

Append a new section with its own page layout.

```
claw docx section add <file.docx> [--orientation portrait|landscape] [--columns N]
                                  [--margin-top IN] [--margin-bottom IN] [--margin-left IN] [--margin-right IN]
                                  [--page-size Letter|A4|Legal] [--start-type continuous|new-page|odd-page|even-page]
```

Example:

```
claw docx section add report.docx --orientation landscape --columns 2 --margin-left 0.75
```

### 4.3 `header set`

> Source: [scripts/claw/src/claw/docx/header.py](../../scripts/claw/src/claw/docx/header.py)

Set the header text for a section (defaults to all sections).

```
claw docx header set <file.docx> --text STR [--section N] [--align left|center|right]
                                 [--type primary|first-page|even-page]
```

Example:

```
claw docx header set report.docx --text "Quarterly Report — Confidential" --align center
```

### 4.4 `footer set`

> Source: [scripts/claw/src/claw/docx/footer.py](../../scripts/claw/src/claw/docx/footer.py)

Same shape as `header set`, plus a page-number token.

```
claw docx footer set <file.docx> --text STR [--page-number] [--section N] [--align left|center|right]
```

`--page-number` inserts a `PAGE` field (renders as `1`, `2`, …).

Example:

```
claw docx footer set report.docx --text "Page " --page-number --align right
```

### 4.5 `toc insert`

> Source: [scripts/claw/src/claw/docx/toc.py](../../scripts/claw/src/claw/docx/toc.py)

Insert a Table of Contents field at an anchor. Word recomputes on open.

```
claw docx toc insert <file.docx> [--at "anchor"] [--before|--after] [--levels 1-3] [--title "Contents"]
```

Example:

```
claw docx toc insert spec.docx --before "1. Introduction" --levels 1-2
```

---

## 5. META

### 5.1 `meta`

> Source: [scripts/claw/src/claw/docx/meta.py](../../scripts/claw/src/claw/docx/meta.py)

Core document properties.

```
claw docx meta get <file.docx> [--json]
claw docx meta set <file.docx> [--title STR] [--author STR] [--subject STR]
                                [--keywords a,b,c] [--category STR] [--comments STR]
```

Example:

```
claw docx meta set report.docx --title "Q3 Review" --author "Finance" --keywords q3,review,finance
```

### 5.2 `custom-xml attach`

> Source: **NOT IMPLEMENTED** — no `docx/custom_xml.py` exists.

Embed a custom XML part (used by SharePoint / document bindings).

```
claw docx custom-xml attach <file.docx> --part FILE.xml [--id ID] [--backup]
```

Example:

```
claw docx custom-xml attach report.docx --part metadata.xml --id reportMetadata
```

---

## 6. TABLES

### 6.1 `table fit`

> Source: **NOT IMPLEMENTED** — no `docx/table_fit.py` exists.

Switch table width mode between autofit and fixed column widths.

```
claw docx table fit <file.docx> --at "Table N" --mode autofit|fixed [--widths "1in,2in,1in"]
```

Example:

```
claw docx table fit report.docx --at "Table 1" --mode fixed --widths "1in,3in,1in"
```

---

## When `claw docx` Isn't Enough

Use `python-docx` (+ `docx.oxml` for raw XML) directly.

| Use case | Why `claw` can't do it |
|---|---|
| SmartArt | Not supported by `python-docx` at all — use a template that already contains it |
| Embedded Excel / chart OLE objects | Same; author via a template `.docx` |
| Real Word charts (bar / line / etc.) | Only available via the docx → docx template path |
| Arbitrary `w:*` XML (drawing ML, DrawingML fallback) | Escape-hatch for rare layout requirements |

**python-docx** — `pip install python-docx` · [docs](https://python-docx.readthedocs.io/)
- Import is `from docx import Document` — the package name (`python-docx`) and the import name (`docx`) differ, and there's a separate unrelated `docx` on PyPI you must not install.
- No read/write access to tracked-changes (revision marks) or comment-resolution state — walk `document.part.element` XML via `lxml` directly.
- Assigning `run.text = "..."` only touches the first run's text in a multi-run paragraph; set `.text` on the paragraph (destroys formatting) or edit runs individually.

## Footguns

- **Round-trip drops SmartArt / charts.** `python-docx` replaces them with placeholder images or empty drawings. Use a reference / template doc and only touch content, not those shapes.
- **Setting `run.text = "..."` across runs.** Word splits runs at formatting boundaries. Assigning to `.text` destroys formatting for the trailing part. `claw docx add-paragraph` always creates a fresh paragraph; there is no in-place edit verb that spans runs.
- **`<br type="page"/>` inside a run** — older Word builds sometimes render it as a soft break rather than a page break. `claw docx insert pagebreak` always emits a block-level `<w:pageBreakBefore/>` on a dedicated paragraph.
- **Anchor collisions** — `--at "Introduction"` may match multiple paragraphs. Pass `--match-nth 1` (1-based) to disambiguate; otherwise the verb exits `2` with a list of candidate paragraphs in the error JSON.
- **TOC not auto-populated** — `claw docx toc insert` emits the field; Word computes contents on next open. Headless renders (pandoc `docx → pdf`) preserve it; LibreOffice populates on load only.

---

## Quick Reference

| Task | One-liner |
|------|-----------|
| Blank doc from template | `claw docx new out.docx --template corp.docx` |
| Markdown → docx | `claw docx from-md out.docx --data spec.md --reference corp.docx --toc` |
| Extract text | `claw docx read f.docx --text` |
| Dump headings | `claw docx read f.docx --headings` |
| Add heading | `claw docx add-heading f.docx --text "Results" --level 2` |
| Insert paragraph | `claw docx add-paragraph f.docx --text "Hello" --bold --align center` |
| Add table from CSV | `claw docx add-table f.docx --data t.csv --header --style "Light Grid Accent 1"` |
| Insert image | `claw docx add-image f.docx --image chart.png --width 5` |
| Page break before anchor | `claw docx insert pagebreak f.docx --before "Chapter 2"` |
| Set core properties | `claw docx meta set f.docx --title "Q3" --author Finance` |
