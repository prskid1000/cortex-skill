---
name: cortex
description: >
  ALWAYS LOAD THIS SKILL ON EVERY CONVERSATION WITHOUT EXCEPTION — this is the OS layer.
  Autonomous brain, project tracker, and productivity OS.
  Manages: Obsidian knowledge base (KB mesh), Jira-like issue tracking (epics/stories/tasks/bugs/sprints/kanban),
  adaptive cron heartbeats, Google Workspace (Drive/Sheets/Docs/Slides/Gmail/Calendar/Tasks),
  document creation (Excel/Word/PowerPoint/PDF), screenshots, email workflows, git operations,
  image/video/audio processing, MySQL database queries, data conversion pipelines, auto-testing,
  auto-improvement, and script capture.
  Also trigger when user mentions: obsidian, KB, knowledge, worklog, board, epic, story, sprint,
  ticket, issue, google workspace, gws, drive, sheets, docs, slides, gmail, calendar, email,
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
          command: "echo 'PRE-COMPACT: Flush ALL pending KB entries, Board snapshot, and WorkLog before compaction. CronDelete all cortex crons.'"
          timeout: 3
  Stop:
    - hooks:
        - type: command
          command: "bash -c 'rm -f /tmp/cortex_reminded_$$PPID 2>/dev/null; true'"
          timeout: 3
---

# Cortex — Autonomous Brain, Tracker & Productivity OS

> Always-on operating system layer for knowledge persistence, project tracking, document creation, and tool orchestration.

---

## File Map

### `docs/` — Reference Documentation

| File | Domain | What's Inside |
|------|--------|---------------|
| [knowledge-base.md](docs/knowledge-base.md) | Obsidian KB | Tree structure, 14 MCP tools, node rules, subagent templates, WorkLog/Bug formats, data hygiene |
| [issue-tracker.md](docs/issue-tracker.md) | Board | Epics/Stories/Tasks/Bugs, status workflows, ticket templates, kanban dashboard, sprint management |
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
| [startup.py](bin/startup.py) | Session bootstrap: print structured steps for Claude to execute | `python ~/.claude/skills/cortex/bin/startup.py [--mode coding\|research\|review\|quick]` |
| [healthcheck.py](bin/healthcheck.py) | Verify environment: packages, CLIs, MCPs, structure | `python ~/.claude/skills/cortex/bin/healthcheck.py` |
| [evolve.py](bin/evolve.py) | Self-improvement: detect gaps, stale content, suggest/apply fixes | `python ~/.claude/skills/cortex/bin/evolve.py [--apply]` |
| [stash.py](bin/stash.py) | Capture reusable scripts to cookbook/ with auto-genericizing | `python ~/.claude/skills/cortex/bin/stash.py --name X --source Y` |

### `cookbook/` — Reusable Script Templates

Auto-populated during work sessions. When you create a useful, reusable script:
1. Save genericized version: `python ~/.claude/skills/cortex/bin/stash.py --name "descriptive-name" --source /tmp/script.py --tags "tag1,tag2"`
2. Browse existing: `python ~/.claude/skills/cortex/bin/stash.py --list`
3. Search: `python ~/.claude/skills/cortex/bin/stash.py --search "keyword"`

---

## Session Bootstrap

```
1. READ CONTEXT
   → search_notes(project/topic keywords)
   → read_multiple_notes(["KB/Projects/{name}/_index.md", "WorkLog/{YYYY-MM}.md", "Board/_board.md"])

2. CLEAN ORPHAN CRONS
   → CronList → delete any stale "Cortex heartbeat" crons from previous sessions

3. SET HEARTBEAT (if sustained work)
   → Assess work intensity → CronCreate with appropriate interval

4. HEALTHCHECK (first session or on errors)
   → python ~/.claude/skills/cortex/bin/healthcheck.py
```

---

## Heartbeat Lifecycle

### Create → Monitor → Adjust → Tear Down

**1. Assess & Create** (session start)
- `CronList` → find/delete orphaned heartbeat crons
- Assess work mode → pick interval → `CronCreate`
- Prompt must include **"Cortex heartbeat"** (for orphan detection)

**2. Adjust** (during work)
- Intensity changes → `CronDelete` old → `CronCreate` new
- User goes idle → `CronDelete` (no point syncing nothing)
- User returns → `CronCreate` fresh

**3. Tear Down** (session end / pre-compact)
- `CronList` → `CronDelete` all cortex crons
- Final flush: spawn KB subagent to persist everything

### Interval Table

| Mode | Interval | Signals |
|------|----------|---------|
| Active coding | 10 min | Rapid edits, builds, tests, commits |
| Research | 20 min | Reading code, docs, web searches |
| Light/review | 30 min | Q&A, planning, code review |
| Quick question | None | Single question, no sustained work |

