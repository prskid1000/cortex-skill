# Cortex

Autonomous brain and productivity OS for Claude Code.

## What It Does

Cortex is an always-on skill that gives Claude Code deep tool orchestration — powered by Google Workspace and local Python tooling.

| Capability | How |
|------------|-----|
| **Document Creation** | Excel, Word, PowerPoint, PDF — styled, with charts, uploaded to Drive |
| **Email Automation** | Compose with MIME, attach generated docs, send via Gmail CLI |
| **Database Queries** | MySQL MCP for schema exploration, analytics, data export |
| **Media Processing** | FFmpeg (audio/video), Pillow (images), ImageMagick, Pandoc |
| **Data Pipelines** | CSV→Excel→Sheets, DB→Report→Email, PDF extraction, format conversion |
| **Self-Healing** | Auto-test environment, auto-install missing packages |

## Structure

```
cortex/
├── SKILL.md              # Entry point — file map, heartbeat lifecycle, triggers
├── README.md             # This file
├── docs/                 # Reference documentation (7 files)
│   ├── workspace         # Google Workspace CLI (Drive/Sheets/Docs/Slides/Gmail/Calendar)
│   ├── doc-forge         # Document creation recipes (Excel/Word/PPT/PDF)
│   ├── mailbox           # Email composition + Gmail workflows
│   ├── media-kit         # FFmpeg / Pillow / ImageMagick / Pandoc / screenshots
│   ├── datastore         # MySQL MCP queries + export patterns
│   ├── pipelines         # End-to-end data conversion flows
│   └── bootstrap         # Setup, install, and troubleshooting guide
├── bin/                  # Utility scripts
│   ├── healthcheck.py    # Verify environment: packages, CLIs, MCPs, structure
```

## Auto-Trigger Mechanism

Cortex uses a **three-layer** approach to guarantee it loads on every conversation:

1. **CLAUDE.md instruction** — `~/.claude/CLAUDE.md` tells Claude to invoke `/cortex` BEFORE responding to any first message
2. **Skill description** — leads with `ALWAYS LOAD THIS SKILL ON EVERY CONVERSATION WITHOUT EXCEPTION` plus `priority: critical`
3. **Skill-level hooks** (in SKILL.md frontmatter) — `UserPromptSubmit` reminder, `PreCompact` flush warning, `Stop` cleanup

### Lifecycle

- **Session start** — CLAUDE.md + skill description trigger cortex; runs healthcheck
- **During work** — orchestrates tools for document creation, data pipelines, media processing
- **Pre-compact** — hook reminds Claude to clean up crons
- **Session end** — hook cleans up temp marker files

## CLAUDE.md Setup

Copy the block below into your `~/.claude/CLAUDE.md` to enable automatic cortex bootstrap. This is the most critical piece — without it, Claude may not invoke the skill on session start.

````markdown
# User-Level Instructions

---

## ⚠️ STEP ZERO — DO THIS FIRST, EVERY TIME ⚠️

**Your VERY FIRST action in EVERY conversation MUST be:**

```
Skill(skill="cortex")
```

- Do NOT output ANY text before invoking `/cortex`
- Do NOT greet the user first
- Do NOT acknowledge the user's message first
- Do NOT reason about whether cortex is needed — it ALWAYS is
- The skill call must be the FIRST tool call in your FIRST response, before anything else
- If the `UserPromptSubmit` hook fires "CORTEX BOOTSTRAP REQUIRED" and you have NOT yet invoked `/cortex`, you have already failed — invoke it IMMEDIATELY

**After `/cortex` loads**, execute the bootstrap sequence it describes (run healthcheck if first session today), THEN respond to the user.

---

## Cortex Script Triggers (MANDATORY)

These scripts live in `~/.claude/skills/cortex/bin/`. Run them at the specified times — no exceptions.

### `healthcheck.py` — First session of the day
- Run `python ~/.claude/skills/cortex/bin/healthcheck.py` during bootstrap if it hasn't been run today
- If any check fails, attempt auto-fix or warn the user
- Do NOT skip this — environment drift causes silent failures

---

## Re-invoke Cortex

Re-invoke `/cortex` when the user mentions: google workspace, gws, drive, sheets, docs, slides, gmail, calendar, email, pdf, excel, word, powerpoint, screenshot, ffmpeg, pandoc, imagemagick, document, report, invoice, presentation, spreadsheet, chart, image, video, audio, convert, export, database, mysql, query, sql.

## Important: Hook Subagents Cannot Load Skills

Agent-type hooks in settings.json spawn subagents that have NO access to skills. Do not rely on hooks to run `/cortex` bootstrap — it must be triggered from the main conversation via the skill system.
````

## Naming Convention

| Folder | Pattern | Examples |
|--------|---------|---------|
| `docs/` | `{domain-noun}.md` | `datastore`, `mailbox` |
| `bin/` | `{action-noun}.py` | `healthcheck` |

## Quick Start

```bash
# Verify environment
python ~/.claude/skills/cortex/bin/healthcheck.py
```

## Requirements

| Category | Tools |
|----------|-------|
| **Python packages** | openpyxl, python-docx, python-pptx, pymupdf, PyPDF2, reportlab, pdfplumber, pillow, lxml, beautifulsoup4 |
| **CLI tools** | gws, git, ffmpeg, pandoc, imagemagick |
| **MCP servers** | mysql (optional), chrome-devtools (optional), clickup (optional) |

See [docs/bootstrap.md](docs/bootstrap.md) for installation instructions.

## How It Works

1. **Session start** — runs healthcheck, cleans orphan crons
2. **During work** — orchestrates tools, creates documents, processes data
3. **Session end** — cleans up temp files
