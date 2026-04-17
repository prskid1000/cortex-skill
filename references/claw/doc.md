# `claw doc` — Google Docs Operations Reference

> Source directory: [scripts/claw/src/claw/doc/](../../scripts/claw/src/claw/doc/)

CLI wrapper over `gws docs` for Google Docs work. Absorbs the 100-line markdown → `batchUpdate` builder pattern, handles the `tabId` + Windows-command-line chunking gotchas, and exports to multiple formats in a single verb.

Library API for escape hatches: [references/gws-cli.md § Docs](../gws-cli.md#docs).

## Contents

- **CREATE a document**
  - [New Doc (optionally populated + shared)](#11-create)
- **BUILD / POPULATE content**
  - [Markdown → styled Doc (batchUpdate)](#21-build) · [Append text](#22-append) · [Replace placeholders](#23-replace)
- **READ a document**
  - [Dump text / JSON / markdown](#31-read) · [List tabs](#32-tabs-list)
- **EXPORT to another format**
  - [PDF / DOCX / HTML / Markdown / plain text](#41-export)
- **SHARE the doc** — use [`claw sheet share`](sheet.md#31-share) (Drive permissions work on any file — Docs included)
- **When `claw doc` isn't enough** — [escape hatches](#when-claw-doc-isnt-enough)

---

## Critical Rules

1. **Safe-by-default builds** — `build` computes the full request list, validates it against the Docs schema, then dispatches in chunks of 6–8 requests per `batchUpdate` call to stay under Windows' 32 KiB command-line limit. If any chunk fails, `claw` logs the last successful index and exits 3 (partial) — rerun with `--from-index N` to resume.
2. **`tabId` injection** — newly created Google Docs use tab-based structure; every `location`/`range` must carry `tabId: "t.0"`. `claw doc build` injects this automatically. If you target a custom tab, pass `--tab TAB_ID` and `claw` rewrites all requests.
3. **Selectors** — `<doc-id>` is the positional Google Drive file id. `--tab TAB_ID` accepts a tab id or 1-based index (`1` → `t.0`, `2` → `t.1`). `--range START:END` uses 1-based character indices. Markdown is detected by `.md` extension or `--format md`.
4. **Structured output** — every verb supports `--json`. Machine-readable shape is `{doc_id, revision_id, url, operations?}`. Errors under `--json` emit `{error, code, hint, doc_url}` to stderr.
5. **Exit codes** — `0` success, `1` generic, `2` usage error, `3` partial (one chunk of a multi-chunk `batchUpdate` failed), `4` bad input / missing file, `5` API / auth error, `130` SIGINT.
6. **Help** — `claw doc --help`, `claw doc <verb> --help`, `--examples` prints runnable recipes, `--progress=json` streams one NDJSON line per chunk submitted.
7. **Tab content fetch** — `read` and `export` both pass `includeTabsContent: true` transparently. Without it, newly created docs return an empty body from the API. Never manually hit `documents.get` for new docs without this flag.
8. **Common output flags** — every mutating verb inherits `--force`, `--backup`, `--dry-run`, `--json`, `--quiet`, `--mkdir` via the shared `@common_output_options` decorator. Individual verb blocks only call them out when the verb overrides the default; run `claw doc <verb> --help` for the authoritative per-verb flag list.

---

## 1. CREATE

### 1.1 `create`

> Source: [scripts/claw/src/claw/doc/create.py](../../scripts/claw/src/claw/doc/create.py)

Create a new Google Doc. Optionally populate from markdown and share in one shot.

```
claw doc create --title T [--from FILE.md] [--parent FOLDER_ID]
                          [--share ACL]... [--tab TAB_ID]
                          [--json]
```

Flags:

- `--title` — required.
- `--from FILE.md` — populate the new doc from a markdown file (see [§2.1 `build`](#21-build) for the markdown dialect).
- `--parent FOLDER_ID` — place in a Drive folder.
- `--share ACL` — repeatable. Syntax: `user:EMAIL:reader|commenter|writer`, `domain:DOMAIN:reader`, `anyone:reader`.

Examples:

```
claw doc create --title "Q3 Report" --from q3.md --parent 1aBcD...
```

```
claw doc create --title "Spec" --from spec.md \
  --share user:alice@example.com:writer --share anyone:reader
```

Output (with `--json`):

```json
{"doc_id": "1Abc...", "revision_id": "ALm9...", "url": "https://docs.google.com/document/d/1Abc.../edit"}
```

---

## 2. BUILD / POPULATE

### 2.1 `build`

> Source: [scripts/claw/src/claw/doc/build.py](../../scripts/claw/src/claw/doc/build.py)

Apply a markdown file to an existing Doc. Maps markdown blocks → `batchUpdate` requests:

| Markdown | Doc style |
|----------|-----------|
| `# Title` | `namedStyleType: TITLE` |
| `## Heading` | `HEADING_1` |
| `### Heading` | `HEADING_2` (through `HEADING_6`) |
| `> quote` | `NORMAL_TEXT` with left indent + italic |
| `**bold**` | `textStyle.bold: true` run |
| `*italic*` | `textStyle.italic: true` run |
| `` `code` `` | `textStyle.weightedFontFamily: "Consolas"` run |
| `[text](url)` | `textStyle.link.url` run |
| `- item` / `1. item` | `createParagraphBullets` with `BULLET_DISC_CIRCLE_SQUARE` / `NUMBERED_DECIMAL_*` |

```
claw doc build <doc-id> --from FILE.md [--tab TAB_ID] [--append]
                                       [--replace-all]
                                       [--chunk-size N] [--from-index N]
                                       [--json]
```

Flags:

- `--tab TAB_ID` — defaults to `t.0`. Accepts a tab id or 1-based index.
- `--append` — append after existing content (default replaces the tab body).
- `--replace-all` — equivalent to `--append=false`; explicit for scripts.
- `--chunk-size N` — requests per `batchUpdate` call (default 8). Lower if you hit Windows command-line limits with long bodies.
- `--from-index N` — resume from request index `N` (used by exit-code-3 recovery).

Index tracking: `build` computes a running `insertionIndex` cursor across all chunks, so multi-chunk builds don't corrupt offsets. `--json` output includes `{chunks: N, last_index: M}`.

Examples:

```
claw doc build 1Abc... --from q3.md
```

```
claw doc build 1Abc... --from appendix.md --tab t.1 --append
```

### 2.2 `append`

> Source: **NOT IMPLEMENTED** — no `doc/append.py` exists.

Simpler than `build` — append a text paragraph (or a whole file) to the tab.

```
claw doc append <doc-id> (--text STR | --from FILE) [--tab TAB_ID] [--json]
```

Example:

```
claw doc append 1Abc... --text "Reviewed $(date -I)."
```

### 2.3 `replace`

> Source: **NOT IMPLEMENTED** — no `doc/replace.py` exists.

Find-and-replace across the doc (wraps `replaceAllText` request).

```
claw doc replace <doc-id> --find STR --with STR [--match-case] [--tab TAB_ID] [--json]
```

Example:

```
claw doc replace 1Abc... --find "{{QUARTER}}" --with "Q3 2025"
```

---

## 3. READ

### 3.1 `read`

> Source: [scripts/claw/src/claw/doc/read.py](../../scripts/claw/src/claw/doc/read.py)

Dump the doc content. Defaults to plain text. Always passes `includeTabsContent: true`.

```
claw doc read <doc-id> [--tab TAB_ID] [--format text|json|md]
                       [--range START:END] [--out FILE|-]
```

Flags:

- `--format text` — flattened text, paragraphs separated by `\n`.
- `--format json` — Docs API response (full structure).
- `--format md` — best-effort reverse of [§2.1 `build`](#21-build); round-trip lossless for Title / Heading / Bold / Italic / Links / Bullets. Drops: tables, images, suggestions.
- `--out -` — stdout (default).

Examples:

```
claw doc read 1Abc... --format md --out /tmp/doc.md
```

```
claw doc read 1Abc... --format json | jq '.tabs[0].documentTab.body.content | length'
```

### 3.2 `tabs list`

> Source: **NOT IMPLEMENTED** — no `doc/tabs.py` / `doc/tabs_list.py` exists.

List all tabs in a doc.

```
claw doc tabs list <doc-id> [--json]
```

Output: `[{tab_id, title, index}, ...]`.

---

## 4. EXPORT

### 4.1 `export`

> Source: [scripts/claw/src/claw/doc/export.py](../../scripts/claw/src/claw/doc/export.py)

Export the whole doc to a downloadable format via `drive.files.export`.

```
claw doc export <doc-id> --as pdf|docx|html|md|txt|epub --out FILE [--force]
```

Flags:

- `--as md` — uses Google's native markdown export (Docs added this in 2024).
- `--as epub` — exports via a PDF → EPUB fallback if the Docs API doesn't support EPUB for this doc version.

MIME mapping (for reference — `claw` handles this):

| `--as` | MIME type |
|--------|-----------|
| `pdf` | `application/pdf` |
| `docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `html` | `text/html` |
| `md` | `text/markdown` |
| `txt` | `text/plain` |
| `epub` | `application/epub+zip` |

Examples:

```
claw doc export 1Abc... --as pdf --out /tmp/report.pdf
```

```
claw doc export 1Abc... --as docx --out /tmp/report.docx --force
```

---

## When `claw doc` Isn't Enough

Drop into `gws docs documents batchUpdate` directly for:

| Use case | Why `claw` can't do it | Library anchor |
|---|---|---|
| Complex `batchUpdate` request shapes (named ranges, positioned objects, suggestions API) | `build` covers text + style + lists; no arbitrary request surface | [gws-cli.md § batchUpdate](../gws-cli.md#batchupdate--insertdelete-text-apply-formatting-insert-tables) |
| Comments / replies / suggestion mode | Out of scope | [gws-cli.md § drive comments](../gws-cli.md#comments) and [replies](../gws-cli.md#replies) |
| Table insertion with row/column merges | `build` emits text + headings only | Use `{"insertTable": {...}}` + `{"mergeTableCells": {...}}` requests directly |
| Inline image insertion by Drive file id | No image verb | Use `{"insertInlineImage": {"uri": "...", "location": {...}}}` |
| Real-time collaborative cursor sync | Not a batch operation | Docs API doesn't expose this; use the JS SDK |
| Suggestion-mode edits (`SUGGESTIONS_INLINE`) | No suggestion surface | `writeControl.targetRevisionId` + API |

## Footguns

- **Missing `tabId`** — the Docs API happily returns 200 OK on requests without `tabId` on a tabbed doc, and **silently drops the content**. Always let `claw` inject it; never hand-roll JSON without it.
- **Index drift in multi-chunk builds** — if you send chunk A (inserts 50 chars at index 1), chunk B's indices must start from 51, not 1. `claw doc build` tracks this; manual `batchUpdate` loops frequently corrupt offsets.
- **Docs API quotas** — per-user ~300 write requests / 60s. `build` respects this with 100ms jitter between chunks. Custom batch loops get 429'd hard.
- **`replace` regex escaping** — `--find` is a literal string, not a regex. For regex, drop to `documents.batchUpdate` with `{"replaceAllText": {"containsText": {"text": "...", "matchCase": true}}}` — the Docs API itself doesn't support regex either.
- **Export of a doc with unresolved suggestions** — PDF/DOCX export accepts suggestions as the final text (not the original). `--as pdf` returns the post-accept view.
- **Round-trip `read --format md` → `build --from`** — lossless for the subset listed in [§2.1](#21-build). Images, tables, equations, and drawings are dropped by the MD writer.

---

## Quick Reference

| Task | One-liner |
|------|-----------|
| Create blank | `claw doc create --title "Spec"` |
| Create + populate | `claw doc create --title "Report" --from report.md` |
| Create + share | `claw doc create --title "X" --from x.md --share user:a@x:writer` |
| Append text | `claw doc append <DOC_ID> --text "Done."` |
| Replace placeholder | `claw doc replace <DOC_ID> --find "{{Q}}" --with "Q3"` |
| Read as markdown | `claw doc read <DOC_ID> --format md` |
| Export to PDF | `claw doc export <DOC_ID> --as pdf --out report.pdf` |
| Export to DOCX | `claw doc export <DOC_ID> --as docx --out report.docx` |
| Share publicly (read) | `claw doc share <DOC_ID> --anyone --role reader` |
| List tabs | `claw doc tabs list <DOC_ID> --json` |
