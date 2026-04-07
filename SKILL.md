---
name: claude-claw
description: >
  Create, edit, convert, and export documents, spreadsheets, presentations, PDFs, images, videos, and audio files.
  Manage Google Workspace (Drive, Sheets, Docs, Gmail), ClickUp tasks, and MySQL databases.
  TRIGGERS: Excel, Word, PowerPoint, PDF, spreadsheet, document, presentation, slide deck,
  report, invoice, letter, resume, certificate, chart, table, CSV export,
  image resize, crop, watermark, thumbnail, screenshot, photo edit,
  video trim, compress, convert, audio extract, ffmpeg, media processing,
  email send, Gmail, Google Drive upload, Google Sheets,
  database query, SQL, MySQL, data export, data pipeline,
  file conversion, pandoc, HTML to PDF, markdown to docx,
  ClickUp tasks, sprint, time tracking,
  code review, blast radius, impact analysis, dead code, refactor, code graph, architecture,
  callers, callees, dependencies, test coverage, complexity, communities, wiki,
  conversation history, session search, past solutions, error solutions, file context,
  openpyxl, python-docx, python-pptx, reportlab, Pillow, ImageMagick.
priority: critical
---

# Claude Claw — Productivity OS

> Always-on operating system layer for document creation, tool orchestration, and productivity automation.

---

## Bootstrap (every session)

On first `/claude-claw` invocation each session, run the healthcheck script:

```bash
python ~/.claude/skills/claude-claw/scripts/healthcheck.py
```

If any check fails, attempt auto-fix or warn the user.

---

## References

Detailed tool capabilities, commands, and API surfaces. Load when working with a specific tool.

| Need | Reference |
|------|-----------|
| Google Workspace CLI | [references/gws-cli.md](references/gws-cli.md) |
| Excel / Word / PowerPoint | [references/document-creation.md](references/document-creation.md) |
| PDF tools | [references/pdf-tools.md](references/pdf-tools.md) |
| Image / Video / Audio | [references/media-tools.md](references/media-tools.md) |
| Document conversion | [references/conversion-tools.md](references/conversion-tools.md) |
| HTML/XML parsing | [references/web-parsing.md](references/web-parsing.md) |
| Email / MIME | [references/email-reference.md](references/email-reference.md) |
| Database / MySQL | [references/database-reference.md](references/database-reference.md) |
| ClickUp CLI | [references/clickup-cli.md](references/clickup-cli.md) |
| Code Review Graph (code analysis) | [references/code-review-graph.md](references/code-review-graph.md) |
| Conversation History (claude-historian) | [references/claude-historian.md](references/claude-historian.md) |
| Install / troubleshoot | [references/setup.md](references/setup.md) |
| Claude Code binary patcher | [references/claude-patcher.md](references/claude-patcher.md) |

## Examples

Working code blocks for common tasks. Load when executing a specific workflow.

| Task | Examples |
|------|----------|
| Excel / Word / PPT creation | [examples/office-documents.md](examples/office-documents.md) |
| PDF generation & extraction | [examples/pdf-workflows.md](examples/pdf-workflows.md) |
| Image processing | [examples/image-processing.md](examples/image-processing.md) |
| Video / audio processing | [examples/video-audio.md](examples/video-audio.md) |
| Email composition & sending | [examples/email-workflows.md](examples/email-workflows.md) |
| Database query & export | [examples/database-export.md](examples/database-export.md) |
| End-to-end pipelines | [examples/data-pipelines.md](examples/data-pipelines.md) |
| Document conversion | [examples/document-conversion.md](examples/document-conversion.md) |
| ClickUp task management | [examples/clickup-workflows.md](examples/clickup-workflows.md) |

## Tool Selection Quick Guide

### Document Creation
| Format | Library | When to use |
|--------|---------|-------------|
| Excel .xlsx | `openpyxl` | Tables, charts, styled reports, data exports |
| Word .docx | `python-docx` | Narrative text, formatted reports, letters |
| PowerPoint .pptx | `python-pptx` | Slide decks, presentations with charts |
| PDF (generate) | `reportlab` | From-scratch PDFs with precise layout |
| PDF (edit/render) | `pymupdf` (fitz) | Read, annotate, merge, split, render pages |
| PDF (extract tables) | `pdfplumber` | Extract tabular data from PDFs |
| PDF (merge/split) | `PyPDF2` | Simple merge, split, rotate, encrypt |

