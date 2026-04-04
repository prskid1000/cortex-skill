# Cortex

Autonomous brain and productivity OS for Claude Code.

## Quick Start

```bash
python ~/.claude/skills/cortex/scripts/healthcheck.py
```

## Auto-Trigger Mechanism

Cortex uses a **one-layer** approach to guarantee it loads on every conversation:

1. **CLAUDE.md instruction** — `~/.claude/CLAUDE.md` tells Claude to invoke `/cortex` BEFORE responding to any first message

## CLAUDE.md Setup

Add this minimal block to `~/.claude/CLAUDE.md`:

````markdown
# STEP ZERO (every chat)
Skill(skill="cortex")

# First session each day
python ~/.claude/skills/cortex/scripts/healthcheck.py

# Trigger `/cortex` from main conversation (not subagents)
````

## Structure

```
cortex/
├── SKILL.md              # Skill entry point (lean, always loaded)
├── README.md             # This file
├── scripts/              # Executable Python scripts
│   └── healthcheck.py    # System verification
├── references/           # Tool capabilities, commands, API surfaces
│   ├── gws-cli.md        # Google Workspace CLI reference
│   ├── document-creation.md  # openpyxl, python-docx, python-pptx
│   ├── pdf-tools.md      # PyMuPDF, PyPDF2, pdfplumber, reportlab
│   ├── media-tools.md    # Pillow, ImageMagick, FFmpeg
│   ├── conversion-tools.md   # Pandoc
│   ├── web-parsing.md    # lxml, BeautifulSoup4
│   ├── email-reference.md    # Python MIME + Gmail CLI
│   ├── database-reference.md # MySQL MCP
│   └── setup.md          # Installation & troubleshooting
└── examples/             # Working code blocks
    ├── office-documents.md   # Excel, Word, PowerPoint
    ├── pdf-workflows.md      # PDF generation & extraction
    ├── image-processing.md   # Pillow + ImageMagick
    ├── video-audio.md        # FFmpeg
    ├── email-workflows.md    # Email composition & Gmail
    ├── database-export.md    # Database query & export
    ├── data-pipelines.md     # End-to-end workflows
    └── document-conversion.md # Pandoc conversions
```

## Naming Convention

| Folder | Pattern | Examples |
|--------|---------|----------|
| `scripts/` | `{action-noun}.py` | `healthcheck` |
| `references/` | `{tool-or-domain}.md` | `gws-cli`, `pdf-tools`, `media-tools` |
| `examples/` | `{task-focused}.md` | `office-documents`, `video-audio` |
