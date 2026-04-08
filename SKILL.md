---
name: claude-claw
description: >
  Reference guide for documents, spreadsheets, presentations, PDFs, images, video, audio,
  Google Workspace, ClickUp, MySQL, and media processing.
---

# Claude Claw — Productivity OS

## Bootstrap

```bash
python ~/.claude/skills/claude-claw/scripts/healthcheck.py
```

## Workflow

`Source -> Transform (Python) -> Output (/tmp/) -> Deliver (gws)`

## References

| Topic | File |
|-------|------|
| Google Workspace CLI | [references/gws-cli.md](references/gws-cli.md) |
| Excel / Word / PowerPoint | [references/document-creation.md](references/document-creation.md) |
| PDF tools | [references/pdf-tools.md](references/pdf-tools.md) |
| Image / Video / Audio | [references/media-tools.md](references/media-tools.md) |
| Document conversion | [references/conversion-tools.md](references/conversion-tools.md) |
| HTML/XML parsing | [references/web-parsing.md](references/web-parsing.md) |
| Email / MIME | [references/email-reference.md](references/email-reference.md) |
| ClickUp CLI | [references/clickup-cli.md](references/clickup-cli.md) |
| Claude Code patcher | [references/claude-patcher.md](references/claude-patcher.md) |
| Install / troubleshoot | [references/setup.md](references/setup.md) |

## Examples

| Task | File |
|------|------|
| Excel / Word / PPT | [examples/office-documents.md](examples/office-documents.md) |
| PDF workflows | [examples/pdf-workflows.md](examples/pdf-workflows.md) |
| Image processing | [examples/image-processing.md](examples/image-processing.md) |
| Video / audio | [examples/video-audio.md](examples/video-audio.md) |
| Email workflows | [examples/email-workflows.md](examples/email-workflows.md) |
| Data pipelines | [examples/data-pipelines.md](examples/data-pipelines.md) |
| Document conversion | [examples/document-conversion.md](examples/document-conversion.md) |
| ClickUp workflows | [examples/clickup-workflows.md](examples/clickup-workflows.md) |

## Scripts

| Script | Purpose |
|--------|---------|
| [scripts/healthcheck.py](scripts/healthcheck.py) | Verify packages, CLI tools, MCP servers, and skill structure |
| [scripts/claude-patcher.js](scripts/claude-patcher.js) | Claude Code binary patcher |
