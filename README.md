# Claude Claw

A Claude Code skill that turns Claude into a productivity OS — a single library for working with documents (Excel, Word, PowerPoint, PDF), images, video/audio, Google Workspace, ClickUp, MySQL, email composition, and document conversion.

> **For agents:** start at [SKILL.md](SKILL.md) — it has the full file map with direct links to every section in every reference and example file.

## What's Inside

| Folder | Contents | Total |
|--------|----------|-------|
| [`references/claw/`](references/claw/) | `claw` CLI per-noun reference — primary entry point | 17 noun docs ([xlsx](references/claw/xlsx.md), [docx](references/claw/docx.md), [pptx](references/claw/pptx.md), [pdf](references/claw/pdf.md), [img](references/claw/img.md), [media](references/claw/media.md), [convert](references/claw/convert.md), [email](references/claw/email.md), [doc](references/claw/doc.md), [sheet](references/claw/sheet.md), [web](references/claw/web.md), [html](references/claw/html.md), [xml](references/claw/xml.md), [browser](references/claw/browser.md), [pipeline](references/claw/pipeline.md), [doctor](references/claw/doctor.md), [completion](references/claw/completion.md)) + [README](references/claw/README.md) |
| [`references/`](references/) (library-level) | Escape-hatch API docs — use when `claw` isn't enough | 3 tool refs (`gws-cli`, `clickup-cli`, `claude-customization`) + 5 patcher refs |
| [`examples/`](examples/) | Copy-paste runnable workflows | 3 files: [`claw-recipes.md`](examples/claw-recipes.md) (one-liners), [`claw-pipelines.md`](examples/claw-pipelines.md) (YAML recipes), [`clickup-workflows.md`](examples/clickup-workflows.md) |
| [`scripts/`](scripts/) | Healthcheck + launch wrappers + patchers for third-party apps (plus the [`claw`](scripts/claw/) CLI package itself) | [healthcheck](scripts/healthcheck.py), 4 wrappers, 4 patchers |

**Tools covered:** openpyxl · python-docx · python-pptx · PyMuPDF · PyPDF2 · pdfplumber · reportlab · Pillow · ImageMagick · FFmpeg · Pandoc · lxml · BeautifulSoup4 · gws (Google Workspace) · clickup · MIME/Gmail.

## Install

```bash
git clone https://github.com/prskid1000/claude-claw-skill.git ~/.claude/skills/claude-claw
python ~/.claude/skills/claude-claw/scripts/healthcheck.py
```

The healthcheck verifies all dependencies and auto-fixes Windows LSP issues.

## Activate in Claude Code

The skill auto-loads when Claude detects a relevant task (creating a document, sending email, working with Google Workspace, etc.). To force-activate, mention `claude-claw` in your prompt or invoke `/claude-claw`.

## Optional: LSP-First Code Navigation + Auto-Load

To auto-load the File Map and LSP-first code-navigation rules on every conversation, install the canonical block into your global `~/.claude/CLAUDE.md` via the markdown section patcher:

```bash
python ~/.claude/skills/claude-claw/scripts/patchers/md-section-patcher.py apply \
  --target ~/.claude/CLAUDE.md \
  --section claude-claw \
  --source ~/.claude/skills/claude-claw/references/patchers/claude-md-block.md
```

The block is wrapped in `<!-- claude-claw:begin -->` / `<!-- claude-claw:end -->` markers and prepended to the top of your file; re-runs are idempotent. See [references/patchers/md-section-patcher.md](references/patchers/md-section-patcher.md) for details. The full install — packages, CLI tools, MCP config, this block — is automated by `python scripts/healthcheck.py --install`.

## Structure

```
claude-claw/
├── SKILL.md                    # File map index (auto-loaded into Claude's context)
├── README.md                   # This file
├── scripts/
│   ├── healthcheck.py          # Verify all deps + auto-fix Windows LSP
│   ├── _TEMPLATE.py            # Template for new scripts
│   ├── patchers/               # Binary/config patchers for third-party apps
│   │   ├── claude-patcher.js       # Claude Code binary patcher (context/output)
│   │   ├── claude-desktop-3p.py    # Claude Desktop 3P/BYOM registry toggle
│   │   ├── lm-studio-white-tray.py # LM Studio tray-icon whitener
│   │   └── md-section-patcher.py   # Idempotent markdown-section injector
│   └── wrappers/               # Local-model launch wrappers (codel / claudel / claudedl / codexl)
├── references/
│   ├── _TEMPLATE.md                 # Template for new reference files
│   ├── claw/                        # claw CLI per-noun reference (primary entry point)
│   │   ├── README.md                    # install, global flags, help UX, exit codes
│   │   ├── xlsx.md | docx.md | pptx.md | pdf.md
│   │   ├── img.md | media.md | convert.md
│   │   ├── email.md | doc.md | sheet.md
│   │   ├── web.md | html.md | xml.md | browser.md
│   │   ├── pipeline.md | doctor.md | completion.md
│   ├── gws-cli.md                   # Google Workspace CLI (escape hatch)
│   ├── clickup-cli.md               # ClickUp CLI
│   ├── claude-customization.md      # Launch wrappers + patcher overview
│   ├── patchers/                    # Per-patcher reference docs
│   │   ├── claude-patcher.md            # Claude Code binary patcher
│   │   ├── claude-desktop-3p.md         # Claude Desktop 3P registry toggle
│   │   ├── lm-studio-white-tray.md      # LM Studio tray-icon whitener
│   │   ├── md-section-patcher.md        # Idempotent markdown-section injector
│   │   └── claude-md-block.md           # Canonical block injected into ~/.claude/CLAUDE.md
│   # install via `python scripts/healthcheck.py --install` — no separate setup.md
└── examples/
    ├── _TEMPLATE.md                 # Template for new example files
    ├── claw-recipes.md              # claw one-liners, keyed by user intent
    ├── claw-pipelines.md            # claw pipeline YAML recipes
    └── clickup-workflows.md         # Task management workflows (CLI, not wrapped)
```

## Adding New Files

Templates are provided in `references/_TEMPLATE.md` and `examples/_TEMPLATE.md`. To add a new reference or example:

1. Copy the template into the appropriate folder
2. Replace placeholders
3. Add a link in [SKILL.md](SKILL.md) under the matching section
4. If it needs new dependencies, add them to `scripts/claw/pyproject.toml` extras and to the `PACKAGES` / `CLI_TOOLS` lists in `scripts/healthcheck.py`

## Healthcheck

Run anytime to verify everything is set up:

```bash
python ~/.claude/skills/claude-claw/scripts/healthcheck.py
```

Checks: Python packages · CLI tools · Google Workspace auth · MCP servers (MySQL, Chrome DevTools) · LSP plugins (Pyright, TypeScript, jdtls, Kotlin). Auto-fixes the Windows LSP `uv_spawn` issue.

## License

MIT
