# Cortex

Autonomous brain, project tracker, and productivity OS for Claude Code.

## What It Does

Cortex is an always-on skill that gives Claude Code persistent memory, Jira-like project tracking, and deep tool orchestration — all powered by Obsidian, Google Workspace, and local Python tooling.

| Capability | How |
|------------|-----|
| **Persistent Knowledge** | Obsidian vault with structured KB mesh, auto-synced via background subagents |
| **Issue Tracking** | Epics / Stories / Tasks / Bugs with status workflows, sprints, kanban board |
| **Document Creation** | Excel, Word, PowerPoint, PDF — styled, with charts, uploaded to Drive |
| **Email Automation** | Compose with MIME, attach generated docs, send via Gmail CLI |
| **Database Queries** | MySQL MCP for schema exploration, analytics, data export |
| **Media Processing** | FFmpeg (audio/video), Pillow (images), ImageMagick, Pandoc |
| **Data Pipelines** | CSV→Excel→Sheets, DB→Report→Email, PDF extraction, format conversion |
| **Adaptive Sync** | Dynamic cron heartbeats that scale with work intensity |
| **Self-Healing** | Auto-test environment, auto-install missing packages, auto-improve docs |

## Structure

```
cortex/
├── SKILL.md              # Entry point — file map, heartbeat lifecycle, triggers
├── docs/                 # Reference documentation (9 files)
│   ├── knowledge-base    # Obsidian KB system + 14 MCP tools
│   ├── issue-tracker     # Jira-like board + ticket templates
│   ├── workspace         # Google Workspace CLI (Drive/Sheets/Docs/Slides/Gmail/Calendar)
│   ├── doc-forge         # Document creation recipes (Excel/Word/PPT/PDF)
│   ├── mailbox           # Email composition + Gmail workflows
│   ├── media-kit         # FFmpeg / Pillow / ImageMagick / Pandoc / screenshots
│   ├── datastore         # MySQL MCP queries + export patterns
│   ├── pipelines         # End-to-end data conversion flows
│   └── bootstrap         # Setup, install, and troubleshooting guide
├── bin/                  # Utility scripts (4 files)
│   ├── startup.py        # Session bootstrap — structured steps for Claude
│   ├── healthcheck.py    # Verify all 29 dependencies
│   ├── evolve.py         # Self-improvement analysis
│   └── stash.py          # Capture reusable scripts to cookbook/
└── cookbook/              # Auto-populated reusable script templates
```

## Naming Convention

| Folder | Pattern | Examples |
|--------|---------|---------|
| `docs/` | `{domain-noun}.md` | `knowledge-base`, `datastore`, `mailbox` |
| `bin/` | `{action-noun}.py` | `healthcheck`, `evolve`, `stash` |
| `cookbook/` | `{descriptive-name}.py` | `csv-to-styled-excel`, `pdf-invoice-parser` |

## Auto-Trigger Mechanism

Cortex uses a **three-layer** approach to guarantee it loads on every conversation:

1. **CLAUDE.md instruction** — `~/.claude/CLAUDE.md` tells Claude to invoke `/cortex` BEFORE responding to any first message
2. **Skill description** — leads with `ALWAYS LOAD THIS SKILL ON EVERY CONVERSATION WITHOUT EXCEPTION` plus `priority: critical`
3. **Skill-level hooks** (in SKILL.md frontmatter) — `UserPromptSubmit` reminder, `PreCompact` flush warning, `Stop` cleanup

### Lifecycle

- **Session start** — CLAUDE.md + skill description trigger cortex; `startup.py` prints structured bootstrap steps
- **During work** — adaptive heartbeat crons sync KB in background
- **Pre-compact** — hook reminds Claude to flush all pending KB entries, Board snapshot, WorkLog
- **Session end** — hook cleans up temp marker files; cortex tears down crons

## Quick Start

```bash
# Verify environment
python ~/.claude/skills/cortex/bin/healthcheck.py

# Check skill quality
python ~/.claude/skills/cortex/bin/evolve.py

# Capture a useful script
python ~/.claude/skills/cortex/bin/stash.py --name "my-script" --source /tmp/script.py --tags "excel,report"
```

## Requirements

| Category | Tools |
|----------|-------|
| **Python packages** | openpyxl, python-docx, python-pptx, pymupdf, PyPDF2, reportlab, pdfplumber, pillow, lxml, beautifulsoup4 |
| **CLI tools** | gws, git, ffmpeg, pandoc, imagemagick |
| **MCP servers** | obsidian, mysql (optional), chrome-devtools (optional), clickup (optional) |

See [docs/bootstrap.md](docs/bootstrap.md) for installation instructions.

## How It Works

1. **Session start** — reads Obsidian KB + WorkLog + Board for context, cleans orphan crons, sets adaptive heartbeat
2. **During work** — tracks knowledge via background subagents, manages tickets, adjusts sync interval
3. **On events** — errors create BUG tickets, completions close TASKs, decisions get logged
4. **Session end** — flushes all pending knowledge, tears down crons, no orphans
