# `claw pipeline` — YAML Pipeline DSL & Runtime

> Source directory: [scripts/claw/src/claw/pipeline/](../../scripts/claw/src/claw/pipeline/)

`claw pipeline` is a declarative multi-step recipe runner. It replaces the hand-written Python orchestration in [examples/claw-pipelines.md](../../examples/claw-pipelines.md) with a YAML DAG that any agent can emit, validate, diff, and re-run.

The substrate is intentionally small: every step is a call to another `claw <noun> <verb>` (or a `shell` / `python` escape), and the runtime adds DAG ordering, parallelism, content-addressed caching, retries, and resumable runs.

## Contents

- **AUTHOR a recipe**
  - [Purpose & position in the stack](#1-purpose) · [Recipe shape](#2-recipe-shape) · [Built-in step types](#10-built-in-step-types)
- **RUN / VALIDATE / INSPECT**
  - [Commands](#3-commands) · [DAG semantics](#4-dag-semantics) · [Parallelism](#5-parallelism) · [Debugging](#12-debugging)
- **MAKE IT RELIABLE**
  - [Caching (Nextflow-style)](#6-caching) · [Retries](#7-retries) · [Error policy](#8-error-policy) · [Secrets](#9-secrets)
- **LEARN BY EXAMPLE**
  - [Three real recipes](#11-example-recipes)

---

## Critical Rules

1. **One step = one `claw` call.** Steps should be trivially inspectable. `shell` and `python` exist as escape hatches, not as the default.
2. **Secrets never inline.** `${env:NAME}` and `${file:PATH}` are the only legal secret references; literal keys in YAML are a lint error.
3. **Caching is content-addressed, not time-based.** Never rely on mtime; rely on input-content hashes and arg normalization.
4. **`needs:` is explicit.** Implicit ordering (e.g. "step B uses `${A.out}`") still requires `needs: [A]`. The linter flags the mismatch.
5. **Topological run, but parallel when safe.** Default `--jobs` is `os.cpu_count()`; set `--jobs 1` for deterministic debugging.
6. **`--dry-run` is mandatory before `--force` writes.** Print the plan, resolve interpolation, then execute.
7. **Exit codes roll up.** Pipeline exit is `max(step exit codes)` after mapping: any step `5` → pipeline `5`; any `4` → `4`; any `3` with `continue` policy → `3`; otherwise `0`.
8. **Common output flags.** Pipeline subcommands and inner step-level `claw` invocations inherit `--force`, `--backup`, `--dry-run`, `--json`, `--quiet`, `--mkdir` via the shared `@common_output_options` decorator; run `claw pipeline <verb> --help` for the authoritative per-verb flag list.

---

## 1. Purpose

Before `claw pipeline`, the common shape was a ~200-line Python script chaining `subprocess.run(["gws", ...])`, `openpyxl.Workbook()`, `reportlab.SimpleDocTemplate(...)`, and `email.mime.*` calls — see the marquee example [DB → Styled XLSX + PDF → Drive → Gmail](../../examples/claw-pipelines.md#db-to-styled-xlsx--pdf-to-drive-to-gmail). Every such script re-implements:

- Intermediate file naming in `/tmp`
- Error handling and partial-state recovery
- Logging at each stage
- Dev-vs-prod credential switching
- Resume-from-step after a transient failure

`claw pipeline` factors all of that out. The YAML recipe becomes the only artifact; everything else is runtime.

## 2. Recipe shape

```yaml
name: daily-sales-report
description: Query DB, build styled XLSX, upload to Drive, email to team.

vars:
  outdir: ./out
  recipient: team@example.com
  region: EMEA

defaults:
  retries: 2
  backoff: exponential
  on-error: stop

steps:
  - id: fetch
    run: web.fetch
    args:
      url: https://example.com/report.xlsx
      out: "${vars.outdir}/r.xlsx"
      cache: true

  - id: extract
    run: xlsx.read
    needs: [fetch]
    args:
      path: "${fetch.out}"
      sheet: Summary
      format: json

  - id: mail
    run: email.send
    needs: [extract]
    on-error: continue
    args:
      to: "${vars.recipient}"
      subject: "Daily report — ${vars.region}"
      body-file: "${extract.stdout}"
      oauth: "${env:GMAIL_OAUTH_JSON}"
```

### Top-level keys

| Key | Required | Notes |
|-----|----------|-------|
| `name` | yes | Stable identifier; cache keys include this |
| `description` | no | Human text, surfaced by `pipeline graph` |
| `vars` | no | Static key → value map; used via `${vars.KEY}` |
| `defaults` | no | Applied to every step unless overridden |
| `steps` | yes | Ordered list (order is hint only — DAG is derived from `needs`) |

### Step fields

| Field | Required | Notes |
|-------|----------|-------|
| `id` | yes | Unique within the recipe; `[a-z0-9][a-z0-9_-]*` |
| `run` | yes | Step type — `<noun>.<verb>` or `shell` / `python` |
| `args` | depends | Matches the verb's `--json` arg schema |
| `needs` | no | List of step IDs; default `[]` (runs immediately) |
| `retries` | no | Integer ≥ 0; default `0` |
| `backoff` | no | `none \| linear \| exponential`; default `exponential` if `retries > 0` |
| `timeout` | no | Duration (`30s`, `5m`, `1h`); default none |
| `on-error` | no | `stop \| skip \| continue`; default `stop` |
| `cache` | no | `true \| false \| "inputs-only"`; default `true` for pure steps, `false` for `email.send` / `shell` |
| `when` | no | Expression: `${var} == "prod"` — step skipped if false |

## 3. Commands

### `claw pipeline run <recipe.yaml>`

> Source: [scripts/claw/src/claw/pipeline/run.py](../../scripts/claw/src/claw/pipeline/run.py)

Execute the DAG.

```
claw pipeline run recipe.yaml [--jobs N] [--resume] [--dry-run]
                              [--from STEP] [--until STEP]
                              [--var KEY=VALUE]...
                              [--progress=json] [--json]
```

| Flag | Purpose |
|------|---------|
| `--jobs N` | Max parallel steps (default `os.cpu_count()`) |
| `--resume` | Skip cache-hit steps from a previous run |
| `--dry-run` | Print topo order + resolved vars; don't execute |
| `--from STEP` | Start at `STEP`, skipping everything that doesn't lead to it (pulls dependencies forward) |
| `--until STEP` | Stop after `STEP` completes (including dependents required to compute it) |
| `--var K=V` | Override or set a `vars:` entry |

### `claw pipeline validate <recipe.yaml>`

> Source: [scripts/claw/src/claw/pipeline/validate.py](../../scripts/claw/src/claw/pipeline/validate.py)

Static checks — no execution:

- YAML + JSON Schema validation (pipeline schema published via `claw schema pipeline.recipe`)
- Per-step arg validation against `claw schema <verb>`
- DAG acyclicity
- Interpolation reference check (every `${x.y}` must resolve to a declared var or prior-step output)
- Secret lint (literal values in fields tagged `secret: true` → error)

Exit `0` on clean; exit `2` on any error. `--json` emits one error object per issue.

### `claw pipeline list-steps`

> Source: [scripts/claw/src/claw/pipeline/list_steps.py](../../scripts/claw/src/claw/pipeline/list_steps.py)

Enumerates every step type the runner understands. Output matches `run:` values exactly:

```
$ claw pipeline list-steps --json | head -5
{"run": "xlsx.new",        "claw": "claw xlsx new",        "args_schema": ".../xlsx.new.schema.json"}
{"run": "xlsx.from-csv",   "claw": "claw xlsx from-csv",   "args_schema": ".../xlsx.from-csv.schema.json"}
{"run": "xlsx.read",       "claw": "claw xlsx read",       "args_schema": ".../xlsx.read.schema.json"}
{"run": "pdf.merge",       "claw": "claw pdf merge",       "args_schema": ".../pdf.merge.schema.json"}
...
```

Generated by enumerating all registered verbs — always in sync with the binary.

### `claw pipeline graph <recipe.yaml>`

> Source: [scripts/claw/src/claw/pipeline/graph.py](../../scripts/claw/src/claw/pipeline/graph.py)

Visualize the DAG:

```
claw pipeline graph recipe.yaml --format dot      # Graphviz .dot
claw pipeline graph recipe.yaml --format mermaid  # fenced mermaid block
claw pipeline graph recipe.yaml --format ascii    # default: UTF-8 box drawing
```

ASCII output example:

```
fetch ─┐
       ├─► extract ──► mail
build ─┘
```

## 4. DAG semantics

- **`needs:`** is the only way to declare ordering. Steps with empty `needs` run in the first wave.
- **Interpolation syntax** (Python `string.Template` style, `$` must be escaped as `$$`):
  - `${vars.KEY}` — from top-level `vars:`
  - `${STEP_ID.FIELD}` — a prior step's output record (common fields: `out`, `path`, `stdout`, `count`)
  - `${env:NAME}` — environment variable (error if unset)
  - `${env:NAME:-default}` — environment variable with default
  - `${file:PATH}` — read file contents (`~` expanded)
- **Cycles** are rejected at `validate` time.
- **Orphan references** (`${missing.out}`) fail `validate`.
- **Output surface** — each `run:` verb's `--json` record is the step's output, addressable by field name in downstream `${ID.FIELD}` interpolations. Schema is `claw schema <verb>`.

## 5. Parallelism

- The runner is a `ThreadPoolExecutor(max_workers=--jobs)` driving an eager-scheduled DAG: as soon as a step's `needs` are all satisfied, it's submitted.
- CPU-bound work inside Python verbs (e.g. large `xlsx.from-csv`) still benefits because the heavy lifting happens in C extensions (`openpyxl`'s `lxml`, `Pillow`, etc.) that release the GIL.
- Step types that spawn subprocess (`ffmpeg`, `pandoc`, `magick`) get linear scaling with `--jobs`.
- `--jobs 1` forces serial for deterministic debugging and log readability.
- The runner never cancels a running step — on `stop` error policy, it finishes the in-flight step and then halts dispatch.

## 6. Caching

Nextflow-style, content-addressed. No mtime, no `--newer-than`.

Per step, the cache key is:

```
SHA256( step.run
      | canonical_json(step.args with ${...} resolved)
      | sorted list of (input_path, sha256_of_contents)
      | claw_version
      | recipe_name )
```

- **Location**: `$XDG_CACHE_HOME/claw/pipeline/<key-prefix>/<key>/`
  - `out/` — captured output files
  - `record.json` — the step's `--json` output record
  - `meta.json` — cache key inputs, duration, exit code
- **`--resume`** consults this cache; on hit, the step is skipped, `record.json` is loaded into the interpolation context, and `out/` is symlinked (or copied on Windows) to the declared output path.
- **Input hashing** streams the file — no memory blow-up on multi-GB inputs.
- **`cache: false`** disables caching for a specific step (required for side-effectful steps like `email.send`, `shell` with network calls).
- **Cache invalidation** happens automatically whenever any input hash, arg, or `claw` version changes. No manual bust needed; `claw cache clear` exists for the rare emergency.

## 7. Retries

```yaml
- id: fetch
  run: web.fetch
  retries: 3
  backoff: exponential        # 1s, 2s, 4s (capped at 30s)
  timeout: 30s
  args: { url: https://flaky.example.com/data }
```

- `backoff: none` — immediate retry
- `backoff: linear` — `1s, 2s, 3s, ...`
- `backoff: exponential` — `1s, 2s, 4s, 8s, ... (cap 30s)`
- Retries apply to exit codes `4` and `5` by default; exit `2` (usage) never retries.
- `retry-on: [4, 5, 130]` can override.

## 8. Error policy

Per step:

| `on-error` | Effect |
|------------|--------|
| `stop` (default) | Fail the pipeline; already-running steps finish; pipeline exit = step exit |
| `skip` | Mark dependents as unreachable; pipeline continues; pipeline exit ≥ `3` |
| `continue` | Ignore this step's failure; downstream steps treat its outputs as empty strings; pipeline exit ≥ `3` |

A global `defaults.on-error` applies to every step unless overridden.

## 9. Secrets

- Never write resolved secret values to logs (`-vvv` masks them with `***`).
- Never include them in cache keys as cleartext (only their SHA-256 hash participates in the key).
- Never include them in `--dry-run` output (shown as `<secret:ENV_NAME>`).
- `claw pipeline validate` flags any field whose schema is tagged `secret: true` if it contains a literal string rather than `${env:...}` / `${file:...}`.

Example:

```yaml
- id: mail
  run: email.send
  args:
    to: "${vars.recipient}"
    oauth: "${env:GMAIL_OAUTH_JSON}"   # OK
    # oauth: "/home/me/secret.json"    # validate error: literal secret path
```

## 10. Built-in step types

Every `claw <noun> <verb>` is a step type. The table below lists the common ones; full enumeration via `claw pipeline list-steps`.

| `run:` | Equivalent CLI | Notes |
|--------|----------------|-------|
| `xlsx.new` | `claw xlsx new` | Blank workbook |
| `xlsx.from-csv` | `claw xlsx from-csv` | CSV → XLSX |
| `xlsx.from-json` | `claw xlsx from-json` | JSON → XLSX |
| `xlsx.read` | `claw xlsx read` | XLSX → JSON rows |
| `xlsx.style` | `claw xlsx style` | Apply header / banded styles |
| `xlsx.chart` | `claw xlsx chart` | Inject bar/line/pie chart |
| `docx.new` | `claw docx new` | Document from template |
| `docx.fill` | `claw docx fill` | Mustache-style placeholder fill |
| `pptx.from-deck` | `claw pptx from-deck` | Slide generation from a data file |
| `pdf.merge` | `claw pdf merge` | Concatenate PDFs |
| `pdf.split` | `claw pdf split` | Split by page range |
| `pdf.extract-tables` | `claw pdf extract-tables` | pdfplumber-backed |
| `pdf.render` | `claw pdf render` | PDF → PNG/JPEG pages |
| `img.resize` | `claw img resize` | Pillow/ImageMagick |
| `img.watermark` | `claw img watermark` | Text or image overlay |
| `media.transcode` | `claw media transcode` | ffmpeg format/codec change |
| `media.trim` | `claw media trim` | ffmpeg trim by timestamp |
| `media.concat` | `claw media concat` | ffmpeg concat demuxer |
| `convert.any` | `claw convert any` | Pandoc any ↔ any |
| `email.send` | `claw email send` | Gmail (via `gws`) or SMTP |
| `doc.create` | `claw doc create` | Google Doc |
| `sheet.upload` | `claw sheet upload` | Upload XLSX/CSV as Google Sheet |
| `sheet.read` | `claw sheet read` | Google Sheet → JSON |
| `web.fetch` | `claw web fetch` | HTTP GET with retry, cache |
| `html.extract` | `claw html extract` | CSS selector or XPath |
| `xml.xpath` | `claw xml xpath` | lxml XPath query |
| `browser.screenshot` | `claw browser screenshot` | Headless page capture |
| **`shell`** | — | Raw command; escape hatch |
| **`python`** | — | Inline Python; discouraged |

### `shell` step contract

```yaml
- id: compress
  run: shell
  needs: [build]
  args:
    cmd: ["zip", "-r", "${vars.outdir}/bundle.zip", "${build.out}"]
    stdin: ""                       # optional; string piped to stdin
    cwd: "${vars.outdir}"           # optional
    env:                            # optional; merged over parent env
      LOG_LEVEL: info
    capture: [stdout, stderr]       # default: stdout only
```

Output record: `{exit_code, stdout, stderr, duration_ms}`. Non-zero `exit_code` is treated like any other step failure (respects `on-error`, `retries`). `cmd` must be an argv list — shell-string form is not supported (no implicit shell injection).

### `python` step contract (discouraged)

```yaml
- id: compute
  run: python
  needs: [read]
  args:
    code: |
      import json, sys
      rows = json.loads(sys.stdin.read())
      total = sum(r["revenue"] for r in rows)
      print(json.dumps({"total": total}))
    stdin: "${read.stdout}"
```

Runs in a subprocess with a clean environment; stdout is the step's `stdout` output field. Prefer promoting recurring snippets to a real `claw` verb.

## 11. Example recipes

### 11.1 DB → styled XLSX → Drive → Gmail

Replaces [examples/claw-pipelines.md § DB → Styled XLSX + PDF → Drive → Gmail](../../examples/claw-pipelines.md#db-to-styled-xlsx--pdf-to-drive-to-gmail).

```yaml
name: regional-sales-report
vars:
  outdir: /tmp
  recipient: manager@company.com
  cc: team@company.com

steps:
  - id: query
    run: shell
    args:
      cmd: ["claw", "mysql", "query",
            "--host", "${env:DB_HOST}",
            "--db", "sales",
            "--sql-file", "queries/regional.sql",
            "--format", "json",
            "--out", "${vars.outdir}/raw.json"]

  - id: build-xlsx
    run: xlsx.from-json
    needs: [query]
    args:
      data: "${vars.outdir}/raw.json"
      out: "${vars.outdir}/regional_sales.xlsx"
      sheet: "Regional Sales"
      types: infer
      style: corporate
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
      subject: "Regional Sales Report — Q1–Q4"
      body: |
        Attached is the regional sales report covering Q1 through Q4.
        Both Excel (with charts) and PDF are attached; files are also on Drive.
      attachments:
        - "${build-xlsx.out}"
        - "${build-pdf.out}"
      oauth: "${env:GMAIL_OAUTH_JSON}"
```

### 11.2 CSV → Google Sheet

Replaces [examples/claw-pipelines.md § CSV → Styled XLSX → Google Sheet](../../examples/claw-pipelines.md#csv-to-styled-xlsx-to-google-sheet).

```yaml
name: csv-to-sheet
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

  - id: upload
    run: sheet.upload
    needs: [build]
    args:
      path: "${build.out}"
      name: "Sales Data Import"
      convert: true             # XLSX → native Google Sheet
      share:
        type: anyone
        role: reader
```

### 11.3 PDF tables → multi-sheet XLSX → PDF summary

Replaces [examples/claw-pipelines.md § PDF Tables → Multi-Sheet XLSX → PDF Summary](../../examples/claw-pipelines.md#pdf-tables-to-multi-sheet-xlsx-to-pdf-summary).

```yaml
name: pdf-tables-roundtrip
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
      layout: landscape
```

## 12. Debugging

- **`--dry-run`** — prints topo order, resolved vars, resolved interpolations, and the concrete `claw ...` command for every step. Exits `0` without executing.

  ```
  $ claw pipeline run recipe.yaml --dry-run
  [plan]
    wave 1: query
    wave 2: build-xlsx, build-pdf
    wave 3: upload-xlsx, upload-pdf
    wave 4: mail
  [vars] outdir=/tmp recipient=manager@company.com cc=team@company.com
  [step query] claw mysql query --host db.internal --db sales ...
  ```

- **`--from STEP` / `--until STEP`** — partial runs. `--from` re-runs STEP (and anything that depends on it that comes later); `--until` stops at STEP after completing it. They compose: `--from build-xlsx --until upload-pdf`.

- **`--progress=json`** — NDJSON event stream on stderr. Each event: `{ts, step, stage, pct, msg}`, where `stage` ∈ `queued / running / ok / err / skip / cache-hit`. Agents should parse this stream to render progress bars.

- **`-vv` / `-vvv`** — log every subprocess invocation, every cache probe, every interpolation resolution. Secrets stay masked.

- **`claw pipeline validate recipe.yaml --json`** — before running, always validate. Emits one error object per issue with `{path, rule, message, hint}` so CI can annotate.

---

## Quick Reference

| Task | Command |
|------|---------|
| Run a recipe | `claw pipeline run recipe.yaml` |
| Dry run with plan | `claw pipeline run recipe.yaml --dry-run` |
| Resume after failure | `claw pipeline run recipe.yaml --resume` |
| Re-run from step | `claw pipeline run recipe.yaml --from build-xlsx` |
| Stop at step | `claw pipeline run recipe.yaml --until upload-xlsx` |
| Set / override var | `claw pipeline run recipe.yaml --var region=APAC` |
| Validate only | `claw pipeline validate recipe.yaml` |
| List step types | `claw pipeline list-steps` |
| Visualize DAG | `claw pipeline graph recipe.yaml --format mermaid` |
| Progress stream | `claw pipeline run recipe.yaml --progress=json 2>events.ndjson` |
| Clear cache for recipe | `claw cache clear --recipe regional-sales-report` |
