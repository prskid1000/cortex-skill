# Claude Claw

Reference guide for Claude Code — documents, media, Google Workspace, ClickUp, and MySQL.

## Install

```bash
git clone https://github.com/prskid1000/claude-claw-skill.git ~/.claude/skills/claude-claw
```

## Quick Start

```bash
/claude-claw
python ~/.claude/skills/claude-claw/scripts/healthcheck.py
```

## Structure

```
claude-claw/
├── SKILL.md                    # Skill index (always loaded)
├── README.md
├── scripts/
│   ├── healthcheck.py          # System verification
│   └── claude-patcher.js       # Claude Code binary patcher
├── references/
│   ├── gws-cli.md              # Google Workspace CLI
│   ├── document-creation.md    # openpyxl, python-docx, python-pptx
│   ├── pdf-tools.md            # PyMuPDF, PyPDF2, pdfplumber, reportlab
│   ├── media-tools.md          # Pillow, ImageMagick, FFmpeg
│   ├── conversion-tools.md     # Pandoc
│   ├── web-parsing.md          # lxml, BeautifulSoup4
│   ├── email-reference.md      # Python MIME + Gmail CLI
│   ├── clickup-cli.md          # ClickUp CLI
│   ├── claude-patcher.md       # Claude Code binary patcher
│   └── setup.md                # Installation & troubleshooting
└── examples/
    ├── office-documents.md
    ├── pdf-workflows.md
    ├── image-processing.md
    ├── video-audio.md
    ├── email-workflows.md
    ├── data-pipelines.md
    ├── document-conversion.md
    └── clickup-workflows.md
```
