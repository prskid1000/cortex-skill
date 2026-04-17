# `claw web` — HTTP Fetch + Content Extraction Reference

> Source directory: [scripts/claw/src/claw/web/](../../scripts/claw/src/claw/web/)

Small, composable CLI for the HTTP side of web work: fetch a URL, extract clean article text (trafilatura-style), pull tables, or enumerate links. For structured HTML scraping with selectors, chain into [`claw html`](html.md). For JavaScript-rendered sites, launch a real browser with [`claw browser`](browser.md).

Library API for escape hatches: `requests` / `httpx` for fetch, `trafilatura` for extraction. See [When `claw web` Isn't Enough](#when-claw-web-isnt-enough) for post-processing.

## Contents

- **FETCH a URL**
  - [Raw HTTP GET/POST with cookies + headers](#11-fetch)
- **EXTRACT main article content**
  - [Clean-text extraction (precision/recall presets)](#21-extract)
- **HARVEST tables**
  - [Pull `<table>` elements → CSV / XLSX](#31-table)
- **ENUMERATE links**
  - [List anchors with filters](#41-links)
- **SNAPSHOT + ARCHIVE**
  - [Save page as single-file html / warc](#51-snapshot)
- **When `claw web` isn't enough** — [escape hatches](#when-claw-web-isnt-enough)

---

## Critical Rules

1. **Safe-by-default writes** — `fetch`/`extract`/`table`/`links` write atomically to `<out>.tmp` and rename. `--force` required to overwrite an existing `--out`. Stdout output (`--out -` or no `--out`) bypasses the temp-file dance.
2. **Selectors auto-detect** — `--selector` uses XPath when it starts with `/` or `//`, otherwise CSS. Override with `--lang xpath` / `--lang css`.
3. **Structured output** — every verb supports `--json`. `links` and `table` emit NDJSON by default (one record per line) on stdout. Errors under `--json` emit `{error, code, hint, doc_url}` to stderr.
4. **Exit codes** — `0` success, `1` generic, `2` usage error, `3` partial (e.g. 2 of 3 tables extracted cleanly), `4` bad input (unreachable URL, invalid selector), `5` system error (TLS / DNS / timeout after all retries), `6` HTTP status ≥ 400 (unless `--accept-errors`), `130` SIGINT.
5. **Help** — `claw web --help`, `claw web <verb> --help`, `--examples` prints runnable recipes, `--progress=json` streams download progress for large responses.
6. **User-Agent** — default UA is `claw/1.0 (+https://github.com/...)` — a real, identifiable, well-behaved bot string. Override with `--ua STR` or set `CLAW_WEB_UA` env. Some sites 403 generic Python-requests UAs; `claw` avoids that footgun.
7. **Stdin / stdout glue** — `fetch` with `--out -` prints to stdout; `extract` / `table` / `links` accept `-` as their `<url|->` positional to read HTML from stdin. Makes pipelines trivial: `claw web fetch URL --out - | claw web extract -`.
8. **Rate limiting** — default 1 request/sec per-origin. `--rps N` raises it (use responsibly). `--sleep S` inserts a fixed delay instead.
9. **Common output flags** — every mutating verb inherits `--force`, `--backup`, `--dry-run`, `--json`, `--quiet`, `--mkdir` via the shared `@common_output_options` decorator. Individual verb blocks only call them out when the verb overrides the default; run `claw web <verb> --help` for the authoritative per-verb flag list.

---

## 1. FETCH

### 1.1 `fetch`

> Source: [scripts/claw/src/claw/web/fetch.py](../../scripts/claw/src/claw/web/fetch.py)

HTTP GET/POST with sensible defaults (redirects followed, gzip decoded, UTF-8 decoded when possible).

```
claw web fetch <url> [--out FILE|-] [--method GET|POST|PUT|DELETE|HEAD]
                     [--header K=V]... [--data @FILE|STR]
                     [--timeout SEC] [--retries N] [--retry-on 429,500-599]
                     [--follow-redirects] [--max-redirects N]
                     [--save-cookies FILE] [--load-cookies FILE]
                     [--ua STR] [--proxy URL]
                     [--accept-errors] [--json]
```

Flags:

- `--data @FILE` — read request body from file. `--data STR` — literal string. JSON bodies: pair with `--header 'Content-Type=application/json'`.
- `--save-cookies` / `--load-cookies` — Netscape-format cookie jar. Use together for multi-request sessions.
- `--retries N` — retry on 5xx and transient network errors; exponential backoff (1s, 2s, 4s...).
- `--accept-errors` — don't exit 6 on HTTP 4xx/5xx; let the body be written and the status end up in `--json` output.

Examples:

```
claw web fetch https://example.com/report.pdf --out /tmp/report.pdf
```

```
claw web fetch https://api.example.com/login \
  --method POST --header 'Content-Type=application/json' \
  --data '{"user":"a","pass":"b"}' --save-cookies /tmp/jar.txt
```

```
claw web fetch https://api.example.com/me \
  --load-cookies /tmp/jar.txt --json
```

Output (`--json`):

```json
{"url": "...", "status": 200, "final_url": "...", "headers": {...}, "body_path": "/tmp/report.pdf", "size": 12345, "elapsed_ms": 420}
```

---

## 2. EXTRACT

### 2.1 `extract`

> Source: [scripts/claw/src/claw/web/extract.py](../../scripts/claw/src/claw/web/extract.py)

Extract main article text — title, author, date, body — stripping boilerplate (nav, ads, comments). Uses trafilatura-style heuristics under the hood.

```
claw web extract <url|-> [--precision | --recall | --balanced]
                         [--include-comments] [--include-tables]
                         [--format text|md|json|xml]
                         [--out FILE|-]
```

Flags:

- `--precision` — tighter filtering; best for cleanroom text extraction but drops marginal content (side images, nested quotes). Use when you want the cleanest possible prose.
- `--recall` — permissive; keeps more content at the cost of boilerplate leak-through. Use for archiving.
- `--balanced` (default) — middle ground.
- `--format md` — markdown with headings preserved.
- `--format json` — structured `{title, author, date, description, text, url, sitename, categories, tags}`.
- `<url|->` — read HTML from stdin when `-`.

Presets, not flags: `claw` deliberately hides the 20+ trafilatura knobs. Pick one of the three presets; for finer control, use the library directly.

Examples:

```
claw web extract https://example.com/blog/post --format md --out /tmp/post.md
```

```
claw web fetch https://example.com/post --out - \
  | claw web extract - --precision --format json
```

---

## 3. TABLE

### 3.1 `table`

> Source: [scripts/claw/src/claw/web/table.py](../../scripts/claw/src/claw/web/table.py)

Pull `<table>` elements → CSV / XLSX. For one table, streams CSV. For multiple, writes an xlsx with one sheet per table.

```
claw web table <url|-> [--selector CSS|XPATH] [--index N | --all]
                       --out FILE.csv|FILE.xlsx|-
                       [--headers first-row|none] [--force] [--json]
```

Flags:

- `--selector` — narrow to a specific table (auto-detects CSS vs XPath). Default: every `<table>` on the page.
- `--index N` — extract only the N-th table (1-based). `--all` extracts every table.
- `--headers first-row` (default) — use the first row as column names. `--headers none` — generic column names.
- `--out -` — stdout CSV (only valid with `--index N` or exactly one table match).

Examples:

```
claw web table https://en.wikipedia.org/wiki/List_of_countries \
  --index 1 --out /tmp/countries.csv
```

```
claw web table https://example.com/stats --all --out /tmp/stats.xlsx
```

```
claw web fetch URL --out - | claw web table - --selector ".data-grid" --out /tmp/data.csv
```

---

## 4. LINKS

### 4.1 `links`

> Source: [scripts/claw/src/claw/web/links.py](../../scripts/claw/src/claw/web/links.py)

Enumerate anchor hrefs.

```
claw web links <url|-> [--absolute] [--filter "EXPR"]
                       [--same-origin] [--unique] [--format text|json]
                       [--out FILE|-]
```

Flags:

- `--absolute` — resolve relative URLs against the page's base URL.
- `--filter "EXPR"` — tiny expression language: `href contains 'docs'`, `text matches '^Chapter'`, `rel == 'nofollow'`. Combine with `and` / `or` / `not`.
- `--same-origin` — drop external links.
- `--unique` — de-dupe by absolute URL.
- `--format json` — NDJSON: `{href, text, rel, title, absolute_href}`.

Examples:

```
claw web links https://example.com/docs --absolute --same-origin --unique
```

```
claw web links https://example.com --filter "href contains 'pdf'" --format json
```

---

## 5. SNAPSHOT

### 5.1 `snapshot`

> Source: **NOT IMPLEMENTED** — no `web/snapshot.py` exists.

Save a page as a self-contained file (inlined CSS, images). Useful for archiving and sharing.

```
claw web snapshot <url> --out FILE [--as html|warc|mhtml]
                        [--max-size MB] [--timeout SEC]
```

Flags:

- `--as html` (default) — single-file HTML with data-URI images and inlined CSS.
- `--as warc` — Web ARChive format (for long-term archival / replay).
- `--as mhtml` — MIME HTML (Edge / Chrome format).

Note: JavaScript-rendered pages won't capture dynamic content here — use [`claw browser`](browser.md) + the Chrome DevTools MCP for that.

Example:

```
claw web snapshot https://example.com/article --out /tmp/article.html
```

---

## When `claw web` Isn't Enough

Drop into the libraries or sibling tools:

| Use case | Why `claw web` can't do it | Escape hatch |
|---|---|---|
| JavaScript-rendered pages (React / Vue SPAs) | `fetch` gets raw HTML only | [`claw browser launch`](browser.md) + Chrome DevTools MCP |
| Authenticated scraping with interactive 2FA | Cookie jar can't handle prompts | Launch browser with user profile, extract cookies post-login, hand jar to `claw web` |
| Form POST with CSRF token round-trip | `fetch` can do it, but fragile | [`requests.Session()`](https://docs.python-requests.org/en/latest/user/advanced/#session-objects) in Python |
| Structured scraping (select + normalize + deduplicate) | `extract` is one-shot; no DOM walking | [`claw html`](html.md) — selectors, mutations, sanitization |
| Rate-limited API with OAuth | No OAuth flow | `authlib` / `requests-oauthlib` |
| Streamed large download with resume | `fetch` re-downloads from scratch on retry | `curl -C -` or `wget -c` |
| Concurrent crawl of 100s of URLs | No parallelism | Python `asyncio` + `httpx.AsyncClient` |

**lxml** — see [`claw html` escape hatches](html.md#when-claw-html-isnt-enough) for lxml gotchas (post-fetch tree walks).

**BeautifulSoup4** — see [`claw html` escape hatches](html.md#when-claw-html-isnt-enough) for BS4 gotchas. `claw web extract` wraps `trafilatura`, not BS4, so raw DOM walking on the fetched HTML is a BS4 job.

## Footguns

- **Encoding guess-fail** — sites that lie about their charset (especially older Asian sites) may come back mojibake. Override with `--header 'Accept-Charset=...'` or fetch bytes (`--out file.bin`) and decode manually.
- **Aggressive `--retries`** — 5xx retries without backoff can get you IP-banned. Default backoff is exponential; don't lower unless you own the server.
- **`--follow-redirects` + login flows** — login endpoints often 302 to a `/dashboard` that requires a *different* cookie than the login page set. Use `--max-redirects 0` to inspect the intermediate response.
- **Trafilatura on login-walled pages** — `extract` doesn't know the content behind a paywall exists. Fetch first with auth, then pipe to `extract -`.
- **`--filter` expression injection** — the filter language is a tiny interpreter, not Python `eval`. It's safe but intentionally limited. For anything complex, use `links --format json | jq`.
- **Robots.txt** — `claw web` does NOT check `robots.txt` before fetching. You're responsible for respecting site policy — particularly with `--all` or loop-based scraping.

---

## Quick Reference

| Task | One-liner |
|------|-----------|
| Fetch to file | `claw web fetch URL --out page.html` |
| Fetch to stdout | `claw web fetch URL --out -` |
| POST JSON | `claw web fetch URL --method POST --header 'Content-Type=application/json' --data '{"k":"v"}'` |
| Extract article text | `claw web extract URL --format md` |
| Extract to JSON | `claw web extract URL --format json` |
| Pull first table | `claw web table URL --index 1 --out t.csv` |
| All tables → xlsx | `claw web table URL --all --out t.xlsx` |
| List links | `claw web links URL --absolute --unique` |
| Links containing "docs" | `claw web links URL --filter "href contains 'docs'"` |
| Snapshot page | `claw web snapshot URL --out article.html` |
| Pipe fetch → extract | `claw web fetch URL --out - \| claw web extract -` |
