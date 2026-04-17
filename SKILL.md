---
name: claude-claw
description: >
  Reference guide for documents, spreadsheets, presentations, PDFs, images, video, audio,
  Google Workspace, ClickUp, MySQL, and media processing.
---

# Claude Claw — Productivity OS

- [Bootstrap](#bootstrap) · [Workflow](#workflow) · [Decision-Tree List Format](#decision-tree-list-format) · [Templates & Extension Guides](#templates--extension-guides) · [Scripts](#scripts)

## Bootstrap

```bash
python ~/.claude/skills/claude-claw/scripts/healthcheck.py
```

## Workflow

`Source -> Transform (Python) -> Output (/tmp/) -> Deliver (gws)`

## Decision-Tree List Format

Every index / TOC in this skill (the File Map below, plus each reference's and example's Contents list) uses the same decision-tree shape. Apply it to any markdown file that indexes capability by user task.

- Top level: `- **VERB …**` — the *user's intent* in bold caps (CREATE, READ, EDIT, CONVERT, PATCH, SEND, QUERY, …). New tools go under an existing verb when possible; add a new verb only for a genuinely new task category.
- Second level: one option per line, ` — ` separator before the backticked package/binary.
- Third level — choose one shape per node, don't mix:
  - **Expanded** — `- Ref:` + `- Ex:` sub-bullets, one anchor per line (use for options with many subsections).
  - **Compact** — a single line of `·`-separated anchor links (use for dense sub-capabilities where a full nested list would dominate the page).
- Anchors: lowercase kebab-case, strip punctuation, spaces → hyphens. Link labels restate section purpose in 3–8 words — don't just repeat the heading.
- Never force the tree onto code blocks, tables, or API detail — only onto index lists.
- Broken anchors silently degrade retrieval; treat them as build-breaks.

Copy [references/_TEMPLATE.md](references/_TEMPLATE.md) or [examples/_TEMPLATE.md](examples/_TEMPLATE.md) for a pre-filled shape. For adding or improving `claw` commands, follow the agent checklist in [references/claw/contributing.md](references/claw/contributing.md).

_Primary entry point: the **`claw`** CLI. Library-level references are escape hatches. See [references/claw/README.md](references/claw/README.md) for install, global flags, help UX, exit codes, and plugin model._


## CREATE a document

- Excel (.xlsx) — `claw xlsx` · [src](scripts/claw/src/claw/xlsx/)
  - Ref: [claw xlsx](references/claw/xlsx.md) — `new`, `from-csv`, `from-json`, `from-html`, `from-pdf`, `append`, `style`, `chart`, `table`, `validate`, `protect`, `richtext`, `freeze`, `filter`, `conditional`, `meta`
  - Escape hatch: [openpyxl](references/claw/xlsx.md#when-claw-xlsx-isnt-enough) — custom chart construction, overlapping conditional-formatting rule stacks, VBA preservation, pivot-table read, worksheet-scoped styles
  - Ex: [recipes — xlsx](examples/claw-recipes.md)
- Word (.docx) — `claw docx` · [src](scripts/claw/src/claw/docx/)
  - Ref: [claw docx](references/claw/docx.md) — `new`, `from-md`, `add-heading|paragraph|table|image`, `header`, `footer`, `toc`, `style`, `section`, `comments`, `custom-xml`
  - Escape hatch: [python-docx](references/claw/docx.md#when-claw-docx-isnt-enough) — SmartArt, embedded Excel/chart objects, numbering.xml, track-changes write
  - Ex: [recipes — docx](examples/claw-recipes.md)
- PowerPoint (.pptx) — `claw pptx` · [src](scripts/claw/src/claw/pptx/)
  - Ref: [claw pptx](references/claw/pptx.md) — `new`, `add-slide`, `add-chart`, `add-table`, `add-image`, `brand`, `chart refresh`, `notes`, `reorder`
  - Escape hatch: [python-pptx](references/claw/pptx.md#when-claw-pptx-isnt-enough) — KPI dashboards, animations, SmartArt, master-slide construction
  - Ex: [recipes — pptx](examples/claw-recipes.md)
- PDF from scratch — `claw pdf from-html|from-md|qr|barcode` · [src](scripts/claw/src/claw/pdf/)
  - Ref: [claw pdf § CREATE](references/claw/pdf.md)
  - Escape hatch: [reportlab / PyMuPDF / pypdf / pdfplumber](references/claw/pdf.md#when-claw-pdf-isnt-enough) — freeform Canvas drawing, custom NumberedCanvas, AcroForm authoring, custom Flowables
- Google Doc — `claw doc` · [src](scripts/claw/src/claw/doc/)
  - Ref: [claw doc](references/claw/doc.md) — `create`, `build` (markdown → chunked batchUpdate), `read`, `export`
  - Escape hatch: [gws docs commands](references/gws-cli.md#docs)
- Google Sheet / Drive upload — `claw sheet` · [src](scripts/claw/src/claw/sheet/)
  - Ref: [claw sheet](references/claw/sheet.md) — `upload --convert`, `download`, `share`, `list`, `move`, `copy`, `rename`, `delete`
  - Escape hatch: [gws sheets / drive commands](references/gws-cli.md#sheets)


## READ / EXTRACT

- PDF → text — `claw pdf extract-text [--mode plain|blocks|dict|html]` · [src](scripts/claw/src/claw/pdf/extract_text.py)
  - Ref: [claw pdf § READ](references/claw/pdf.md) · [OCR](references/claw/pdf.md)
  - Escape hatch: [PyMuPDF / pdfplumber](references/claw/pdf.md#when-claw-pdf-isnt-enough)
- PDF → tables — `claw pdf extract-tables [--strategy text --vlines …]` · [src](scripts/claw/src/claw/pdf/extract_tables.py)
  - Ref: [claw pdf § extract-tables](references/claw/pdf.md)
  - Escape hatch: [pdfplumber](references/claw/pdf.md#when-claw-pdf-isnt-enough)
- PDF → images — `claw pdf extract-images | render` · [src](scripts/claw/src/claw/pdf/)
  - Escape hatch: [PyMuPDF](references/claw/pdf.md#when-claw-pdf-isnt-enough)
- Excel → data — `claw xlsx read | sql | stat | to-csv` · [src](scripts/claw/src/claw/xlsx/)
- HTML — `claw html select | text | strip | sanitize | absolutize | rewrite` · [src](scripts/claw/src/claw/html/)
  - Ref: [claw html](references/claw/html.md)
  - Escape hatch: [BeautifulSoup4 / lxml.html / trafilatura](references/claw/html.md#when-claw-html-isnt-enough)
- XML — `claw xml xpath | xslt | validate | canonicalize | stream-xpath | to-json` · [src](scripts/claw/src/claw/xml/)
  - Ref: [claw xml](references/claw/xml.md)
  - Escape hatch: [lxml](references/claw/xml.md#when-claw-xml-isnt-enough) — XSLT params, Schematron, custom element classes, resolver registration
- Web page → article — `claw web fetch | extract | table | links | snapshot` · [src](scripts/claw/src/claw/web/)
  - Ref: [claw web](references/claw/web.md)
- Email — `claw email search | download-attachment` · [src](scripts/claw/src/claw/email/)


## EDIT

- PDF annotate / redact / watermark — `claw pdf annotate|redact|watermark|stamp|flatten` · [src](scripts/claw/src/claw/pdf/)
  - Ref: [claw pdf § STAMP / SECURE / ANNOTATE](references/claw/pdf.md)
  - Escape hatch: [PyMuPDF](references/claw/pdf.md#when-claw-pdf-isnt-enough)
- PDF merge / split / rotate / crop — `claw pdf merge|split|rotate|crop` · [src](scripts/claw/src/claw/pdf/)
  - Escape hatch: [pypdf](references/claw/pdf.md#when-claw-pdf-isnt-enough)
- Excel / Word / PPT — same `claw xlsx|docx|pptx` nouns (CREATE verbs also edit in place) · [xlsx src](scripts/claw/src/claw/xlsx/) · [docx src](scripts/claw/src/claw/docx/) · [pptx src](scripts/claw/src/claw/pptx/)
- Image — `claw img crop | resize | composite | exif | rename | batch` · [src](scripts/claw/src/claw/img/)
  - Ref: [claw img](references/claw/img.md)
- HTML tree — `claw html unwrap | wrap | replace` · [src](scripts/claw/src/claw/html/)
- XML — `claw xml fmt` (pretty-print) · [src](scripts/claw/src/claw/xml/fmt.py) · [canonicalize](references/claw/xml.md)


## CONVERT format — `claw convert` · [src](scripts/claw/src/claw/convert/)

- Any ↔ Any (Markdown, Word, PDF, HTML, EPUB, Slides, LaTeX, …) — `claw convert <in> <out> [--toc --template F --ref-doc F --css F --engine xelatex|weasyprint|typst]` · [src](scripts/claw/src/claw/convert/convert.py)
  - Ref: [claw convert](references/claw/convert.md)
  - Escape hatch: [pandoc](references/claw/convert.md#when-claw-convert-isnt-enough) — custom Lua filters, Defaults YAML beyond passthrough
  - Ex: [recipes — convert](examples/claw-recipes.md)
- PDF without LaTeX — `claw convert md2pdf-nolatex` (pandoc → HTML → PyMuPDF Story) · [src](scripts/claw/src/claw/convert/md2pdf_nolatex.py)
- Multi-chapter book — `claw convert book <chapters…> [--csl FILE --bib FILE]` · [src](scripts/claw/src/claw/convert/book.py)
- Slides — `claw convert slides <in.md> --format reveal|beamer|pptx` · [src](scripts/claw/src/claw/convert/slides.py)


## SEND / COMPOSE email — `claw email` · [src](scripts/claw/src/claw/email/)

- Build + send — `claw email send --to … [--attach @PATH] [--html FILE] [--inline CID=…]` · [src](scripts/claw/src/claw/email/send.py)
  - Ref: [claw email](references/claw/email.md)
  - Escape hatch: [Python `email.mime` + Gmail API](references/claw/email.md#when-claw-email-isnt-enough) — bulk merge >100 recipients, iCalendar, S/MIME
- Reply / forward / draft — `claw email reply|forward|draft <msg-id>` (auto In-Reply-To / References) · [src](scripts/claw/src/claw/email/)
- Search — `claw email search --q "…" [--max N]` · [src](scripts/claw/src/claw/email/search.py)
- Download attachment — `claw email download-attachment <msg-id> <att-id> --out PATH` · [src](scripts/claw/src/claw/email/download_attachment.py)


## PROCESS images — `claw img` · [src](scripts/claw/src/claw/img/)

- Resize / fit / pad / thumb / crop — `claw img resize|fit|pad|thumb|crop` (ImageMagick geometry syntax) · [src](scripts/claw/src/claw/img/)
- Enhance — `claw img enhance [--autocontrast --equalize --posterize --solarize]` · `sharpen` · `composite` · `watermark` · `overlay` · [src](scripts/claw/src/claw/img/)
- Convert format — `claw img convert | to-jpeg | to-webp [--animated --lossless]` · [src](scripts/claw/src/claw/img/)
- EXIF — `claw img exif [strip|auto-rotate|set]` · `rename --template "{CreateDate:%Y%m%d}_{Camera}.{ext}"` · [src](scripts/claw/src/claw/img/)
- Batch — `claw img batch <dir> --op "resize:1024|strip|webp:85" [--recursive]` · [src](scripts/claw/src/claw/img/batch.py)
- Frames → GIF — `claw img gif-from-frames <dir> --fps N` · [src](scripts/claw/src/claw/img/gif_from_frames.py)
  - Ref: [claw img](references/claw/img.md) · Escape hatch: [Pillow / ImageMagick](references/claw/img.md#when-claw-img-isnt-enough)


## PROCESS video / audio — `claw media` · [src](scripts/claw/src/claw/media/)

- Trim / compress / scale / concat — `claw media trim|compress|scale|concat` · [src](scripts/claw/src/claw/media/)
- Extract audio / frames — `claw media extract-audio|thumbnail|gif` · [src](scripts/claw/src/claw/media/)
- Normalize / effects — `claw media loudnorm|speed|fade|burn-subs|crop-auto` · [src](scripts/claw/src/claw/media/)
- Info — `claw media info <file> [--json]` (jc-style normalized ffprobe output) · [src](scripts/claw/src/claw/media/info.py)
  - Ref: [claw media](references/claw/media.md) · Escape hatch: [ffmpeg / ffprobe](references/claw/media.md#when-claw-media-isnt-enough)


## GOOGLE WORKSPACE — `claw doc | claw sheet | claw email` (plus raw `gws` for uncovered APIs) · [doc src](scripts/claw/src/claw/doc/) · [sheet src](scripts/claw/src/claw/sheet/) · [email src](scripts/claw/src/claw/email/)

- Docs — see CREATE / READ branches above
- Sheets / Drive — see CREATE branch above
- Gmail — see SEND branch above
- Escape hatch (all services): [gws CLI reference](references/gws-cli.md) — Drive permissions, Calendar events, Tasks, batch-update request shapes
  - Read-first rules: [critical rules](references/gws-cli.md#critical-rules-read-first--violations-cause-errors) · [general syntax](references/gws-cli.md#general-syntax) · [global CLI flags](references/gws-cli.md#global-cli-flags) · [`+helper` commands](references/gws-cli.md#ergonomic-helper-commands) · [auth / login / scopes](references/gws-cli.md#auth)
  - Per-service deep dives: [drive](references/gws-cli.md#drive) · [sheets](references/gws-cli.md#sheets) · [docs](references/gws-cli.md#docs) · [slides](references/gws-cli.md#slides) · [gmail](references/gws-cli.md#gmail) · [calendar](references/gws-cli.md#calendar) · [tasks](references/gws-cli.md#tasks)
  - Reference tables: [common MIME types](references/gws-cli.md#common-mime-types) · [sharing patterns](references/gws-cli.md#sharing-patterns)


## MANAGE tasks (ClickUp) — `clickup` CLI (already a CLI — `claw` does not wrap)

- Ref: [clickup-cli reference](references/clickup-cli.md)
  - Setup + output: [conventions](references/clickup-cli.md#conventions-important) · [setup](references/clickup-cli.md#setup) · [output flags](references/clickup-cli.md#output-flags-most-commands)
  - Core nouns: [task management](references/clickup-cli.md#task-management) · [status management](references/clickup-cli.md#status-management) · [sprint management](references/clickup-cli.md#sprint-management) · [comments](references/clickup-cli.md#comments) · [time tracking](references/clickup-cli.md#time-tracking) · [custom fields](references/clickup-cli.md#custom-fields)
  - Workflow glue: [git integration (PR / branch / commit)](references/clickup-cli.md#git-integration) · [checklists / dependencies / tags](references/clickup-cli.md#checklists-dependencies-tags-on-tasks) · [workspace](references/clickup-cli.md#workspace) · [misc](references/clickup-cli.md#more)
- Ex: [clickup-workflows.md](examples/clickup-workflows.md)
  - Task ops: [read a task](examples/clickup-workflows.md#read-a-task) · [search tasks](examples/clickup-workflows.md#search-tasks) · [list tasks in a list](examples/clickup-workflows.md#list-tasks-in-a-list) · [create a task](examples/clickup-workflows.md#create-a-task) · [update status](examples/clickup-workflows.md#update-task-status) · [sprint view](examples/clickup-workflows.md#sprint-view)
  - Collab + tracking: [comments](examples/clickup-workflows.md#comments) · [time tracking](examples/clickup-workflows.md#time-tracking) · [custom fields](examples/clickup-workflows.md#custom-fields) · [git integration (branch workflow)](examples/clickup-workflows.md#git-integration) · [workspace navigation](examples/clickup-workflows.md#workspace) · [development workflow pattern](examples/clickup-workflows.md#development-workflow-pattern)


## AUTOMATE browser — `claw browser launch` + Chrome DevTools MCP · [src](scripts/claw/src/claw/browser/)

- Launch — `claw browser launch [--profile default|throwaway] [--port 9222]` · [src](scripts/claw/src/claw/browser/launch.py)
  - Ref: [claw browser](references/claw/browser.md) — launch / verify / stop + [escape hatch for manual binary invocation](references/claw/browser.md#escape-hatch--manual-browser-launch)
- Post-launch automation — Chrome DevTools MCP tool calls (`list_pages`, `new_page`, `navigate_page`, `take_screenshot`, etc.)


## QUERY database — MySQL MCP

- Ref: [healthcheck auto-installs MCP config](scripts/healthcheck.py) with placeholder env vars; edit then restart Claude Code


## ORCHESTRATE (multi-step pipelines) — `claw pipeline run <recipe.yaml>` · [src](scripts/claw/src/claw/pipeline/)

- Ref: [claw pipeline](references/claw/pipeline.md) — YAML DSL with `${vars.*}`, `${step.output}`, `${env:…}`, `${file:…}` interpolation; Nextflow-style content-hash cache + `--resume`; parallel execution; `retries`, `on-error`, `when:` guards
- Commands: `run` · [src](scripts/claw/src/claw/pipeline/run.py) · `validate` · [src](scripts/claw/src/claw/pipeline/validate.py) · `list-steps` · [src](scripts/claw/src/claw/pipeline/list_steps.py) · `graph` · [src](scripts/claw/src/claw/pipeline/graph.py)
- Ex: [claw-pipelines.md](examples/claw-pipelines.md) — 15+ worked recipes
  - Report & deliver: [DB → styled XLSX + PDF → Drive → Gmail](examples/claw-pipelines.md#db-to-styled-xlsx--pdf-to-drive-to-gmail) · [CSV → XLSX → Google Sheet](examples/claw-pipelines.md#csv-to-styled-xlsx-to-google-sheet) · [scheduled DB snapshot → Sheet](examples/claw-pipelines.md#scheduled-db-snapshot-to-google-sheet)
  - Extract & deliver: [PDF tables → multi-sheet XLSX + summary](examples/claw-pipelines.md#pdf-tables-to-multi-sheet-xlsx-to-pdf-summary) · [HTML → XLSX → email](examples/claw-pipelines.md#html-page-to-xlsx-to-email) · [JSON API → flattened XLSX → Drive](examples/claw-pipelines.md#json-api-to-flattened-xlsx-to-drive)
  - ETL round-trip: [Sheet → enrich → upload-back](examples/claw-pipelines.md#google-sheet-download-enrich-upload-back) · [Excel → SQL → styled XLSX](examples/claw-pipelines.md#excel-to-sql-transform-to-styled-xlsx)
  - Multi-format publish: [Markdown → HTML + PDF + DOCX + EPUB](examples/claw-pipelines.md#markdown-to-html--pdf--docx--epub) · [Slide deck: outline → pptx + PDF + images](examples/claw-pipelines.md#slide-deck-build-outline-to-pptx--pdf--images)
  - Media pipelines: [photo batch (EXIF + resize + watermark + upload)](examples/claw-pipelines.md#photo-batch-strip-exif--resize--watermark--upload) · [video trim + compress + contact sheet](examples/claw-pipelines.md#video-trim--compress--thumbnail-contact-sheet)
  - Orchestration primitives: [parallel fan-out / fan-in](examples/claw-pipelines.md#parallel-fan-out--fan-in) · [conditional step `when:`](examples/claw-pipelines.md#conditional-step-with-when) · [retry on transient HTTP failure](examples/claw-pipelines.md#retry-on-transient-http-failure) · [resume after partial failure](examples/claw-pipelines.md#resume-after-partial-failure)


## RECIPES — one-liner cookbook ([claw-recipes.md](examples/claw-recipes.md))

- CREATE: [blank workbook / doc / deck / PDF](examples/claw-recipes.md#create-blank) · [from data (CSV / JSON / MD / HTML / PDF tables)](examples/claw-recipes.md#create-from-data) · [PDF from HTML or Markdown](examples/claw-recipes.md#create-pdf-from-source)
- READ / EXTRACT: [cells and text](examples/claw-recipes.md#read-cells-and-text) · [from PDF](examples/claw-recipes.md#read--extract-from-pdf) · [web and XML](examples/claw-recipes.md#read-web-and-xml) · [metadata](examples/claw-recipes.md#read-metadata)
- TRANSFORM / EDIT: [workbook](examples/claw-recipes.md#transform-workbook) · [PDF](examples/claw-recipes.md#transform-pdf) · [image](examples/claw-recipes.md#transform-image) · [docs and decks](examples/claw-recipes.md#transform-docs-and-decks)
- CONVERT: [via pandoc](examples/claw-recipes.md#convert-via-pandoc) · [office](examples/claw-recipes.md#convert-office) · [image / media](examples/claw-recipes.md#convert-image--media)
- MEDIA / SEND / BROWSER: [media ops](examples/claw-recipes.md#media-ops) · [send email](examples/claw-recipes.md#send-email) · [Drive + Sheets](examples/claw-recipes.md#send-via-drive-and-sheets) · [browser ops](examples/claw-recipes.md#browser-ops) · [pipeline ops](examples/claw-recipes.md#pipeline-ops) · [diagnose](examples/claw-recipes.md#diagnose) · [quick reference cheat sheet](examples/claw-recipes.md#quick-reference-cheat-sheet)


## DIAGNOSE environment — `claw doctor` · [src](scripts/claw/src/claw/doctor.py)

- Ref: [claw doctor](references/claw/doctor.md) — Python packages, CLI tools, LaTeX packages, Gmail scopes, config validation, cache health
- Output modes: human · `--json` · `--prometheus`


## SHELL COMPLETIONS — `claw completion bash|zsh|fish|pwsh` · [src](scripts/claw/src/claw/completion.py)

- Ref: [claw completion](references/claw/completion.md)


## SETUP / INSTALL — one-command: `python ~/.claude/skills/claude-claw/scripts/healthcheck.py --install`

- Installs every Python package, CLI tool (winget), the `claw` package, MCP server config, and the `claude-claw` block in `~/.claude/CLAUDE.md`.
- Interactive steps it can't automate: `gws auth login`, Chrome DevTools via `/plugin`, editing MCP env vars — printed as "NEXT STEPS" after install.


## CUSTOMIZE Claude apps (Code + Desktop) for local-model use

- [Overview & comparison table](references/claude-customization.md#at-a-glance) · [Why two different approaches](references/claude-customization.md#why-two-different-approaches) · [Launch wrappers (codel/claudel/claudedl/codexl)](references/claude-customization.md#launch-wrappers) · [Installing wrappers to PATH](references/claude-customization.md#installing-the-wrappers) · [Combining both for Claude Desktop](references/claude-customization.md#combining-both-for-claude-desktop) · [When to use what](references/claude-customization.md#when-to-use-what)
- **PATCH Claude Code binary** — bigger context/output ([detail](references/patchers/claude-patcher.md))
  - Orientation: [what it does](references/patchers/claude-patcher.md#what-it-does) · [patchable constants](references/patchers/claude-patcher.md#patchable-constants) · [usage](references/patchers/claude-patcher.md#usage) · [after updates](references/patchers/claude-patcher.md#after-claude-code-updates) · [how it works](references/patchers/claude-patcher.md#how-it-works)
  - Anchor details: [the four anchors in detail](references/patchers/claude-patcher.md#the-four-anchors-in-detail) → [context window](references/patchers/claude-patcher.md#1-context-window--return-1e6-proximity) · [max output](references/patchers/claude-patcher.md#2-max-output--model-name-string-proximity) · [autocompact](references/patchers/claude-patcher.md#3-autocompact--1e6--3000--autocompact-cluster) · [summary max](references/patchers/claude-patcher.md#4-summary-max--system-prompt-instruction-string)
  - Ops / caveats: [recovery when an anchor breaks](references/patchers/claude-patcher.md#recovery-when-an-anchor-breaks) · [when you should NOT patch](references/patchers/claude-patcher.md#when-you-should-not-patch) · [limitations](references/patchers/claude-patcher.md#limitations)
- **TOGGLE Claude Desktop Custom 3P (BYOM)** — registry policy, no binary changes ([detail](references/patchers/claude-desktop-3p.md))
  - Orientation: [what it does](references/patchers/claude-desktop-3p.md#what-it-does) · [why it's needed](references/patchers/claude-desktop-3p.md#why-its-needed) · [requirements](references/patchers/claude-desktop-3p.md#requirements) · [usage](references/patchers/claude-desktop-3p.md#usage) · [verifying via main.log](references/patchers/claude-desktop-3p.md#verifying-it-worked) · [registry schema](references/patchers/claude-desktop-3p.md#registry-schema-what-gets-written)
  - Ops / caveats: [after Claude Desktop updates](references/patchers/claude-desktop-3p.md#after-claude-desktop-updates) · [recovery when it stops working](references/patchers/claude-desktop-3p.md#recovery-when-it-stops-working) · [limitations](references/patchers/claude-desktop-3p.md#limitations)
  - Research trail: [research notes — how this was discovered](references/patchers/claude-desktop-3p.md#research-notes--how-this-was-discovered) · [dead-ends ruled out](references/patchers/claude-desktop-3p.md#dead-ends-ruled-out-first) · [what surfaced 3P mode](references/patchers/claude-desktop-3p.md#what-surfaced-3p-mode) · [activation chain](references/patchers/claude-desktop-3p.md#the-activation-chain) · [HTTPS gotcha](references/patchers/claude-desktop-3p.md#the-https-gotcha) · [HKCU + HKLM rationale](references/patchers/claude-desktop-3p.md#why-both-hkcu--hklm) · [schema source of truth](references/patchers/claude-desktop-3p.md#schema-source-of-truth)

## PATCH third-party apps

- **WHITEN LM Studio tray icon** — on-demand `apply` / `restore`; re-run after each LM Studio update ([detail](references/patchers/lm-studio-white-tray.md))
  - [Critical rules](references/patchers/lm-studio-white-tray.md#critical-rules) · [how it works](references/patchers/lm-studio-white-tray.md#how-it-works) · [usage](references/patchers/lm-studio-white-tray.md#usage) · [customize icon](references/patchers/lm-studio-white-tray.md#customize-icon-design) · [troubleshooting](references/patchers/lm-studio-white-tray.md#troubleshooting) · [quick reference](references/patchers/lm-studio-white-tray.md#quick-reference)
- **INJECT markdown section into any file** — generic, idempotent ([detail](references/patchers/md-section-patcher.md))
  - [Critical rules](references/patchers/md-section-patcher.md#critical-rules) · [markers](references/patchers/md-section-patcher.md#markers) · [usage (`apply` / `status` / `remove`)](references/patchers/md-section-patcher.md#usage) · [worked example](references/patchers/md-section-patcher.md#worked-example) · [status exit codes](references/patchers/md-section-patcher.md#status-exit-codes) · [remove](references/patchers/md-section-patcher.md#remove) · [quick reference](references/patchers/md-section-patcher.md#quick-reference)



## Templates & Extension Guides

- **Reference template** — [references/_TEMPLATE.md](references/_TEMPLATE.md) — Contents tree -> Critical Rules -> numbered API sections -> Quick Reference. Copy for a new library or noun.
- **Example template** — [examples/_TEMPLATE.md](examples/_TEMPLATE.md) — Contents tree -> numbered self-contained workflows. Copy for end-to-end recipes.
- **Script template** — [scripts/_TEMPLATE.py](scripts/_TEMPLATE.py) — exit codes, status prefixes, cross-platform conventions. For standalone scripts, not claw verbs.
- **Agent extension guide** — [references/claw/contributing.md](references/claw/contributing.md) — exact checklists for agents adding a `claw` verb, adding a whole noun, fixing a bug, adding/deprecating a flag. Includes pitfalls (code, docs, anchors) and verification commands.

## Scripts

- [scripts/healthcheck.py](scripts/healthcheck.py) — one-command installer (`--install` / `--upgrade`); verifies packages, CLI tools, MCP servers, LSP plugins, claw package, and the `claude-claw` block in `~/.claude/CLAUDE.md`.
- [scripts/claw/](scripts/claw/) — the `claw` CLI package itself (`pip install -e scripts/claw[all]` registered by healthcheck). Package layout: [scripts/claw/src/claw/](scripts/claw/src/claw/) · entry point [__main__.py](scripts/claw/src/claw/__main__.py) · shared helpers [common/](scripts/claw/src/claw/common/) · metadata [pyproject.toml](scripts/claw/pyproject.toml).
- [scripts/patchers/claude-patcher.js](scripts/patchers/claude-patcher.js) — Claude Code binary patcher (context window, output limits).
- [scripts/patchers/claude-desktop-3p.py](scripts/patchers/claude-desktop-3p.py) — Claude Desktop 3P/BYOM toggle (registry policy).
- [scripts/patchers/lm-studio-white-tray.py](scripts/patchers/lm-studio-white-tray.py) — LM Studio white tray-icon patcher.
- [scripts/patchers/md-section-patcher.py](scripts/patchers/md-section-patcher.py) — generic idempotent markdown-section injector (used by healthcheck to maintain the `claude-claw` block in `~/.claude/CLAUDE.md`).
- [scripts/wrappers/codel.bat](scripts/wrappers/codel.bat) — VS Code Insiders + local-model env.
- [scripts/wrappers/claudel.bat](scripts/wrappers/claudel.bat) — Claude Code CLI + local-model env.
- [scripts/wrappers/claudedl.bat](scripts/wrappers/claudedl.bat) — Claude Desktop launcher + dynamic MSIX path + local-model env.
- [scripts/wrappers/codexl.bat](scripts/wrappers/codexl.bat) — Codex CLI in OSS mode.
