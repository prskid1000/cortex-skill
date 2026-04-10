# Setup Guide

Run the healthcheck to verify everything at once:

```bash
python ~/.claude/skills/claude-claw/scripts/healthcheck.py
```

---

## 1. Python Packages

| pip name | import name | Purpose |
|----------|-------------|---------|
| `openpyxl` | `openpyxl` | Excel .xlsx (cells, styles, charts, formulas) |
| `python-docx` | `docx` | Word .docx (paragraphs, tables, styles, images) |
| `python-pptx` | `pptx` | PowerPoint .pptx (slides, shapes, charts, layouts) |
| `pymupdf` | `fitz` | PDF read, render, annotate, merge, split, extract |
| `PyPDF2` | `PyPDF2` | PDF merge, split, rotate, encrypt/decrypt |
| `reportlab` | `reportlab` | Generate PDFs from scratch (layout, tables, graphics) |
| `pdfplumber` | `pdfplumber` | Extract tables and text from PDFs |
| `pillow` | `PIL` | Image manipulation (resize, crop, filters, convert) |
| `lxml` | `lxml` | XML/HTML parsing, XPath, XSLT, validation |
| `beautifulsoup4` | `bs4` | HTML/XML parsing with CSS selectors |

### Install

```bash
pip install openpyxl python-docx python-pptx pymupdf PyPDF2 reportlab pdfplumber pillow lxml beautifulsoup4
```

---

## 2. CLI Tools

| Tool | Install | Verify |
|------|---------|--------|
| `gws` | `npm install -g @anthropic/gws` | `gws --version` |
| `clickup` | Download from [releases](https://github.com/triptechtravel/clickup-cli/releases) → `~/.local/bin/` | `clickup version` |
| `git` | `winget install Git.Git` | `git --version` |
| `ffmpeg` | `winget install Gyan.FFmpeg` | `ffmpeg -version` |
| `pandoc` | `winget install JohnMacFarlane.Pandoc` | `pandoc --version` |
| `magick` | `winget install ImageMagick.ImageMagick` | `magick --version` |
| `node` | `winget install OpenJS.NodeJS` | `node --version` |
| `npx` | (comes with node) | `npx --version` |

---

## 3. Google Workspace (GWS) Auth

```bash
gws auth login           # opens browser for Google OAuth
gws auth status           # verify token
gws drive about           # test API access
```

Multiple accounts:

```bash
gws auth login --account work
gws auth login --account personal
gws --account work drive files list
```

---

## 4. MCP Servers

### MySQL

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "mcp_server_mysql": {
      "type": "stdio",
      "command": "npx",
      "args": ["@benborla29/mcp-server-mysql"],
      "env": {
        "MYSQL_HOST": "127.0.0.1",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "root",
        "MYSQL_PASS": "password",
        "MYSQL_DB": "database_name",
        "ALLOW_INSERT_OPERATION": "true",
        "ALLOW_UPDATE_OPERATION": "true",
        "ALLOW_DELETE_OPERATION": "false",
        "MULTI_DB_WRITE_MODE": "true"
      }
    }
  }
}
```

Restart Claude Code after editing.

### Chrome DevTools

Install via Claude Code plugin marketplace (`/plugin` → `chrome-devtools-plugins`). No manual config needed.

To connect to an existing browser:

```bash
start chrome --remote-debugging-port=9222 --user-data-dir="C:/tmp/debug-profile"
```

Then set plugin args to `["chrome-devtools-mcp@latest", "--browserUrl=http://127.0.0.1:9222"]`.

### ClickUp (CLI, not MCP)

```bash
clickup auth login           # interactive OAuth/API-token flow
clickup space select         # pick default workspace/space
```

---

## 5. LSP Plugins

### Step 1 — Enable plugins

In Claude Code, run `/plugin` and enable from the official marketplace:

| Plugin | Language | File types |
|--------|----------|------------|
| `pyright-lsp` | Python | `.py`, `.pyi` |
| `typescript-lsp` | TypeScript / JavaScript | `.ts`, `.tsx`, `.js`, `.jsx`, `.mts`, `.cts`, `.mjs`, `.cjs` |
| `jdtls-lsp` | Java | `.java` |
| `kotlin-lsp` | Kotlin | `.kt`, `.kts` |

### Step 2 — Install language servers

**Python & TypeScript** (npm):

```bash
npm install -g pyright typescript-language-server typescript
```

**Java (jdtls)** — requires Java 17+ JDK:

```bash
mkdir -p ~/.local/jdtls
curl -L "https://download.eclipse.org/jdtls/milestones/1.57.0/jdt-language-server-1.57.0-202602261110.tar.gz" \
  | tar xz -C ~/.local/jdtls
