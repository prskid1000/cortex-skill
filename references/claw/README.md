# `claw` — CLI Reference (Overview)

`claw` is a single CLI that absorbs the glue around `openpyxl`, `fitz` / `PyMuPDF`, `Pillow`, `reportlab`, `pdfplumber`, `lxml`, `BeautifulSoup4`, `pypdf`, `python-docx`, `python-pptx`, `ffmpeg`, `magick`, `pandoc`, `gws`, `clickup`, and the rest of the claude-claw stack. Each verb wraps a task that is ≥ 5 Python lines or a multi-step shell pipeline; anything smaller is better expressed directly against the underlying library, and `claw` will happily point you there.

The CLI is a thin adapter. It does not reinvent any library and it does not hide any capability — every noun has a documented escape hatch that links back to the canonical library reference under `references/`.

## Contents

- **GET STARTED**
  - [What `claw` is and isn't](#1-what-claw-is) · [Install](#2-install) · [Command surface map](#3-command-surface-map)
- **INVOKE / DISCOVER**
  - [Global flags](#4-global-flags) · [Help UX](#5-help-ux) · [Exit codes](#6-exit-codes)
- **WRITE / OUTPUT CONTRACT**
  - [Safe-write contract](#7-safe-write-contract) · [Structured output (`--json`)](#8-structured-output-contract)
- **EXTEND & CONFIGURE**
  - [Plugin model](#9-plugin-model) · [Config precedence](#10-config-precedence) · [Cache directory](#11-caching)
- **WHEN CLAW ISN'T ENOUGH**
  - [Escape hatches per noun](#12-when-claw-isnt-enough)

---

## Critical Rules

1. **`claw` wraps; it does not hide.** Every verb maps to a short, inspectable Python or subprocess call. Verbs that would need custom invention (e.g. app-context detection, wake words) don't exist — use the library directly.
2. **Never silent-overwrite.** All writes are temp-file + atomic rename; `--force` is required to clobber any existing `--out` path; `--backup` drops a `*.bak` sidecar.
3. **`--json` flips the whole output to NDJSON.** Success records and errors both go to stdout/stderr as JSON — mixing text and JSON in the same stream is a bug.
4. **Errors surface with a hint and a doc URL.** Under `--json` every error emits `{error, code, hint, doc_url}` on stderr; under human mode the same fields render as a short block.
5. **Exit codes are load-bearing.** Agents branch on `0 / 2 / 3 / 4 / 5`; never collapse them into `1`.
6. **Config precedence is fixed.** CLI flag → `CLAW_*` env → `./claw.toml` → `~/.config/claw/config.toml`. Surprises here break pipelines.
7. **Cache is content-addressed and side-effect-free.** `claw cache clear` is always safe. Never store secrets in the cache.

---

## 1. What `claw` is

- A thin CLI over proven libraries. The "good code" still lives in `openpyxl`, `fitz`, `Pillow`, etc. — `claw` just removes the 10-line boilerplate for common tasks and gives them a consistent surface (flags, exit codes, JSON).
- A pipeline substrate. `claw pipeline run recipe.yaml` replaces the hand-written Python orchestration in [examples/claw-pipelines.md](../../examples/claw-pipelines.md) with declarative YAML — see [references/claw/pipeline.md](pipeline.md).
- **Not** a generic scripting runtime. If your task is one Python call, just write it. If it's five calls with intermediate files, `claw` is worth it.
- **Not** an auth broker. `gws auth` stays the source of truth for Google; `clickup auth` for ClickUp; Gmail OAuth JSON for SMTP fallback. `claw doctor` verifies these.

## 2. Install

```bash
# Preferred (isolated venv, shares with uv toolchain)
uv tool install claw

# pipx (same model, separate tool dir)
pipx install claw

# Unprefixed pip (not recommended outside venvs)
pip install claw
```

Installed entry point (from `pyproject.toml`):

```toml
[project.scripts]
claw = "claw.cli:main"
```

Verify:

```bash
claw --version
claw doctor
```

`claw doctor` prints external-dep status and should run clean before any pipeline. See [references/claw/doctor.md](doctor.md).

## 3. Command surface map

Nouns live under the single `claw` binary. Each has its own reference file in this directory.

| Noun | Purpose | Reference |
|------|---------|-----------|
| `xlsx` | Excel workbooks — create, read, style, chart, validate | [claw/xlsx.md](xlsx.md) |
| `docx` | Word documents — paragraphs, tables, headers, styles | [claw/docx.md](docx.md) |
| `pptx` | PowerPoint decks — slides, shapes, layouts, charts | [claw/pptx.md](pptx.md) |
| `pdf` | PDF read / edit / merge / split / annotate / redact | [claw/pdf.md](pdf.md) |
| `img` | Raster image ops via Pillow + ImageMagick | [claw/img.md](img.md) |
| `media` | Video / audio via `ffmpeg` (encode, trim, concat, extract) | [claw/media.md](media.md) |
| `convert` | Format-to-format via Pandoc + fallbacks | [claw/convert.md](convert.md) |
| `email` | Compose + send MIME; Gmail via `gws` or OAuth2 | [claw/email.md](email.md) |
| `doc` | Google Docs — create, insert, export (wraps `gws docs`) | [claw/doc.md](doc.md) |
| `drive` | Google Drive — upload/download, list, move, copy, rename, delete, share (wraps `gws drive`) | [claw/drive.md](drive.md) |
| `web` | HTTP fetch with retry, content-type sniff, cookie jars | [claw/web.md](web.md) |
| `html` | HTML parse / query / scrape via lxml + BS4 | [claw/html.md](html.md) |
| `xml` | XML parse / XPath / XSLT / validate via lxml | [claw/xml.md](xml.md) |
| `browser` | Headless browser ops via Chrome DevTools MCP | [claw/browser.md](browser.md) |
| `pipeline` | YAML DSL recipe runner (parallel DAG, cache, resume) | [claw/pipeline.md](pipeline.md) |
| `doctor` | Environment diagnostics + optional auto-fix | [claw/doctor.md](doctor.md) |
| `completion` | Emit shell completion scripts (bash / zsh / fish / pwsh) | [claw/completion.md](completion.md) |

Utility subcommands that don't need their own noun:

| Command | Purpose |
|---------|---------|
| `claw schema <verb>` | Print the JSON Schema for a verb's `--json` output |
| `claw cache clear [--older-than 7d]` | Wipe `$XDG_CACHE_HOME/claw/` |
| `claw help <cmd>` | Alias for `claw <cmd> --help` |

## 4. Global flags

Every verb accepts the following:

| Flag | Purpose |
|------|---------|
| `--help`, `-h` | Print help for the current scope (root / noun / verb) |
| `--json` | Emit NDJSON on stdout; errors as JSON on stderr |
| `--progress=json` | Emit NDJSON `{stage, pct, msg}` progress events on stderr |
| `--quiet`, `-q` | Suppress progress/info; errors still print |
| `-v`, `-vv`, `-vvv` | Verbosity: `WARN` / `INFO` / `DEBUG` / `TRACE` on stderr |
| `--force` | Allow overwrite of existing `--out` paths |
| `--backup` | Drop a `<out>.bak` sidecar before atomic rename |
| `--dry-run` | Print the plan (files read, files written, commands spawned) and exit 0 |
| `--stream` | Enable streaming / memory-bounded mode where the verb supports it |
| `--mkdir` | Auto-create the parent directory of `--out` |
| `--color auto\|always\|never` | Force TTY color; default `auto` |
| `--version` | Print `claw` + bundled library versions and exit |

Flags are additive — `--json --progress=json -vv` is a valid combination (one stdout stream, two stderr streams).

## 5. Help UX

`claw` uses a git-style three-level help model.

| Invocation | Prints |
|------------|--------|
| `claw` or `claw --help` | Nouns table (see [section 3](#3-command-surface-map)) + global flags |
| `claw <noun> --help` | List of verbs under that noun + noun-level flags |
| `claw <noun> <verb> --help` | Full flags, positional args, examples, exit codes |
| `claw help <cmd>` | Alias for `claw <cmd> --help` (git parity) |
| `claw --help-all` | Full tree dump — every noun, every verb, every flag |
| `claw <cmd> --examples` | Standalone examples page; auto-pipes to `$PAGER` (default `less -R`) |
| `claw schema <verb>` | JSON Schema for `--json` output of that verb |

**Did-you-mean suggestions.** On unknown command, `claw` prints up to 3 nearest matches by Damerau-Levenshtein distance:

```
$ claw xlxs new out.xlsx
error: unknown noun 'xlxs'
did you mean: xlsx, xml, pdf?
```

**Man pages.** `claw` installs one man page per verb at `$prefix/share/man/man1/claw-<noun>-<verb>.1` (e.g. `claw-xlsx-new.1`) plus a top-level `claw.1`. `man claw-xlsx-new` works after install.

## 6. Exit codes

| Code | Meaning | When |
|------|---------|------|
| `0` | Success | All requested work completed |
| `1` | Generic error | Uncategorised failure (rare — prefer 4 or 5) |
| `2` | Usage error | Bad flag, missing required arg, schema violation |
| `3` | Partial success | Multi-item op where ≥ 1 item succeeded and ≥ 1 skipped/failed (e.g. 3 of 5 PDFs merged) |
| `4` | Input / remote error | File not found, 4xx HTTP, bad input format |
| `5` | Server / system error | 5xx HTTP, OOM, disk full, missing external binary |
| `130` | SIGINT | User pressed Ctrl-C; partial output cleaned up |

Agents branching on these codes should treat `3` as "retry-not-helpful, inspect the report" and `5` as "retry-with-backoff-may-help".

## 7. Safe-write contract

Every verb that produces a file follows the same write protocol:

1. Compute `<out>`. If it exists and caller did not pass `--force`, fail with exit `2` and the hint `pass --force to overwrite`.
2. If `--backup` and `<out>` exists, copy `<out>` → `<out>.bak` (preserving mtime).
3. Write to `<out>.tmp-<pid>` in the same directory as `<out>`.
4. `fsync()` the temp file.
5. `os.replace(<tmp>, <out>)` — atomic on both NTFS and ext4.
6. On any error between (3) and (5), delete the temp file; `<out>` is untouched.

`--mkdir` is the **only** way `claw` auto-creates parent directories. Without it, writing to `./reports/q4/report.xlsx` when `./reports/q4/` does not exist fails with exit `4`.

Writes to stdout (no `--out`) are unbuffered and flushed on each logical record.

## 8. Structured output contract

`--json` puts the verb into machine mode:

- **stdout** — NDJSON, one JSON object per logical record (one per row, one per file, etc.). No text, no banners, no progress.
- **stderr** — logs (respecting `-v` level) and, on failure, one JSON error object:

```json
{"error": "file not found", "code": "INPUT_MISSING", "hint": "check the path", "doc_url": "https://claw.dev/errors/INPUT_MISSING"}
```

- Schema discovery — `claw schema <verb>` prints the JSON Schema (Draft 2020-12) for the `--json` success record. Pipeline validators consume this.
- `--progress=json` is orthogonal to `--json`: progress events go to stderr as NDJSON `{stage, pct, msg, ts}` regardless of stdout mode.

## 9. Plugin model

Third-party subcommands register via `entry_points`:

```toml
[project.entry-points."claw.commands"]
my-noun = "my_claw_plugin.cli:register"
```

`register(parser)` receives the root subparser; plugins add their noun + verbs. `claw --help` lists plugin nouns separately at the bottom. `claw doctor --plugins` verifies each plugin imports cleanly.

Plugins inherit all global flags (including `--json`, `--progress=json`) via the shared `claw.cli.Context`. Plugins that don't honor the safe-write and JSON contracts are not considered conformant.

## 10. Config precedence

Resolution order (highest wins):

1. CLI flag (`--lmstudio-url https://...`)
2. Env var (`CLAW_LMSTUDIO_URL=...`) — namespace is `CLAW_<NOUN>_<KEY>` for per-noun and `CLAW_<KEY>` for global
3. Project config `./claw.toml` (walks up from CWD to the first match)
4. User config `~/.config/claw/config.toml` (`%APPDATA%\claw\config.toml` on Windows)

Example `claw.toml`:

```toml
[defaults]
force = false
backup = true

[email]
from = "ops@example.com"
oauth = "~/.claw/gmail-oauth.json"

[web]
user_agent = "claw/1.0 (+https://example.com)"
timeout_sec = 30
```

`claw config show [--json]` prints the fully resolved config with source annotations. `claw config path` prints the config paths in precedence order.

## 11. Caching

- Location: `$XDG_CACHE_HOME/claw/` (Linux/macOS), `%LOCALAPPDATA%\claw\cache\` (Windows).
- Content-addressed — keys are SHA-256 of `(verb, normalized-args, input-content-hashes)`.
- Used by `claw pipeline run --resume`, `claw web fetch` (when `--cache`), and model-call caching in any LLM-adjacent verb.
- `claw cache clear` — remove everything.
- `claw cache clear --older-than 7d` — remove entries with `mtime < now - 7d`.
- `claw cache stats` — size, entry count, top 10 largest.

Cache entries never contain secrets; interpolation results that resolve `${env:...}` / `${file:...}` are rehashed with the resolved value **but the resolved value is not stored** — only its hash.

## 12. When `claw` isn't enough

`claw` covers the 80%. The remaining 20% is where you want full library access. Each noun's reference ends with a `When claw <noun> isn't enough` section listing the relevant libraries, `pip install` command, canonical docs URL, and the non-obvious gotchas you'll actually hit:

| Noun | Libraries to drop to |
|------|----------------------|
| `xlsx` | [openpyxl](xlsx.md#when-claw-xlsx-isnt-enough) |
| `docx` | [python-docx](docx.md#when-claw-docx-isnt-enough) |
| `pptx` | [python-pptx](pptx.md#when-claw-pptx-isnt-enough) |
| `pdf` | [PyMuPDF / pypdf / pdfplumber / reportlab](pdf.md#when-claw-pdf-isnt-enough) |
| `img` | [Pillow / ImageMagick](img.md#when-claw-img-isnt-enough) |
| `media` | [ffmpeg / ffprobe](media.md#when-claw-media-isnt-enough) |
| `convert` | [pandoc](convert.md#when-claw-convert-isnt-enough) |
| `email` | [Python `email.mime` + gws gmail](email.md#when-claw-email-isnt-enough) |
| `doc` / `drive` | [references/gws-cli.md](../gws-cli.md) (all `gws` verbs + params) |
| `html` | [BeautifulSoup4 / lxml.html / trafilatura](html.md#when-claw-html-isnt-enough) |
| `xml` | [lxml](xml.md#when-claw-xml-isnt-enough) |
| `web` | [requests / httpx / trafilatura](web.md#when-claw-web-isnt-enough) |
| `browser` | [references/claw/browser.md § escape hatch](browser.md#escape-hatch--manual-browser-launch) |

The rule: if the library has a feature and `claw` doesn't, that's a known gap — drop to the library, don't file a bug.

---

## Quick Reference

| Task | Command |
|------|---------|
| List nouns | `claw --help` |
| Verbs under a noun | `claw xlsx --help` |
| Full flags for a verb | `claw xlsx new --help` |
| Examples for a verb | `claw xlsx new --examples` |
| Dump full CLI tree | `claw --help-all` |
| JSON schema of output | `claw schema xlsx.read` |
| Environment check | `claw doctor` |
| Run a pipeline | `claw pipeline run recipe.yaml` |
| Install shell completion | `claw completion bash > /etc/bash_completion.d/claw` |
| Clear cache | `claw cache clear` |
| Show effective config | `claw config show --json` |
