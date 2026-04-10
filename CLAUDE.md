# Claude Claw — User Instructions

> Copy this entire file's content into your `~/.claude/CLAUDE.md`.

- [Auto-Load Skill](#auto-load-skill) · [LSP-First Navigation](#lsp-first-navigation)

## Auto-Load Skill

- **First action of every conversation:** read `~/.claude/skills/claude-claw/SKILL.md`
  - Unconditional — read on every message regardless of topic, even simple greetings
  - SKILL.md is small (File Map index only) — fast to load
  - Gives you the index needed to find detailed references and examples
- **After loading SKILL.md:**
  - Follow direct links inside it to load only specific sections
  - Never read whole reference files (some are 60KB+)
  - Match the user's task to a category in the File Map, then jump to the linked section

## LSP-First Navigation

When working on code in Python, TypeScript/JavaScript, Java, or Kotlin, use the LSP tool as your primary source of code intelligence before falling back to Grep, Glob, or file reads.

- **Prefer LSP for:**
  - Finding definitions — `goToDefinition` instead of grepping for function/class names
  - Finding usages — `findReferences` instead of grepping for symbol names
  - Understanding structure — `documentSymbol` to map a file's classes, methods, fields
  - Type information — `hover` for type signatures and documentation
  - Call chains — `incomingCalls` / `outgoingCalls` to trace execution flow
  - Implementations — `goToImplementation` for concrete implementations of interfaces
- **Fall back to Grep/Glob when:**
  - File type has no LSP server (YAML, Markdown, shell scripts)
  - Searching for strings in file contents, not symbols (log messages, config keys)
  - LSP returns no results (symbol may be dynamically generated or in an unindexed file)