```

Create `~/.local/bin/jdtls.bat`:

```bat
@echo off
set JAVA_HOME=C:\Users\prith\.jdks\corretto-21.0.9
set JDTLS_HOME=%USERPROFILE%\.local\jdtls
"%JAVA_HOME%\bin\java.exe" ^
  --add-modules=ALL-SYSTEM ^
  --add-opens java.base/java.util=ALL-UNNAMED ^
  --add-opens java.base/java.lang=ALL-UNNAMED ^
  -Declipse.application=org.eclipse.jdt.ls.core.id1 ^
  -Dosgi.bundles.defaultStartLevel=4 ^
  -Declipse.product=org.eclipse.jdt.ls.core.product ^
  -Xmx1G ^
  -jar "%JDTLS_HOME%\plugins\org.eclipse.equinox.launcher_*.jar" ^
  -configuration "%JDTLS_HOME%\config_win" ^
  -data "%APPDATA%\jdtls-data" ^
  %*
```

**Kotlin** ([JetBrains/kotlin-lsp](https://github.com/Kotlin/kotlin-lsp)) — ships its own JRE:

```bash
mkdir -p ~/.local/kls-jetbrains
curl -L "https://download-cdn.jetbrains.com/kotlin-lsp/262.2310.0/kotlin-lsp-262.2310.0-win-x64.zip" \
  -o /tmp/kotlin-lsp.zip
unzip /tmp/kotlin-lsp.zip -d ~/.local/kls-jetbrains/
```

### Step 3 — Apply Windows fix

On Windows, Claude Code's LSP launcher cannot execute `.cmd`/`.bat` shims. The healthcheck auto-patches this:

```bash
python ~/.claude/skills/claude-claw/scripts/healthcheck.py
```

What it patches in `marketplace.json`:

| Server | Strategy |
|--------|----------|
| `pyright` | `node.exe` + `pyright/langserver.index.js` |
| `typescript` | `node.exe` + `typescript-language-server/lib/cli.mjs` |
| `jdtls` | `cmd.exe /d /s /c ~/.local/bin/jdtls.bat` |
| `kotlin-lsp` | Full path to `~/.local/kls-jetbrains/kotlin-lsp.cmd` |

Restart Claude Code after patching (`/reload-plugins`).

> Re-run the healthcheck after marketplace auto-updates — they overwrite these patches.

### Step 4 — Verify

Test each LSP in Claude Code:

```
LSP hover on a .py file    → function signature
LSP hover on a .ts file    → type info
LSP hover on a .java file  → method signature
LSP hover on a .kt file    → function signature
```

### CLAUDE.md integration

To enable auto-loading of the File Map and LSP-first code navigation on every conversation, add this block to your `~/.claude/CLAUDE.md`:

```markdown
**Before responding to ANY user request, ensure the claude-claw skill and its instructions are loaded into this conversation.**

Check your context for both of the following:

1. **`SKILL.md` content from the claude-claw skill** — if not visible in your context, load it by invoking: `Skill(skill: "claude-claw")`.
2. **`~/.claude/skills/claude-claw/CLAUDE.md` content** — if not visible in your context, load it by calling: `Read(file_path: "~/.claude/skills/claude-claw/CLAUDE.md")`.

Both must be loaded. If either is missing, load it FIRST before doing anything else — even for simple greetings. Invoking the skill does NOT automatically load the skill's `CLAUDE.md`; that is a separate file requiring a separate `Read` call.

Once both are loaded, they stay in context for the rest of the session — you do not need to reload them.
```

**Why both steps:** the `Skill` call loads `SKILL.md` (the File Map index) into context as a single message. The `Read` call loads this directory's `CLAUDE.md`, which contains the LSP-First Navigation rules and other usage instructions. These are **two separate files** — per the [Claude Code skills docs](https://code.claude.com/docs/en/skills), invoking a skill only loads its `SKILL.md`; the skill directory's `CLAUDE.md` is NOT auto-loaded by the Skill tool. Skipping either one means missing guidance.

**Idempotent check pattern:** the "check your context" framing ensures loads happen at most once per session. Once both files are in context after the first check, subsequent turns skip the load step because the content is already visible.

---

## 6. Notes

- **Windows MCP servers**: Do not wrap `npx` in `cmd /c` — Claude Code already does this internally.
- **jdtls**: Shows "non-project file" warnings for standalone `.java` files outside Maven/Gradle projects. Launch from the project root to avoid.
- **Config changes**: MCP and LSP configs are loaded at Claude Code startup. Always restart after edits.
