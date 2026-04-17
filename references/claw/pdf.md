# `claw pdf` — PDF Operations Reference

> Source directory: [scripts/claw/src/claw/pdf/](../../scripts/claw/src/claw/pdf/)

CLI wrapper spanning PyMuPDF (fitz), pypdf, pdfplumber, and reportlab. The PDF surface is large, so this is the biggest `claw` command.

Library API for escape hatches: see [When `claw pdf` Isn't Enough](#when-claw-pdf-isnt-enough).

## Contents

- **READ / EXTRACT**
  - [Extract text](#11-extract-text) · [Extract tables](#12-extract-tables) · [Extract embedded images](#13-extract-images) · [Search pages](#14-search) · [Document info](#15-info) · [Characters with positions](#16-chars) · [Words with font filters](#17-words) · [Vector shapes](#18-shapes)
- **RENDER**
  - [Render page → image](#21-render) · [Debug table detection](#22-tables-debug)
- **TRANSFORM structure**
  - [Merge PDFs](#31-merge) · [Split](#32-split) · [Rotate pages](#33-rotate) · [Crop page](#34-crop)
- **STAMP / WATERMARK**
  - [Text watermark](#41-watermark) · [Image stamp](#42-stamp)
- **SECURE**
  - [Redact](#51-redact) · [Encrypt](#52-encrypt) · [Decrypt](#53-decrypt) · [Flatten forms](#54-flatten)
- **ANNOTATE**
  - [Highlight / note / ink](#61-annotate)
- **FORMS**
  - [List fields](#71-form-list) · [Fill from JSON](#72-form-fill)
- **META / STRUCTURE**
  - [Core metadata](#81-meta) · [Table of contents](#82-toc) · [Bookmarks](#83-bookmark-add) · [Optional content layers](#84-layer-toggle) · [Page labels](#85-labels-set) · [File attachments](#86-attach) · [Edit journal](#87-journal)
- **OCR**
  - [Scanned → searchable PDF](#91-ocr)
- **CREATE**
  - [HTML → PDF](#101-from-html) · [Markdown → PDF](#102-from-md) · [Convert EPUB/XPS/CBZ → PDF](#103-convert) · [QR code PDF](#104-qr) · [Barcode PDF](#105-barcode)
- **When `claw pdf` isn't enough** — [library escape hatches](#when-claw-pdf-isnt-enough)

---

## Critical Rules

1. **Safe-by-default writes** — every mutating verb writes to `<out>.tmp`, fsyncs, then atomic-renames. `--force` overwrites existing `--out`; `--backup` creates `<out>.bak` first. In-place edits are rejected unless `--in-place` is passed, in which case claw still stages the write and renames.
2. **Selectors**
   - Pages: `--pages N | a-b | all | odd | even | z-1 | 1-5,7,9-end`. `end` is total page count; negative indices count from end (`z-1` = last page, `z-2` = second-last).
   - Rectangles: `--box x0,y0,x1,y1` in PDF points (72pt = 1in), origin top-left on page.
   - Colours: `#RRGGBB` / `#RRGGBBAA` / CSS named.
3. **Structured output** — `--json` for machine output; long verbs stream NDJSON with `--progress=json`; errors to stderr as `{error, code, hint}` under `--json`.
4. **Exit codes** — `0` success, `1` generic, `2` usage, `3` partial (e.g. 3 pages of 40 failed), `4` input / remote, `5` server / system, `130` SIGINT.
5. **Help** — `claw pdf --help`, `claw pdf <verb> --help`, `claw help pdf <verb>` alias, `--examples` for recipes.
6. **Stream mode** — `--stream` opens with PyMuPDF's page iterator (no full tree held in memory); required for PDFs &gt; 100 MB. Not all verbs support it (`merge`, `form fill` must load fully).
7. **Licence surface — PyMuPDF is AGPL-3.0.** Using `claw pdf` in a closed-source service triggers AGPL obligations (network copyleft). `claw` prints a one-line AGPL notice on first use per shell session unless `CLAW_SUPPRESS_AGPL=1`. For AGPL-incompatible deployments use only the `pypdf` / `reportlab` code paths (flagged as `--engine pypdf|reportlab` where available).
8. **Common output flags** — every mutating verb inherits `--force`, `--backup`, `--dry-run`, `--json`, `--quiet`, `--mkdir` via the shared `@common_output_options` decorator. Individual verb blocks only call them out when the verb overrides the default; run `claw pdf <verb> --help` for the authoritative per-verb flag list.

---

## 1. READ / EXTRACT

### 1.1 `extract-text`

> Source: [scripts/claw/src/claw/pdf/extract_text.py](../../scripts/claw/src/claw/pdf/extract_text.py)

Extract text in one of PyMuPDF's output modes.

```
claw pdf extract-text <in.pdf> [--pages all|1-5] [--mode plain|blocks|dict|html|xhtml|xml|json]
                               [--out FILE|-] [--dehyphenate] [--preserve-ligatures]
                               [--stream] [--json]
```

- `plain` (default) — newline-separated paragraphs.
- `blocks` — list of `[x0, y0, x1, y1, text, block_no, block_type]`.
- `dict` — blocks → lines → spans with `font`, `size`, `color`, `flags`.
- `html` / `xhtml` — styled HTML.
- `xml` — char-level XML.

Example:

```
claw pdf extract-text report.pdf --pages 1-5 --mode blocks --json
```

### 1.2 `extract-tables`

> Source: [scripts/claw/src/claw/pdf/extract_tables.py](../../scripts/claw/src/claw/pdf/extract_tables.py)

Table extraction via pdfplumber.

```
claw pdf extract-tables <in.pdf> [--pages all|1-5]
                                  [--strategy lines|lines_strict|text|explicit]
                                  [--vlines N,N,N] [--hlines N,N,N]
                                  [--snap-tol 3] [--join-tol 3] [--edge-min-length 3]
                                  [--intersection-tol 3] [--text-tolerance 3]
                                  [--out FILE.json|FILE.csv|FILE.xlsx] [--json]
```

`--vlines` and `--hlines` are explicit split coordinates (used when `--strategy explicit`). `--snap-tol` is the snap-to-grid tolerance in points.

Example:

```
claw pdf extract-tables statement.pdf --pages 2-end --strategy lines --snap-tol 5 \
  --out /tmp/tables.xlsx
```

### 1.3 `extract-images`

> Source: [scripts/claw/src/claw/pdf/extract_images.py](../../scripts/claw/src/claw/pdf/extract_images.py)

Dump embedded images to a directory.

```
claw pdf extract-images <in.pdf> --out DIR [--pages all|1-5]
                                  [--format png|jpeg|original] [--min-width N] [--min-height N]
```

Example:

```
claw pdf extract-images brochure.pdf --out /tmp/imgs/ --min-width 300
```

### 1.4 `search`

> Source: [scripts/claw/src/claw/pdf/search.py](../../scripts/claw/src/claw/pdf/search.py)

Search pages; returns page + bounding boxes.

```
claw pdf search <in.pdf> --term STR [--regex] [--case-sensitive] [--pages all|1-5]
                         [--context 40] [--json]
```

Example:

```
claw pdf search contract.pdf --term "SSN" --regex --context 60 --json
```

### 1.5 `info`

> Source: [scripts/claw/src/claw/pdf/info.py](../../scripts/claw/src/claw/pdf/info.py)

Print document metadata + structural summary.

```
claw pdf info <in.pdf> [--json]
```

Includes: page count, title, author, encryption status, permissions, form presence, OCR presence heuristic, compression ratio, file size, optional content group (OCG) layers, attachment count.

Example:

```
claw pdf info contract.pdf --json
```

### 1.6 `chars`

> Source: **NOT IMPLEMENTED** — no `pdf/chars.py` exists.

Per-character positional data (pdfplumber `.chars`).

```
claw pdf chars <in.pdf> --pages 1 [--bbox x0,y0,x1,y1] [--json]
```

### 1.7 `words`

> Source: **NOT IMPLEMENTED** — no `pdf/words.py` exists.

Extract words with font filtering.

```
claw pdf words <in.pdf> --pages 1 [--filter "fontname~=Bold"] [--filter "size>=10"] [--json]
```

Filter operators: `=`, `!=`, `~=` (substring), `>=`, `<=`, `>`, `<`.

Example:

```
claw pdf words spec.pdf --pages 1-3 --filter "fontname~=Bold" --filter "size>=14" --json
```

### 1.8 `shapes`

> Source: **NOT IMPLEMENTED** — no `pdf/shapes.py` exists.

Vector objects (lines, rects, curves) from pdfplumber.

```
claw pdf shapes <in.pdf> --pages 1 [--kind line|rect|curve|all] [--json]
```

---

## 2. RENDER

### 2.1 `render`

> Source: [scripts/claw/src/claw/pdf/render.py](../../scripts/claw/src/claw/pdf/render.py)

Rasterize a page to PNG / JPEG.

```
claw pdf render <in.pdf> --page N --out FILE.png [--dpi 300] [--zoom 2.0]
                         [--colorspace rgb|gray|cmyk] [--clip x0,y0,x1,y1]
                         [--no-annots]
```

Example:

```
claw pdf render report.pdf --page 3 --out /tmp/p3.png --dpi 300
```

### 2.2 `tables-debug`

> Source: **NOT IMPLEMENTED** — no `pdf/tables_debug.py` exists.

Overlay pdfplumber's table-detection edges on a rendered page — useful when tuning `--strategy` / `--snap-tol`.

```
claw pdf tables-debug <in.pdf> --page N --out FILE.png [--strategy lines|text|explicit]
                                [--vlines N,N] [--hlines N,N] [--snap-tol 3]
```

Example:

```
claw pdf tables-debug statement.pdf --page 2 --out /tmp/dbg.png --strategy lines --snap-tol 5
```

---

## 3. TRANSFORM

### 3.1 `merge`

> Source: [scripts/claw/src/claw/pdf/merge.py](../../scripts/claw/src/claw/pdf/merge.py)

Pdftk-style concatenation. Each input can carry a range selector.

```
claw pdf merge <out.pdf> <in1[:pages]> <in2[:pages]> ...
                         [--toc-from filenames|none] [--force] [--backup]
```

Example:

```
claw pdf merge /tmp/report.pdf cover.pdf body.pdf:1-10,15 appendix.pdf:all --toc-from filenames
```

### 3.2 `split`

> Source: [scripts/claw/src/claw/pdf/split.py](../../scripts/claw/src/claw/pdf/split.py)

Split by ranges or per page.

```
claw pdf split <in.pdf> [--ranges "1-5,6-end"] [--per-page]
                         --out-dir DIR [--name-template "page-{n:03d}.pdf"]
```

- `--ranges` — one output per range.
- `--per-page` — one output per page.

Example:

```
claw pdf split book.pdf --per-page --out-dir /tmp/pages/
claw pdf split book.pdf --ranges "1-5,6-end" --out-dir /tmp/split/
```

### 3.3 `rotate`

> Source: [scripts/claw/src/claw/pdf/rotate.py](../../scripts/claw/src/claw/pdf/rotate.py)

Rotate pages in place.

```
claw pdf rotate <in.pdf> --pages 3-7 --by 90|-90|180 [--out FILE] [--in-place] [--backup]
```

Example:

```
claw pdf rotate scan.pdf --pages 3-7 --by 90 --in-place --backup
```

### 3.4 `crop`

> Source: **NOT IMPLEMENTED** — no `pdf/crop.py` exists.

Crop a page to a rectangle.

```
claw pdf crop <in.pdf> --page N --box x0,y0,x1,y1 [--out FILE] [--in-place] [--backup]
```

Coordinates are in points with origin top-left (claw normalises PyMuPDF's bottom-left origin internally).

Example:

```
claw pdf crop report.pdf --page 3 --box 72,72,540,720 --out /tmp/cropped.pdf
```

---

## 4. STAMP / WATERMARK

### 4.1 `watermark`

> Source: [scripts/claw/src/claw/pdf/watermark.py](../../scripts/claw/src/claw/pdf/watermark.py)

Diagonal (default) text watermark across every page.

```
claw pdf watermark <in.pdf> --text STR [--opacity 0.2] [--rotate 45]
                             [--color #HEX] [--font Helvetica] [--size 64]
                             [--pages all|1-5] [--layer behind|above]
                             [--out FILE] [--in-place]
```

Example:

```
claw pdf watermark draft.pdf --text "CONFIDENTIAL" --opacity 0.2 --rotate 45 \
  --color "#FF0000" --out /tmp/cf.pdf
```

### 4.2 `stamp`

> Source: **NOT IMPLEMENTED** — no `pdf/stamp.py` exists.

Image stamp at a named anchor or coordinate.

```
claw pdf stamp <in.pdf> --image FILE [--scale 0.2] [--at TL|TR|BL|BR|C]
                         [--offset x,y] [--opacity 1.0] [--pages all|1-5]
                         [--out FILE] [--in-place]
```

Example:

```
claw pdf stamp report.pdf --image logo.png --scale 0.2 --at TR --offset 20,20 --in-place
```

---

## 5. SECURE

### 5.1 `redact`

> Source: [scripts/claw/src/claw/pdf/redact.py](../../scripts/claw/src/claw/pdf/redact.py)

Apply redactions — pixel + text removal. Uses PyMuPDF `apply_redactions`.

```
claw pdf redact <in.pdf> [--regex "SSN \d{3}-\d{2}-\d{4}"]
                          [--terms FILE.txt] [--boxes FILE.json]
                          [--preview preview.png] [--fill #000000]
                          [--dehyphenate] [--pages all|1-5]
                          [--out FILE] [--in-place] [--backup]
```

- `--regex` — regex, applied to each page's text.
- `--terms` — newline-separated literal strings.
- `--boxes` — JSON `[{page, x0, y0, x1, y1}]`.
- `--preview` — don't apply; render overlay showing what *would* be redacted.
- `--dehyphenate` — merge hyphenated line-break words before matching (avoids ligature-glyph misses).

Example (preview before applying):

```
claw pdf redact form.pdf --regex "SSN \d{3}-\d{2}-\d{4}" --preview /tmp/prev.png
claw pdf redact form.pdf --regex "SSN \d{3}-\d{2}-\d{4}" --dehyphenate --in-place --backup
```

### 5.2 `encrypt`

> Source: [scripts/claw/src/claw/pdf/encrypt.py](../../scripts/claw/src/claw/pdf/encrypt.py)

Password-protect with access flags.

```
claw pdf encrypt <in.pdf> --password P [--owner-password OP]
                           [--aes256 | --aes128 | --rc4-128]
                           [--allow print,copy,modify,annotate,fill-forms,assemble,print-high]
                           [--deny print,copy,...]
                           [--out FILE]
```

`--aes256` requires the `pycryptodome` extra; `--aes128` is the default. `--allow` and `--deny` are mutually exclusive — omit both for "deny all except opening".

Example:

```
claw pdf encrypt contract.pdf --password hunter2 --aes256 --allow print --out /tmp/locked.pdf
```

### 5.3 `decrypt`

> Source: [scripts/claw/src/claw/pdf/decrypt.py](../../scripts/claw/src/claw/pdf/decrypt.py)

Remove password protection (requires valid owner or user password).

```
claw pdf decrypt <in.pdf> --password P [--out FILE] [--in-place]
```

### 5.4 `flatten`

> Source: [scripts/claw/src/claw/pdf/flatten.py](../../scripts/claw/src/claw/pdf/flatten.py)

Bake form fields and annotations into static page content.

```
claw pdf flatten <in.pdf> [--forms] [--annotations] [--out FILE] [--in-place]
```

`--forms` (default on) flattens AcroForm + XFA widgets; `--annotations` flattens highlight / note / ink annotations.

Example:

```
claw pdf flatten signed.pdf --forms --annotations --out /tmp/final.pdf
```

---

## 6. ANNOTATE

### 6.1 `annotate`

> Source: **NOT IMPLEMENTED** — no `pdf/annotate.py` exists.

Add a highlight, sticky note, or free-hand ink.

```
claw pdf annotate <in.pdf> --page N \
  [--highlight TERM [--regex]] \
  [--note TEXT --at x,y] \
  [--ink-path "x1,y1 x2,y2 x3,y3 ..."] \
  [--color #FFFF00] [--opacity 0.5] [--author NAME]
  [--out FILE] [--in-place]
```

Example:

```
claw pdf annotate report.pdf --page 2 --highlight "risk" --color "#FFFF00" --in-place
claw pdf annotate report.pdf --page 3 --note "Check with legal" --at 100,150 --author "editor@"
```

---

## 7. FORMS

### 7.1 `form list`

> Source: **NOT IMPLEMENTED** — no `pdf/form.py` / `pdf/form_list.py` exists.

Enumerate AcroForm / XFA fields.

```
claw pdf form list <in.pdf> [--json]
```

Output: `[{name, type, value, flags, page, rect}]`.

### 7.2 `form fill`

> Source: **NOT IMPLEMENTED** — no `pdf/form_fill.py` exists.

Populate fields from a JSON object keyed by field name.

```
claw pdf form fill <in.pdf> --values FILE.json [--flatten] [--out FILE] [--in-place]
```

`--flatten` bakes values into page content after filling (same as `claw pdf flatten --forms`).

Example:

```
claw pdf form fill application.pdf --values answers.json --flatten --out /tmp/submitted.pdf
```

---

## 8. META / STRUCTURE

### 8.1 `meta`

> Source: **NOT IMPLEMENTED** — no `pdf/meta.py` exists.

Core metadata.

```
claw pdf meta get <in.pdf> [--json]
claw pdf meta set <in.pdf> [--title STR] [--author STR] [--subject STR]
                            [--keywords a,b,c] [--creator STR] [--producer STR]
                            [--creation-date YYYY-MM-DD] [--mod-date YYYY-MM-DD]
                            [--out FILE] [--in-place]
```

### 8.2 `toc`

> Source: **NOT IMPLEMENTED** — no `pdf/toc.py` exists.

Read or overwrite the outline / bookmarks tree.

```
claw pdf toc get <in.pdf> [--json]
claw pdf toc set <in.pdf> --json FILE [--out FILE] [--in-place]
```

Format: `[[level, title, page, {"kind":"GoTo","page":N,"to":[0,792]}], ...]`.

Example:

```
claw pdf toc get book.pdf --json > toc.json
$EDITOR toc.json
claw pdf toc set book.pdf --json toc.json --in-place --backup
```

### 8.3 `bookmark add`

> Source: **NOT IMPLEMENTED** — no `pdf/bookmark.py` exists.

Append a single bookmark (alternative to full `toc set`).

```
claw pdf bookmark add <in.pdf> --title STR --page N [--level 1] [--parent "Chapter 1"]
                                [--out FILE] [--in-place]
```

### 8.4 `layer toggle`

> Source: **NOT IMPLEMENTED** — no `pdf/layer.py` exists.

Show / hide an Optional Content Group (layer).

```
claw pdf layer toggle <in.pdf> --name NAME [--show | --hide] [--out FILE] [--in-place]
```

Example:

```
claw pdf layer toggle map.pdf --name "Topology" --hide --in-place
```

### 8.5 `labels set`

> Source: **NOT IMPLEMENTED** — no `pdf/labels.py` exists.

Set PDF page label ruleset (e.g. roman numerals for front matter).

```
claw pdf labels set <in.pdf> --rule "i:1-5,1:6-end" [--out FILE] [--in-place]
```

Each rule chunk is `style:range` where style is `i` (lowercase roman), `I` (uppercase roman), `a` / `A` (letters), `1` (decimal).

Example:

```
claw pdf labels set book.pdf --rule "i:1-8,1:9-end" --in-place
```

### 8.6 `attach`

> Source: **NOT IMPLEMENTED** — no `pdf/attach.py` exists.

File attachments (embedded files).

```
claw pdf attach list <in.pdf> [--json]
claw pdf attach add  <in.pdf> --file FILE [--name NAME] [--description STR] [--in-place]
claw pdf attach extract <in.pdf> --name NAME --out FILE
claw pdf attach remove <in.pdf> --name NAME [--in-place]
```

### 8.7 `journal`

> Source: **NOT IMPLEMENTED** — no `pdf/journal.py` exists.

Experimental — stage a series of edits, inspect, commit or roll back. Each verb supports `--journal NAME` which writes staged changes to a sidecar.

```
claw pdf journal start  <in.pdf> --name edit-session
# ... mutating verbs with --journal edit-session ...
claw pdf journal status --name edit-session [--json]
claw pdf journal commit --name edit-session [--out FILE] [--in-place]
claw pdf journal rollback --name edit-session
```

Example:

```
claw pdf journal start book.pdf --name fix
claw pdf rotate  book.pdf --pages 3-7 --by 90 --journal fix
claw pdf meta set book.pdf --title "Revised" --journal fix
claw pdf journal commit --name fix --in-place --backup
```

---

## 9. OCR

### 9.1 `ocr`

> Source: [scripts/claw/src/claw/pdf/ocr.py](../../scripts/claw/src/claw/pdf/ocr.py)

Run OCR via PyMuPDF + Tesseract. Produces a text layer over the original pixels so `claw pdf search` / `extract-text` then work.

```
claw pdf ocr <in.pdf> [--lang eng] [--dpi 300] [--sidecar]
                      [--pages all|1-5] [--out FILE] [--in-place]
```

- `--lang` — Tesseract language code(s), e.g. `eng+fra`.
- `--sidecar` — also write `<out>.txt` containing the extracted text.

Example:

```
claw pdf ocr scan.pdf --lang eng+fra --dpi 300 --sidecar --out /tmp/searchable.pdf
```

---

## 10. CREATE

### 10.1 `from-html`

> Source: [scripts/claw/src/claw/pdf/from_html.py](../../scripts/claw/src/claw/pdf/from_html.py)

HTML → PDF via reportlab's Story API. Accepts a subset of HTML (paragraphs, headings, tables, lists, images, inline styling).

```
claw pdf from-html <in.html> <out.pdf> [--rect "1in,1in,7.5in,10in"]
                                        [--page-size Letter|A4|Legal]
                                        [--css FILE.css] [--force]
```

Example:

```
claw pdf from-html invoice.html /tmp/invoice.pdf --rect "0.5in,0.5in,8in,10.5in" --css brand.css
```

### 10.2 `from-md`

> Source: [scripts/claw/src/claw/pdf/from_md.py](../../scripts/claw/src/claw/pdf/from_md.py)

Markdown → PDF via reportlab PLATYPUS with theme presets.

```
claw pdf from-md <in.md> <out.pdf> [--theme minimal|corporate|academic|dark]
                                    [--page-size Letter|A4] [--margin 1in]
                                    [--toc] [--title STR] [--author STR]
                                    [--engine reportlab|pypdf|pymupdf]
                                    [--force]
```

Example:

```
claw pdf from-md spec.md /tmp/spec.pdf --theme corporate --toc --title "Spec" --author "Eng"
```

### 10.3 `convert`

> Source: **NOT IMPLEMENTED** — no `pdf/convert.py` exists.

Convert other document formats (EPUB, XPS, CBZ, plaintext) to PDF.

```
claw pdf convert <in.epub|xps|cbz|txt> <out.pdf> [--page-size A4] [--force]
```

Example:

```
claw pdf convert novel.epub /tmp/novel.pdf
```

### 10.4 `qr`

> Source: [scripts/claw/src/claw/pdf/qr.py](../../scripts/claw/src/claw/pdf/qr.py)

QR code PDF (single-page, value-centred).

```
claw pdf qr --value STR --out FILE.pdf [--size 150] [--ec L|M|Q|H] [--page-size A4]
            [--caption STR]
```

Example:

```
claw pdf qr --value "https://example.com" --out /tmp/qr.pdf --size 200 --caption "Scan me"
```

### 10.5 `barcode`

> Source: **NOT IMPLEMENTED** — no `pdf/barcode.py` exists.

Various barcode types.

```
claw pdf barcode --type code128|ean|ean13|upc|qr --value V --out FILE.pdf
                 [--size WxH] [--caption STR]
```

Example:

```
claw pdf barcode --type code128 --value "SKU-004321" --out /tmp/label.pdf --size 3inx1in
```

---

## When `claw pdf` Isn't Enough

Drop to the library directly:

| Use case | Why `claw` can't do it |
|---|---|
| Freeform reportlab Canvas drawing (custom vector graphics, precise glyph placement) | Flag surface is finite |
| Custom AcroForm authoring from scratch (new fields, validation JS, appearance streams) | Only fill / flatten is exposed |
| Low-level XREF editing, object stream rewriting | Not a typical CLI use case |
| `NumberedCanvas` subclass pattern for "Page X of Y" totals | Requires Python class-level hook |
| Bespoke table-extraction heuristics (cluster-then-project) | Beyond the `--strategy` preset set |

**PyMuPDF** — `pip install pymupdf` · [docs](https://pymupdf.readthedocs.io/)
- Import is `import fitz`, not `import pymupdf` (legacy binding name; `pymupdf` module alias exists in newer versions but examples on the net use `fitz`).
- Licensed **AGPL-3.0** — commercial closed-source deployments must either buy a commercial license or avoid PyMuPDF (use `pypdf` + `pdfplumber` + `reportlab`).
- Coordinate origin is bottom-left (PDF convention); `claw pdf` normalises to top-left on input/output, so when hand-crafting `--boxes` JSON from raw PyMuPDF code you must flip `y' = page_height - y`.

**PyPDF2 / pypdf** — `pip install pypdf` · [docs](https://pypdf.readthedocs.io/)
- The package was renamed from `PyPDF2` to `pypdf` in 2022 — install `pypdf` and `import pypdf`; `PyPDF2` on PyPI still exists but is the frozen pre-rename version.
- `reader.pages[i]` lazily parses — holding the reader open is cheap, but mutating via `writer.add_page(reader.pages[i])` clones references, so a later `reader.close()` can invalidate them.
- AES-256 encryption requires `pip install pypdf[crypto]` (pulls in `cryptography`); without the extra, `writer.encrypt(algorithm="AES-256")` silently falls back to AES-128 on some versions.

**pdfplumber** — `pip install pdfplumber` · [docs](https://github.com/jsvine/pdfplumber)
- Built on `pdfminer.six`; table extraction is deterministic but extremely sensitive to `table_settings` — `{"vertical_strategy": "text", "horizontal_strategy": "lines"}` vs `"lines"`/`"text"` gives totally different row counts.
- `page.extract_text()` returns text in *rendering order*, which is often not reading order for multi-column layouts; use `page.extract_text(layout=True)` or cluster by `page.chars` manually.
- Scanned PDFs produce empty strings, not errors — run `claw pdf ocr` first if `len(text.strip()) == 0` for a page.

**reportlab** — `pip install reportlab` · [docs](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- Coordinate origin is bottom-left and the unit is 1/72 inch; `from reportlab.lib.units import inch, cm, mm` — forgetting this is the classic "my text is 5 points from the bottom" bug.
- `Canvas.showPage()` commits the current page and resets state (fonts, fills, transforms); forgetting it merges page N's content into page N+1.
- Custom fonts must be registered via `pdfmetrics.registerFont(TTFont('Name', 'path.ttf'))` *before* the first `setFont` — registration after yields a silent fallback to Helvetica.

## Footguns

- **PyMuPDF is AGPL-3.0.** See Critical Rules. If your deployment cannot comply with AGPL, restrict yourself to `--engine pypdf|reportlab` and note that `extract-text`, `redact`, `ocr`, `annotate`, `layer`, and `journal` *require* PyMuPDF.
- **`doc.save(same_path)` raises** unless `incremental=True`. `claw pdf ... --in-place` wraps this with an atomic tmp-then-rename, so you never hit the ambiguity.
- **Ligature-glyph regex mismatches in redaction.** Words like `office`, `flame`, `fiction` get written as single ligature glyphs (`ﬃ`, `ﬀ`, `ﬁ`) in many PDFs. Pass `--dehyphenate` and enable ligature normalisation (automatic when `--regex` contains alphanumerics).
- **AES-256 needs `pycryptodome`.** Install with `pip install 'claw[crypto]'` or fall back to `--aes128`.
- **Origin convention.** Rectangle coordinates in `claw pdf` use **top-left origin, y increasing downward** (matches screen/image tools). PyMuPDF's internal origin is bottom-left — `claw` normalises both on input (`--box`) and output (`--json`). If you hand-craft `--boxes` JSON from PyMuPDF code, convert first (`y' = page_height - y`).
- **`extract-tables --strategy lines` misses borderless tables.** Use `text` or hand-supply `--vlines`/`--hlines`. `tables-debug` is the fastest way to diagnose.
- **Incremental save accumulates cruft.** `--in-place` does an incremental save by default. For long edit chains use `--no-incremental` (rewrites the whole file) or `journal commit` (single atomic rewrite).
- **Form fields survive `redact`.** Redactions don't remove form widgets — call `flatten --forms` first if fields might carry sensitive defaults.
- **`merge` preserves outlines but renumbers pages.** Bookmark destinations pointing to merged files are remapped; external `GoToR` destinations stay unchanged.

---

## Quick Reference

| Task | One-liner |
|------|-----------|
| Extract text | `claw pdf extract-text in.pdf --out out.txt` |
| Extract tables → xlsx | `claw pdf extract-tables in.pdf --out out.xlsx` |
| Merge | `claw pdf merge out.pdf a.pdf b.pdf:1-5` |
| Split per page | `claw pdf split in.pdf --per-page --out-dir pages/` |
| Rotate | `claw pdf rotate in.pdf --pages 3-7 --by 90 --in-place` |
| Watermark | `claw pdf watermark in.pdf --text "DRAFT" --opacity 0.2 --rotate 45 --out w.pdf` |
| Redact SSNs | `claw pdf redact in.pdf --regex "\d{3}-\d{2}-\d{4}" --in-place --backup` |
| Encrypt | `claw pdf encrypt in.pdf --password P --aes256 --out locked.pdf` |
| OCR scan | `claw pdf ocr scan.pdf --lang eng --dpi 300 --out searchable.pdf` |
| Render page → PNG | `claw pdf render in.pdf --page 1 --out p1.png --dpi 300` |
| Markdown → PDF | `claw pdf from-md spec.md spec.pdf --theme corporate --toc` |
| QR PDF | `claw pdf qr --value https://example.com --out qr.pdf` |
| Fill form | `claw pdf form fill f.pdf --values answers.json --flatten --out done.pdf` |
| Search with context | `claw pdf search in.pdf --term "SSN" --regex --context 60 --json` |