### Heartbeat Prompt
```
Cortex heartbeat: background subagent to sync pending knowledge.
1. Append WorkLog if new activity since last sync
2. Patch KB nodes with new findings
3. Update Board tickets if status changed
4. Run data hygiene (truncate stale, merge duplicates)
SKIP if nothing changed since last sync.
```

### Rules
- **One heartbeat at a time** — delete before creating new
- **Always `CronList` first** — no duplicates
- **Always tear down** — never orphan crons
- **Tag with "Cortex heartbeat"** — for orphan detection

---

## Knowledge Sync Triggers

| Priority | Triggers | Actions |
|----------|----------|---------|
| CRITICAL | Before auto-compact | Flush ALL: WorkLog resume + Board snapshot + KB nodes |
| HIGH | Topic switch | Close WorkLog entry, open new, update Board if switching tickets |
| HIGH | Subtask complete | Append WorkLog, patch KB, move ticket → DONE |
| HIGH | Error encountered | Create BUG ticket, append to Bugs.md, tag INVESTIGATING |
| HIGH | Error resolved | Patch bug + ticket → CLOSED, link to Patterns |
| HIGH | User teaches | Patch relevant KB node immediately |
| HIGH | Work item started | Create/move ticket → IN_PROGRESS, update Board |
| MED | Decision made | Create `Decisions/{date}-{slug}.md`, log in ticket |
| MED | New pattern | Patch Patterns node |
| MED | Debug step | Append to Debug Trail (Bugs.md + BUG ticket) |
| MED | Research done | Update Research/ or project KB node |
| MED | Sprint boundary | Archive completed sprint, create new, carry over |
| LOW | Heartbeat fires | Sync accumulated changes (skip if nothing new) |

**Always** background subagent for writes. **Never** blank nodes. **Batch** triggers firing close together.

---

## Board (Jira-like Tracking)

`Epic → Story → Task` + standalone `Bug`

Status: `BACKLOG → TODO → IN_PROGRESS → IN_REVIEW → DONE` (+ `BLOCKED`)

**Auto-behaviors:** start work → create TASK if none → IN_PROGRESS | finish → DONE | error → create BUG | sprint end → archive + carry over

Full reference: [docs/issue-tracker.md](docs/issue-tracker.md)

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
| Obsidian KB rules & tools | [docs/knowledge-base.md](docs/knowledge-base.md) |
| Track work with tickets | [docs/issue-tracker.md](docs/issue-tracker.md) |
| Install missing tools | [docs/bootstrap.md](docs/bootstrap.md) |

---

## Auto-Evolve

After every 5th subtask or on request ("improve cortex" / "update skill"):
1. Run `evolve.py` — detect gaps, stale docs, missing coverage
2. Patch reference docs with new patterns/recipes discovered during work
3. Capture interesting scripts to `cookbook/`
4. Log improvement in WorkLog

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

3. **New cookbook entry?** Use `bin/stash.py` — it handles naming, headers, and indexing automatically.

### File Naming Convention

```
docs/                          bin/                       cookbook/
├── {domain-noun}.md           ├── {action-noun}.py       ├── {descriptive-name}.py
│   knowledge-base.md          │   healthcheck.py          │   csv-to-styled-excel.py
│   issue-tracker.md           │   evolve.py               │   pdf-invoice-parser.py
│   workspace.md               │   stash.py                │   bulk-image-resize.py
│   doc-forge.md               │                           │   db-export-to-sheets.py
│   mailbox.md                 │                           │
│   media-kit.md               │                           │
│   datastore.md               │                           │
│   pipelines.md               │                           │
│   bootstrap.md               │                           │
```

**Rules:**
- kebab-case, no underscores
- Docs: noun-based (what it covers), 1-2 words
- Bin: action/tool-based (what it does), 1 word preferred
- Cookbook: descriptive (what the script does), 2-4 words

---

## Autonomous Behaviors

1. **KB-first** — all learned knowledge → Obsidian via background subagent
2. **Board-driven** — track all work through tickets, auto-create/close
3. **Adaptive sync** — dynamic heartbeat matching work intensity
4. **Auto-compact** — flush everything before context compaction
5. **Continuity** — new session → read KB + WorkLog + Board
6. **File ops** — download → edit locally → upload (automate everything)
7. **Sprint mgmt** — auto-archive/carry-over at week boundaries
8. **Clean crons** — no orphans, ever
9. **Auto-evolve** — improve skill docs from real usage
10. **Auto-install** — fix missing dependencies on detection
11. **Script capture** — save reusable scripts to cookbook/
12. **Auto-add files** — create new docs/scripts when new domains emerge

## Browser

- Always use Microsoft Edge, never Chrome.
