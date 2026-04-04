# Claude Claw

Productivity OS for Claude Code — document creation, tool orchestration, and automation.

## Quick Start

```bash
# Invoke the skill
/claude-claw

# Run healthcheck
python ~/.claude/skills/claude-claw/scripts/healthcheck.py
```

## Structure

```
claude-claw/
├── SKILL.md              # Skill entry point (lean, always loaded)
├── README.md             # This file
├── scripts/              # Executable Python scripts
│   └── healthcheck.py    # System verification
├── references/           # Tool capabilities, commands, API surfaces
│   ├── gws-cli.md        # Google Workspace CLI
│   ├── document-creation.md  # openpyxl, python-docx, python-pptx
│   ├── pdf-tools.md      # PyMuPDF, PyPDF2, pdfplumber, reportlab
│   ├── media-tools.md    # Pillow, ImageMagick, FFmpeg
│   ├── conversion-tools.md   # Pandoc
│   ├── web-parsing.md    # lxml, BeautifulSoup4
│   ├── email-reference.md    # Python MIME + Gmail CLI
│   ├── database-reference.md # MySQL MCP
│   ├── clickup-cli.md     # ClickUp CLI
│   └── setup.md          # Installation & troubleshooting
└── examples/             # Working code blocks
    ├── office-documents.md
    ├── pdf-workflows.md
    ├── image-processing.md
    ├── video-audio.md
    ├── email-workflows.md
    ├── database-export.md
    ├── data-pipelines.md
    ├── document-conversion.md
    └── clickup-workflows.md
```
