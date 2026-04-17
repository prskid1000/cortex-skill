# `claw sheet` — Google Drive Upload / Download / Share Reference

> Source directory: [scripts/claw/src/claw/sheet/](../../scripts/claw/src/claw/sheet/)

CLI wrapper over `gws drive`. Covers the 80% of Drive work that isn't spreadsheet-cell editing: uploading local files (with optional auto-convert to Google-native format), downloading Google-native files (via `files.export`) or binary uploads (via `files.get ... alt=media`), sharing, and listing.

For per-cell `spreadsheets.values` work, fall through to [`gws sheets`](../gws-cli.md#sheets) — this wrapper deliberately doesn't try to re-invent sheet editing.

Library API for escape hatches: [references/gws-cli.md § Drive](../gws-cli.md#drive) and [§ Sheets](../gws-cli.md#sheets).

## Contents

- **UPLOAD a local file to Drive**
  - [Upload (auto-convert xlsx/csv/docx → Google-native)](#11-upload)
- **DOWNLOAD a file from Drive**
  - [Download (export Google-native; `alt=media` for uploads)](#21-download)
- **SHARE a file**
  - [Grant user / domain / anyone permission](#31-share) · [List current permissions](#32-share-list) · [Revoke](#33-share-revoke)
- **LIST files in Drive**
  - [Search with query / parent filter](#41-list)
- **MOVE / COPY / RENAME**
  - [Move between folders, duplicate, rename](#51-move) · [Copy](#52-copy) · [Rename](#53-rename)
- **DELETE**
  - [Trash (recoverable) or permanent delete](#61-delete)
- **When `claw sheet` isn't enough** — [escape hatches](#when-claw-sheet-isnt-enough)

---

## Critical Rules

1. **Safe-by-default downloads** — `download` writes to `<out>.tmp`, verifies byte count vs. `Content-Length`, then atomic-renames. `--force` is required to overwrite an existing file. `--backup` keeps a `<out>.bak` sidecar.
2. **`--convert` default is smart** — if the source extension matches a Google-native target (`.xlsx`→Sheet, `.docx`→Doc, `.pptx`→Slides, `.csv`→Sheet), `--convert` is `on` by default. Force with `--convert=on` / `--convert=off`.
3. **Selectors** — `<file-id>` is a positional Drive file id. Folder references accept either a folder id (`1aBc...`) or a path-style alias `/Work/2025/Q3` if `claw sheet config --alias` has been set.
4. **Structured output** — every verb supports `--json`. `list` emits NDJSON (one file per line). `upload`/`download`/`share` emit a single result object. Errors under `--json` emit `{error, code, hint, doc_url}` to stderr.
5. **Exit codes** — `0` success, `1` generic, `2` usage error, `3` partial (one of N in a batch failed), `4` bad input / missing file, `5` API / auth / quota error, `130` SIGINT.
6. **Help** — `claw sheet --help`, `claw sheet <verb> --help`, `--examples` prints runnable recipes, `--progress=json` streams per-chunk upload progress (Drive uses resumable upload for files >5 MB).
7. **Content-type detection** — upload MIME type is detected via `mimetypes` with an override table for Office formats. Override with `--mime TYPE`. Unknown extensions default to `application/octet-stream`.
8. **Common output flags** — every mutating verb inherits `--force`, `--backup`, `--dry-run`, `--json`, `--quiet`, `--mkdir` via the shared `@common_output_options` decorator. Individual verb blocks only call them out when the verb overrides the default; run `claw sheet <verb> --help` for the authoritative per-verb flag list.

---

## 1. UPLOAD

### 1.1 `upload`

> Source: [scripts/claw/src/claw/sheet/upload.py](../../scripts/claw/src/claw/sheet/upload.py)

Upload a local file to Drive. Auto-converts to Google-native format when the extension matches.

```
claw sheet upload --from FILE [--name N] [--parent FOLDER_ID]
                              [--convert on|off] [--mime TYPE]
                              [--description STR] [--json]
```

Flags:

- `--from FILE` — local path. `-` is reserved for future stdin upload but not currently supported (file-size metadata is needed upfront for resumable upload).
- `--name N` — target name in Drive (defaults to `basename(FILE)`).
- `--parent FOLDER_ID` — put the upload in this folder. Can be repeated for multi-parent (shortcut-style).
- `--convert on` — force conversion to Google-native (e.g. upload an `.xlsx` and land a Google Sheet, not an attached Excel file).
- `--convert off` — keep the uploaded file as-is (the xlsx stays an xlsx in Drive).
- `--mime TYPE` — override detected MIME type.

Conversion map (default when `--convert` unset):

| Source extension | Default target | MIME in (upload) | MIME out (Drive) |
|---|---|---|---|
| `.xlsx` / `.csv` / `.tsv` | Google Sheet | `...spreadsheetml.sheet` / `text/csv` | `application/vnd.google-apps.spreadsheet` |
| `.docx` | Google Doc | `...wordprocessingml.document` | `application/vnd.google-apps.document` |
| `.pptx` | Google Slides | `...presentationml.presentation` | `application/vnd.google-apps.presentation` |
| `.pdf` | PDF (no conversion) | `application/pdf` | unchanged |
| other | unchanged | auto | unchanged |

Examples:

```
claw sheet upload --from /tmp/report.xlsx --parent 1abcFolder
```

```
claw sheet upload --from /tmp/raw.csv --name "Raw Q3" --convert off
```

Output (with `--json`):

```json
{"file_id": "1xYz...", "name": "report", "mime_type": "application/vnd.google-apps.spreadsheet", "web_view_link": "https://docs.google.com/..."}
```

---

## 2. DOWNLOAD

### 2.1 `download`

> Source: [scripts/claw/src/claw/sheet/download.py](../../scripts/claw/src/claw/sheet/download.py)

Save a Drive file to local disk. Dispatches `files.export` for Google-native files, `files.get ... alt=media` for binary uploads.

```
claw sheet download <file-id> --out PATH [--as xlsx|csv|pdf|docx|html|txt|epub|md]
                                        [--force] [--backup] [--json]
```

Flags:

- `<file-id>` — positional Drive id.
- `--out PATH` — destination.
- `--as` — required for Google-native files (Sheet / Doc / Slides); ignored for binary uploads. Supported values:
  - Sheets: `xlsx` · `csv` · `pdf` · `ods` · `html` · `tsv`
  - Docs: `docx` · `pdf` · `md` · `txt` · `html` · `epub` · `odt` · `rtf`
  - Slides: `pptx` · `pdf` · `odp` · `txt`
- `--force` — overwrite existing.

Examples:

```
claw sheet download 1xYz... --out /tmp/report.xlsx --as xlsx
```

```
claw sheet download 1xYz... --out /tmp/report.pdf --as pdf --force
```

For a binary file already stored as-is (a PDF uploaded with `--convert off`), omit `--as`:

```
claw sheet download 1pdfId --out /tmp/copy.pdf
```

---

## 3. SHARE

### 3.1 `share`

> Source: [scripts/claw/src/claw/sheet/share.py](../../scripts/claw/src/claw/sheet/share.py)

Grant permission on a file or folder. Exactly one of `--user` / `--domain` / `--anyone`.

```
claw sheet share <file-id> (--user EMAIL --role reader|commenter|writer|owner
                            | --domain DOMAIN --role reader|commenter|writer
                            | --anyone --role reader|commenter)
                           [--notify] [--message STR] [--transfer-ownership]
                           [--json]
```

Flags:

- `--role owner` + `--user EMAIL` requires `--transfer-ownership` (Google Drive refuses without it).
- `--notify` — send the recipient the default Drive notification email (off by default).
- `--message STR` — personalize the notification; implies `--notify`.

Examples:

```
claw sheet share 1xYz... --user alice@example.com --role writer --notify \
  --message "Review by Friday please"
```

```
claw sheet share 1xYz... --anyone --role reader
```

```
claw sheet share 1xYz... --user new@example.com --role owner --transfer-ownership
```

### 3.2 `share list`

> Source: **NOT IMPLEMENTED** — no `sheet/share_list.py` exists.

List current permissions on a file.

```
claw sheet share list <file-id> [--json]
```

Output: `[{permission_id, role, type, email?, domain?}, ...]`.

### 3.3 `share revoke`

> Source: **NOT IMPLEMENTED** — no `sheet/share_revoke.py` exists.

Remove a permission by id (get ids from `share list`).

```
claw sheet share revoke <file-id> <permission-id> [--json]
```

Example:

```
claw sheet share revoke 1xYz... 10abcPerm
```

---

## 4. LIST

### 4.1 `list`

> Source: [scripts/claw/src/claw/sheet/list_.py](../../scripts/claw/src/claw/sheet/list_.py)

List Drive files. Forwards to `gws drive files list --q` with sugar.

```
claw sheet list [--parent FOLDER_ID] [--query Q] [--mime MIME]
                [--name CONTAINS] [--max N] [--all]
                [--format table|json]
```

Flags:

- `--parent FOLDER_ID` — expands to `"<FOLDER_ID>" in parents`.
- `--query Q` — raw Drive search string (see [Drive search syntax](https://developers.google.com/drive/api/guides/search-files)).
- `--mime MIME` — shortcut for `mimeType = "MIME"`. Accepts shortnames: `sheet`, `doc`, `slides`, `folder`, `pdf`.
- `--name CONTAINS` — expands to `name contains "CONTAINS"`.
- `--all` — paginate everything (NDJSON stream — use with care for large drives).

Examples:

```
claw sheet list --parent 1abcFolder --mime sheet --max 25
```

```
claw sheet list --name "Q3" --format json | jq '.name'
```

```
claw sheet list --query "modifiedTime > '2025-01-01' and trashed = false" --all
```

---

## 5. MOVE / COPY / RENAME

### 5.1 `move`

> Source: **NOT IMPLEMENTED** — no `sheet/move.py` exists.

Move a file between folders. Uses `files.update` with `addParents` / `removeParents`.

```
claw sheet move <file-id> --to FOLDER_ID [--from FOLDER_ID] [--json]
```

If `--from` is omitted, `claw` removes from the file's current parents.

Example:

```
claw sheet move 1xYz... --to 1archiveFolder
```

### 5.2 `copy`

> Source: **NOT IMPLEMENTED** — no `sheet/copy.py` exists.

Duplicate a file (Drive-side; no download).

```
claw sheet copy <file-id> [--name N] [--parent FOLDER_ID] [--json]
```

Example:

```
claw sheet copy 1xYz... --name "Copy of Report" --parent 1newFolder
```

### 5.3 `rename`

> Source: **NOT IMPLEMENTED** — no `sheet/rename.py` exists.

Shortcut for `files.update` with a new `name`.

```
claw sheet rename <file-id> --name N [--json]
```

Example:

```
claw sheet rename 1xYz... --name "Q3 Final"
```

---

## 6. DELETE

### 6.1 `delete`

> Source: **NOT IMPLEMENTED** — no `sheet/delete.py` exists.

Trash (recoverable, default) or permanently delete (flag-gated).

```
claw sheet delete <file-id> [--permanent] [--yes]
```

Flags:

- `--yes` — skip the interactive confirmation prompt (required for `--permanent` in non-TTY environments).

Example:

```
claw sheet delete 1xYz... --permanent --yes
```

---

## When `claw sheet` Isn't Enough

Drop into `gws` directly for:

| Use case | Why `claw` can't do it | Library anchor |
|---|---|---|
| Per-cell Sheets `values.update` / `values.append` | Out of scope — that's sheet-cell editing, not Drive file-ops | [gws-cli.md § Sheets](../gws-cli.md#sheets), [`gws sheets +append`](../gws-cli.md#ergonomic-helper-commands) |
| `spreadsheets.batchUpdate` (add/delete sheets, conditional formatting, charts) | Same | [gws-cli.md § batchUpdate](../gws-cli.md#batchupdate--structural-changes-adddelete-sheets-formatting-charts) |
| Drive `changes` feed / watch channels (push notifications) | Long-running API | `gws drive changes list` + webhook endpoint |
| Shared drives (`drives` resource) | Not wrapped; infrequently used | [gws-cli.md § Shared Drives](../gws-cli.md#drives-shared-drives) |
| File revisions (pin / unpin) | Not wrapped | [gws-cli.md § revisions](../gws-cli.md#revisions) |
| Comments / replies | Not Drive-file-ops | [gws-cli.md § comments](../gws-cli.md#comments) |

## Footguns

- **Silent `--convert` mismatch** — uploading `.xlsx` without `--convert off` gives you a Google Sheet, not an attached xlsx. If the downstream consumer expects an xlsx, explicitly pass `--convert off`.
- **`share --role owner` without `--transfer-ownership`** — Drive API returns 400. `claw` fails fast with `code=OWNER_REQUIRES_TRANSFER`.
- **`--parent` on upload = additional parent** — not "set the single parent". To move between folders, use `move`, not `upload` with `--parent`.
- **Download of a huge Google Sheet as `csv`** — the export endpoint has a 10 MB cap; larger sheets return 403. Use `--as xlsx` instead (100 MB cap) or drop to `spreadsheets.values.batchGet` for ranged reads.
- **`list --all` on a shared drive** — forwards to `--page-all`; can pull megabytes. Always scope with `--parent` or `--query` first.
- **Permission inheritance** — sharing a folder shares every child. `share revoke` on the child doesn't override inherited permissions — revoke on the parent instead.

---

## Quick Reference

| Task | One-liner |
|------|-----------|
| Upload xlsx → Sheet | `claw sheet upload --from r.xlsx --parent <F>` |
| Upload xlsx (keep as xlsx) | `claw sheet upload --from r.xlsx --convert off` |
| Download Sheet → xlsx | `claw sheet download <ID> --out r.xlsx --as xlsx` |
| Download Doc → PDF | `claw sheet download <ID> --out r.pdf --as pdf` |
| Share with user | `claw sheet share <ID> --user a@x --role writer --notify` |
| Public read-only | `claw sheet share <ID> --anyone --role reader` |
| List folder contents | `claw sheet list --parent <F> --format json` |
| Move to folder | `claw sheet move <ID> --to <NEW_F>` |
| Rename | `claw sheet rename <ID> --name "Q3 Final"` |
| Trash | `claw sheet delete <ID>` |
