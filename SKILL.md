---
name: cortex
description: >
  ALWAYS LOAD THIS SKILL ON EVERY CONVERSATION WITHOUT EXCEPTION — this is the OS layer.
  Autonomous brain and productivity OS.
  Manages: Google Workspace (Drive/Sheets/Docs/Slides/Gmail/Calendar/Tasks),
  document creation (Excel/Word/PowerPoint/PDF), screenshots, email workflows, git operations,
  image/video/audio processing, MySQL database queries, data conversion pipelines, auto-testing,
  and automation workflows.
  Also trigger when user mentions: google workspace, gws, drive, sheets, docs, slides, gmail, calendar, email,
  pdf, excel, word, powerpoint, screenshot, ffmpeg, pandoc, imagemagick, document, report, invoice,
  presentation, spreadsheet, chart, image, video, audio, convert, export, database, mysql, query, sql.
priority: critical
hooks:
  UserPromptSubmit:
    - hooks:
        - type: command
          command: "bash -c 'MARKER=/tmp/cortex_reminded_$$PPID; if [ ! -f \"$MARKER\" ]; then touch \"$MARKER\" && echo \"CORTEX BOOTSTRAP REQUIRED: Invoke /cortex skill NOW before responding.\"; fi'"
          timeout: 5
  PreCompact:
    - hooks:
        - type: command
          command: "echo 'PRE-COMPACT: CronDelete all cortex crons.'"
          timeout: 3
  Stop:
    - hooks:
        - type: command
          command: "bash -c 'rm -f /tmp/cortex_reminded_$$PPID 2>/dev/null; true'"
          timeout: 3
---

# Cortex — Autonomous Brain & Productivity OS

> Always-on operating system layer for document creation, tool orchestration, and productivity automation.

---

## File Map

### `docs/` — Reference Documentation

| File | Domain | What's Inside |
|------|--------|---------------|
| [workspace.md](docs/workspace.md) | Google Workspace | GWS CLI: Drive, Sheets, Docs, Slides, Gmail, Calendar, Tasks — full command reference |
| [doc-forge.md](docs/doc-forge.md) | Documents | Python recipes: Excel (openpyxl), Word (python-docx), PowerPoint (python-pptx), PDF (reportlab/pymupdf/pdfplumber) |
| [mailbox.md](docs/mailbox.md) | Email | MIME composition (text/HTML/attachments), Gmail CLI, send/read/reply, search operators |
| [media-kit.md](docs/media-kit.md) | Media | FFmpeg (audio/video), Pillow (images), ImageMagick (CLI), Pandoc (doc conversion), screenshots |
| [datastore.md](docs/datastore.md) | Database | MySQL MCP: queries, schema exploration, joins, aggregates, export patterns, performance |
| [pipelines.md](docs/pipelines.md) | Data Flows | End-to-end: CSV→Excel→Sheets, DB→Report→Email, PDF→data, JSON/HTML→Excel |
| [bootstrap.md](docs/bootstrap.md) | Setup | Auto-install: Python packages, CLI tools, MCP servers, dependency chain, troubleshooting |

### `bin/` — Executable Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| [healthcheck.py](bin/healthcheck.py) | Verify environment: packages, CLIs, MCPs, structure | `python ~/.claude/skills/cortex/bin/healthcheck.py` |

---

## Session Bootstrap

```
1. HEALTHCHECK (first session of the day)
   → python ~/.claude/skills/cortex/bin/healthcheck.py
```

---

## Quick Access

| Need | Go To |
|------|-------|
| Create Excel/Word/PPT/PDF | [docs/doc-forge.md](docs/doc-forge.md) |
| Send email with attachment | [docs/mailbox.md](docs/mailbox.md) |
| Query database | [docs/datastore.md](docs/datastore.md) |
| Upload to Drive / Sheets | [docs/workspace.md](docs/workspace.md) |
| Process image/video/audio | [docs/media-kit.md](docs/media-kit.md) |
| Convert data formats | [docs/pipelines.md](docs/pipelines.md) |
| Install missing tools | [docs/bootstrap.md](docs/bootstrap.md) |

---

## Auto-Install

When a tool/package/MCP is missing:
1. **Python package** → `pip install <package>` automatically
2. **CLI tool** → suggest `winget install` command to user
3. **MCP server** → provide settings.json snippet, ask user to configure
4. Run [bin/healthcheck.py](bin/healthcheck.py) to verify

Full install guide: [docs/bootstrap.md](docs/bootstrap.md)

---

## Auto-Add Files

When cortex encounters a new domain or capability during work:

1. **New reference doc needed?** Create in `docs/` following naming convention:
   - Pattern: `{domain-noun}.md` (kebab-case, singular concept)
   - Examples: `auth-tokens.md`, `cloud-deploy.md`, `test-runner.md`
   - Must include: title line, one-line description, `**Related:**` links, `---` divider, sections with `##`
   - Update the File Map table in SKILL.md

2. **New script needed?** Create in `bin/` following convention:
   - Pattern: `{verb-or-noun}.py` (short, memorable)
   - Examples: `lint.py`, `snapshot.py`, `migrate.py`
   - Must include: docstring, `--help` via argparse, clean output
   - Update the Scripts table in SKILL.md

### File Naming Convention

```
docs/                          bin/
├── {domain-noun}.md           ├── {action-noun}.py
│   workspace.md               │   healthcheck.py
│   doc-forge.md               │
│   mailbox.md                 │
│   media-kit.md               │
│   datastore.md               │
│   pipelines.md               │
│   bootstrap.md               │
```

**Rules:**
- kebab-case, no underscores
- Docs: noun-based (what it covers), 1-2 words
- Bin: action/tool-based (what it does), 1 word preferred

---

## Autonomous Behaviors

1. **File ops** — download → edit locally → upload (automate everything)
2. **Auto-install** — fix missing dependencies on detection
3. **Auto-add files** — create new docs/scripts when new domains emerge

## Browser

- Always use Microsoft Edge, never Chrome.
