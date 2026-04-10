# Claude Claw — CLAUDE.md

Copy these sections into your `~/.claude/CLAUDE.md` to always auto-load the claude-claw skill and enable LSP-first code navigation.

---

## Claude Claw — Always Available

The `claude-claw` skill at `~/.claude/skills/claude-claw/SKILL.md` is the canonical reference for documents (Excel, Word, PowerPoint, PDF), images, video/audio, Google Workspace, ClickUp, MIME/email composition, and Pandoc conversion.

**Always read [SKILL.md](skills/claude-claw/SKILL.md) at the start of any task involving:**

- Creating, reading, editing, or converting documents (`.xlsx`, `.docx`, `.pptx`, `.pdf`, Markdown, HTML, EPUB)
- Image processing (Pillow, ImageMagick)
- Video / audio processing (FFmpeg)
- Google Workspace operations (Drive, Sheets, Docs, Slides, Gmail, Calendar, Tasks)
- Composing or sending email (MIME, Gmail)
- ClickUp task management
- Querying MySQL via MCP
- Pandoc document conversion
- Web scraping or HTML/XML parsing (lxml, BeautifulSoup4)

SKILL.md contains a File Map with direct links to every section in every reference and example file. Follow links to load only the sections you need — avoid reading whole reference files (some are 60KB+).

---

## LSP-First Code Navigation

When working on coding tasks in supported languages (Python, TypeScript/JavaScript, Java, Kotlin), use the LSP tool as your primary source of code intelligence before falling back to Grep, Glob, or file reads.

### Prefer LSP for

- **Finding definitions**: `goToDefinition` instead of grepping for function/class names
- **Finding usages**: `findReferences` instead of grepping for symbol names
- **Understanding structure**: `documentSymbol` to map a file's classes, methods, and fields
- **Type information**: `hover` to get type signatures and documentation
- **Call chains**: `incomingCalls` / `outgoingCalls` to trace execution flow
- **Implementations**: `goToImplementation` to find concrete implementations of interfaces

### Fall back to Grep/Glob when

- The file type has no LSP server (e.g. YAML, Markdown, shell scripts)
- You need to search across file contents for strings, not symbols (log messages, config keys)
- LSP returns no results (symbol may be dynamically generated or in an unindexed file)