### Media Processing
| Task | Tool |
|------|------|
| Image manipulation (Python) | `Pillow` (PIL) |
| Image manipulation (CLI) | `magick` (ImageMagick) |
| Video/audio processing | `ffmpeg` |
| Document conversion | `pandoc` |
| PDF page screenshots | `pymupdf` (fitz) |
| Web screenshots / browser automation | Chrome DevTools MCP (`mcp__plugin_chrome-devtools-mcp_chrome-devtools__*`) — provisioned by the claude-claw bootstrap |

### Code Analysis & Review
| Task | Tool |
|------|------|
| Build/update code graph | `build_or_update_graph_tool` — parse codebase into AST graph |
| Blast radius analysis | `get_impact_radius_tool` — trace callers, dependents, tests affected by changes |
| Review context | `get_review_context_tool` — token-optimised structural summary for reviews |
| Query graph | `query_graph_tool` — callers, callees, tests, imports, inheritance |
| Semantic code search | `semantic_search_nodes_tool` — search code entities by name or meaning |
| Change impact | `detect_changes_tool` — risk-scored change impact analysis |
| Architecture overview | `get_architecture_overview_tool` — community-based architecture map |
| Find large functions | `find_large_functions_tool` — functions/classes exceeding line threshold |
| Execution flows | `list_flows_tool` / `get_flow_tool` / `get_affected_flows_tool` — trace execution paths |
| Refactoring | `refactor_tool` / `apply_refactor_tool` — rename preview, dead code, suggestions |
| Communities | `list_communities_tool` / `get_community_tool` — detected code communities |
| Wiki generation | `generate_wiki_tool` / `get_wiki_page_tool` — markdown docs from graph |
| Multi-repo | `list_repos_tool` / `cross_repo_search_tool` — search across registered repos |
| Graph health | `list_graph_stats_tool` — graph size and stats |

### Conversation History (claude-historian)
| Task | Tool |
|------|------|
| Search past conversations | `mcp__plugin_claude-historian_historian__search_conversations` — full-text search across all sessions |
| Find similar queries | `mcp__plugin_claude-historian_historian__find_similar_queries` — past questions like the current one |
| Error solutions | `mcp__plugin_claude-historian_historian__get_error_solutions` — past fixes for similar errors |
| File context | `mcp__plugin_claude-historian_historian__find_file_context` — past work on a specific file |
| Tool patterns | `mcp__plugin_claude-historian_historian__find_tool_patterns` — how tools were used before |
| Search plans | `mcp__plugin_claude-historian_historian__search_plans` — past implementation plans |
| List sessions | `mcp__plugin_claude-historian_historian__list_recent_sessions` — browse recent sessions |
| Compact summary | `mcp__plugin_claude-historian_historian__extract_compact_summary` — session summaries |

### Data & Integration
| Task | Tool |
|------|------|
| Google Workspace | `gws` CLI |
| ClickUp tasks | `clickup` CLI (tasks, sprints, comments, time, git) |
| MySQL database | `mcp__mcp_server_mysql__mysql_query` — provisioned by the claude-claw bootstrap |
| HTML/XML parsing | `lxml`, `beautifulsoup4` |
| Email composition | Python `email.mime` + `gws gmail users messages send` |

## Core Workflow Pattern

```
Source -> Transform (Python) -> Output file (/tmp/) -> Upload/Send (gws)
```

1. **Source**: database query, CSV, JSON, API, user input, existing file
2. **Transform**: Python processing (openpyxl, python-docx, Pillow, etc.)
3. **Output**: save to `/tmp/` as .xlsx, .docx, .pdf, .png, etc.
4. **Deliver**: `gws drive +upload /tmp/file.xlsx` or `gws gmail +send --to ... --subject ... --body ...` (convenience helpers); for full control use `gws drive files create --upload` / `gws gmail users messages send`.

