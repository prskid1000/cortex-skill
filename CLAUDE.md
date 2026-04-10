# Claude Claw — User Instructions

> Loaded automatically by `~/.claude/CLAUDE.md` via a direct `Read` call — do not copy-paste this file's contents.

## Working With the Skill

- **After SKILL.md is loaded** (via the parent `Skill(claude-claw)` call):
  - Follow direct links inside SKILL.md to load only specific sections
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
