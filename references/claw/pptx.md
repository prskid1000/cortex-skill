# `claw pptx` — PowerPoint Operations Reference

> Source directory: [scripts/claw/src/claw/pptx/](../../scripts/claw/src/claw/pptx/)

CLI wrapper over `python-pptx` for deck authoring. Best paired with a brand template `.pptx`.

Library API for escape hatches: see [When `claw pptx` Isn't Enough](#when-claw-pptx-isnt-enough).

## Contents

- **CREATE a deck**
  - [New blank deck](#11-new) · [Markdown outline → deck](#12-from-outline)
- **EDIT slides**
  - [Add slide](#21-add-slide) · [Chart](#22-add-chart) · [Table](#23-add-table) · [Image](#24-add-image) · [Shape](#25-add-shape) · [Reorder](#26-reorder) · [Fill placeholder](#27-fill)
- **FORMAT / STYLE**
  - [Apply brand](#31-brand) · [Crop image](#32-image-crop) · [Hyperlink](#33-link-add) · [Speaker notes](#34-notes-set)
- **UPDATE live content**
  - [Refresh chart data](#41-chart-refresh)
- **META**
  - [Core deck properties](#51-meta)
- **When `claw pptx` isn't enough** — [python-pptx escape hatches](#when-claw-pptx-isnt-enough)

---

## Critical Rules

1. **Safe-by-default writes** — every mutating verb writes to `<out>.tmp`, fsyncs, then atomic-renames. `--force` overwrites existing `--out`; `--backup` creates `<out>.bak`.
2. **Selectors** — slides addressed as `--slide N` (1-based) or `--slide-title "…"`; shapes by `--placeholder idx` (layout index) or `--shape-name "TitlePlaceholder"`; positions in `--at TL|TR|BL|BR|C` or `--at x,y` (EMU, inches, or `pct`); colors `#RRGGBB` / `#RRGGBBAA` / named.
3. **Structured output** — `--json` for machine output; progress via `--progress=json`; errors to stderr as `{error, code, hint}` under `--json`.
4. **Exit codes** — `0` success, `1` generic, `2` usage, `3` partial, `4` input, `5` system, `130` SIGINT.
5. **Help** — `claw pptx --help`, `claw pptx <verb> --help`, `claw help pptx <verb>` alias, `--examples` for recipes.
6. **Stream mode** — `--stream` is a no-op for `.pptx`. For decks &gt; 100 MB, use a slim template and append chunks in batches (`claw pptx add-slide` is O(1) per call).
7. **Layout indices** — `--layout N` is 0-based against the master's layouts list. `claw pptx meta get --layouts` enumerates them.
8. **Common output flags** — every mutating verb inherits `--force`, `--backup`, `--dry-run`, `--json`, `--quiet`, `--mkdir` via the shared `@common_output_options` decorator. Individual verb blocks only call them out when the verb overrides the default; run `claw pptx <verb> --help` for the authoritative per-verb flag list.

---

## 1. CREATE

### 1.1 `new`

> Source: [scripts/claw/src/claw/pptx/new.py](../../scripts/claw/src/claw/pptx/new.py)

Create a blank deck (default 16:9).

```
claw pptx new <out.pptx> [--16:9 | --4:3] [--template FILE.pptx] [--force] [--backup]
```

`--template` copies the file and clears all existing slides (layouts + master preserved).

Example:

```
claw pptx new /tmp/deck.pptx --template ~/templates/brand.pptx --16:9
```

### 1.2 `from-outline`

> Source: **NOT IMPLEMENTED** — no `pptx/from_outline.py` exists.

Build a deck from a Markdown outline. `#` → title slide, `##` → new content slide with bullets.

```
claw pptx from-outline <out.pptx> --data FILE.md|- [--template FILE.pptx]
                                                    [--layout-title N] [--layout-body N]
                                                    [--notes-from-blockquote] [--force]
```

Example:

```
claw pptx from-outline /tmp/kickoff.pptx --data agenda.md --template brand.pptx --notes-from-blockquote
```

---

## 2. EDIT

### 2.1 `add-slide`

> Source: [scripts/claw/src/claw/pptx/add_slide.py](../../scripts/claw/src/claw/pptx/add_slide.py)

Append a slide, optionally pre-populated.

```
claw pptx add-slide <file.pptx> --layout N [--title STR] [--body STR|FILE.md]
                                [--notes STR] [--at END|N] [--backup]
```

`--body` accepts a newline-separated bullet list or a small Markdown file.

Example:

```
claw pptx add-slide deck.pptx --layout 1 --title "Q3 Results" \
  --body $'- Revenue +12%\n- Churn -3%\n- NPS 68' --notes "Finance will cover Q4 targets."
```

### 2.2 `add-chart`

> Source: [scripts/claw/src/claw/pptx/add_chart.py](../../scripts/claw/src/claw/pptx/add_chart.py)

Insert a native PPT chart populated from CSV.

```
claw pptx add-chart <file.pptx> --slide N --type bar|col|line|pie|scatter|area \
  --data FILE.csv [--at x,y] [--size w,h] [--title STR] [--style N] [--backup]
```

Example:

```
claw pptx add-chart deck.pptx --slide 3 --type line --data trend.csv \
  --at 1in,2in --size 8in,4in --title "Revenue Trend"
```

### 2.3 `add-table`

> Source: [scripts/claw/src/claw/pptx/add_table.py](../../scripts/claw/src/claw/pptx/add_table.py)

Insert a table from CSV / JSON.

```
claw pptx add-table <file.pptx> --slide N --data FILE.csv [--at x,y] [--size w,h]
                                [--header] [--widths "1in,2in,1in"]
```

Example:

```
claw pptx add-table deck.pptx --slide 4 --data stats.csv --header --at 1in,2in --size 8in,3in
```

### 2.4 `add-image`

> Source: [scripts/claw/src/claw/pptx/add_image.py](../../scripts/claw/src/claw/pptx/add_image.py)

Insert a picture (inline) with optional aspect preservation.

```
claw pptx add-image <file.pptx> --slide N --image FILE [--at x,y] [--size w,h] [--keep-aspect]
```

Example:

```
claw pptx add-image deck.pptx --slide 2 --image /tmp/hero.png --at C --size 10in,5.5in
```

### 2.5 `add-shape`

> Source: **NOT IMPLEMENTED** — no `pptx/add_shape.py` exists.

Draw a shape and optionally fill with text.

```
claw pptx add-shape <file.pptx> --slide N --kind rect|rounded-rect|oval|triangle|arrow|callout|line \
  --at x,y --size w,h [--text STR] [--fill #HEX] [--line #HEX] [--text-color #HEX]
```

Example:

```
claw pptx add-shape deck.pptx --slide 5 --kind rounded-rect --at 1in,5in --size 2in,1in \
  --text "Decision" --fill "#4472C4" --text-color "#FFFFFF"
```

### 2.6 `reorder`

> Source: [scripts/claw/src/claw/pptx/reorder.py](../../scripts/claw/src/claw/pptx/reorder.py)

Reorder slides by 1-based index list.

```
claw pptx reorder <file.pptx> --order 3,1,2,4 [--backup]
```

Example:

```
claw pptx reorder deck.pptx --order 1,3,2,4,5
```

### 2.7 `fill`

> Source: **NOT IMPLEMENTED** — no `pptx/fill.py` exists.

Set the text of an existing placeholder on a slide.

```
claw pptx fill <file.pptx> --slide N --placeholder IDX TEXT
claw pptx fill <file.pptx> --slide N --shape-name NAME TEXT
```

Example:

```
claw pptx fill deck.pptx --slide 1 --placeholder 0 "Quarterly Review"
claw pptx fill deck.pptx --slide 1 --placeholder 1 "Finance — April 2026"
```

---

## 3. FORMAT / STYLE

### 3.1 `brand`

> Source: [scripts/claw/src/claw/pptx/brand.py](../../scripts/claw/src/claw/pptx/brand.py)

Bulk-apply brand elements (logo + accent colour) across all slides.

```
claw pptx brand <file.pptx> [--logo FILE --logo-at TR --logo-size 1in,0.5in]
                             [--accent #HEX] [--font NAME]
                             [--apply-to title|body|all]
```

Example:

```
claw pptx brand deck.pptx --logo /tmp/logo.png --logo-at TR --accent "#336699"
```

### 3.2 `image crop`

> Source: [scripts/claw/src/claw/pptx/image_crop.py](../../scripts/claw/src/claw/pptx/image_crop.py)

Crop an image on a given slide by fractional left/right/top/bottom (0..1).

```
claw pptx image crop <file.pptx> --slide N --shape-name NAME \
                     [--left 0.1] [--right 0.1] [--top 0.0] [--bottom 0.0]
```

Example:

```
claw pptx image crop deck.pptx --slide 2 --shape-name Picture1 --left 0.1 --right 0.1
```

### 3.3 `link add`

> Source: [scripts/claw/src/claw/pptx/link.py](../../scripts/claw/src/claw/pptx/link.py)

Attach a hyperlink to a text run or shape.

```
claw pptx link add <file.pptx> --slide N --shape-name NAME --url URL
claw pptx link add <file.pptx> --slide N --placeholder IDX --text "click" --url URL
```

Example:

```
claw pptx link add deck.pptx --slide 3 --shape-name CallToAction --url https://example.com
```

### 3.4 `notes set`

> Source: [scripts/claw/src/claw/pptx/notes.py](../../scripts/claw/src/claw/pptx/notes.py)

Set (or clear) speaker notes on a slide.

```
claw pptx notes set <file.pptx> --slide N --text STR|FILE.md [--append] [--clear]
```

Example:

```
claw pptx notes set deck.pptx --slide 3 --text "Mention the partnership terms."
```

---

## 4. UPDATE

### 4.1 `chart refresh`

> Source: **NOT IMPLEMENTED** — no `pptx/chart_refresh.py` exists.

Replace the data behind an existing native chart while preserving series formatting.

```
claw pptx chart refresh <file.pptx> --slide N --csv FILE [--shape-name NAME] [--backup]
```

Example:

```
claw pptx chart refresh deck.pptx --slide 3 --csv trend-q4.csv
```

---

## 5. META

### 5.1 `meta`

> Source: [scripts/claw/src/claw/pptx/meta.py](../../scripts/claw/src/claw/pptx/meta.py)

```
claw pptx meta get <file.pptx> [--json] [--layouts]
claw pptx meta set <file.pptx> [--title STR] [--author STR] [--subject STR]
                                [--keywords a,b,c] [--category STR] [--comments STR]
```

`--layouts` enumerates `{index, name, placeholder_types}` for each layout on the master — useful for picking `--layout N`.

Example:

```
claw pptx meta set deck.pptx --title "Q3 Review" --author "Finance"
claw pptx meta get brand.pptx --layouts --json
```

---

## When `claw pptx` Isn't Enough

Use `python-pptx` directly:

| Use case | Why `claw` can't do it |
|---|---|
| Custom KPI dashboards with per-shape positioning DSLs | Flag surface can't express compound layouts |
| Master / layout authoring (new layouts, per-layout placeholders) | Author in PowerPoint, save as template |
| Animations / transitions | Unsupported by `python-pptx` |
| Embedded video / audio beyond basic insertion | Limited OLE support |
| Gradient fills with multi-stop colour curves | Only simple solid / single-gradient via flags |

**python-pptx** — `pip install python-pptx` · [docs](https://python-pptx.readthedocs.io/)
- All measurements are English Metric Units (914 400 per inch); use `from pptx.util import Inches, Pt, Emu` — passing raw ints as lengths silently gives you sub-pixel sized shapes.
- Animations, transitions, and SmartArt are read-preserved but not writable; adding a slide from scratch strips any you touch with Python-level mutations.
- `prs.slide_layouts[i]` indexes by layout *order in the master*, which is template-specific — iterate `layout.name` to find the right one, don't hardcode indices.

## Footguns

- **Template first, authoring second.** `claw pptx` assumes a template provides the master + layouts. Authoring layouts from scratch yields ugly defaults.
- **Placeholder indexing** — `--placeholder IDX` is the *layout placeholder* index, not a visual order. Use `claw pptx meta get --layouts` to discover indices.
- **`add-chart` rewrites embedded XLSX** — the chart carries its own mini workbook; `chart refresh` replaces the worksheet bytes in place. Series order is preserved; series count changes will break formatting.
- **EMU math** — internal measurements are English Metric Units (914 400 per inch). `claw` accepts `in`, `cm`, `pt`, `px` (@96 DPI), and raw integers (interpreted as EMU).
- **Silent round-trip losses** — custom transitions, SmartArt, some gradient fills, and non-standard effects are dropped on save. Surface via `meta get --json` under `warnings`.
- **`from-outline` over-fills a single-body layout** — if your layout has one body placeholder but your slide section has multiple `##` headings of content, the extras are ignored. Split the outline.

---

## Quick Reference

| Task | One-liner |
|------|-----------|
| Blank deck from template | `claw pptx new out.pptx --template brand.pptx --16:9` |
| Outline → deck | `claw pptx from-outline out.pptx --data agenda.md --template brand.pptx` |
| Add slide | `claw pptx add-slide d.pptx --layout 1 --title "Q3" --body "- A\n- B"` |
| Insert chart | `claw pptx add-chart d.pptx --slide 3 --type line --data t.csv --at 1in,2in --size 8in,4in` |
| Insert image | `claw pptx add-image d.pptx --slide 2 --image hero.png --at C --size 10in,5.5in` |
| Reorder | `claw pptx reorder d.pptx --order 1,3,2,4` |
| Fill placeholder | `claw pptx fill d.pptx --slide 1 --placeholder 0 "Title"` |
| Apply brand | `claw pptx brand d.pptx --logo logo.png --logo-at TR --accent "#336699"` |
| Refresh chart data | `claw pptx chart refresh d.pptx --slide 3 --csv new.csv` |
| Set speaker notes | `claw pptx notes set d.pptx --slide 3 --text "Mention partners."` |
