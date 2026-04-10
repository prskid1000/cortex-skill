# Installation & Troubleshooting Reference

---

## Python Packages

| pip name | import name | Purpose |
|----------|-------------|---------|
| `openpyxl` | `openpyxl` | Create/read/edit Excel .xlsx files (cells, styles, charts, formulas) |
| `python-docx` | `docx` | Create/read/edit Word .docx files (paragraphs, tables, styles, images) |
| `python-pptx` | `pptx` | Create/read/edit PowerPoint .pptx files (slides, shapes, charts, layouts) |
| `pymupdf` | `fitz` | PDF read, render, annotate, merge, split, extract text/images, page-to-image |
| `PyPDF2` | `PyPDF2` | PDF merge, split, rotate, encrypt/decrypt, extract text (simple ops) |
| `reportlab` | `reportlab` | Generate PDFs from scratch (precise layout, tables, charts, graphics) |
| `pdfplumber` | `pdfplumber` | Extract tables and text from PDFs with positional data |
| `pillow` | `PIL` | Image manipulation (resize, crop, rotate, filters, format convert, draw) |
| `lxml` | `lxml` | Fast XML/HTML parsing, XPath, XSLT, validation (XSD, RelaxNG, DTD) |
| `beautifulsoup4` | `bs4` | HTML/XML parsing with CSS selectors, tree navigation, modification |
| `pandas` | `pandas` | DataFrames for data analysis, CSV/Excel/JSON/SQL read/write |
| `matplotlib` | `matplotlib` | Charts and plots (line, bar, pie, scatter, histogram, subplots) |
| `requests` | `requests` | HTTP client (GET, POST, PUT, DELETE, sessions, auth, file upload) |
| `pyyaml` | `yaml` | Read/write YAML files |

### Install all
```bash
pip install openpyxl python-docx python-pptx pymupdf PyPDF2 reportlab pdfplumber pillow lxml beautifulsoup4 pandas matplotlib requests pyyaml
```

### Verify a package
```bash
python -c "import openpyxl; print(openpyxl.__version__)"
python -c "import fitz; print(fitz.__doc__)"
python -c "import docx; print('python-docx OK')"
```

---

## CLI Tools

| Tool | Check command | Install command (winget) | Purpose |
|------|--------------|------------------------|---------|
| `gws` | `gws --version` | `npm install -g @anthropic/gws` | Google Workspace CLI (Drive, Sheets, Docs, Slides, Gmail, Calendar) |
| `clickup` | `clickup version` | Download binary from [GitHub releases](https://github.com/triptechtravel/clickup-cli/releases) → `~/.local/bin/` | ClickUp task management (tasks, sprints, comments, time, git linking) |
| `git` | `git --version` | `winget install Git.Git` | Version control |
| `ffmpeg` | `ffmpeg -version` | `winget install Gyan.FFmpeg` | Video/audio processing, conversion, streaming |
| `pandoc` | `pandoc --version` | `winget install JohnMacFarlane.Pandoc` | Universal document converter (45+ input, 60+ output formats) |
| `magick` | `magick --version` | `winget install ImageMagick.ImageMagick` | CLI image processing (resize, convert, compose, batch) |
| `node` | `node --version` | `winget install OpenJS.NodeJS` | JavaScript runtime (required for npm-based tools) |
| `npm` | `npm --version` | (comes with node) | Package manager for JS/TS tools |

---

## MCP Servers

These MCPs are first-class `claude-claw` dependencies and are verified on every session by `scripts/healthcheck.py`. If a check fails, the healthcheck prints the exact fix to apply — it will not patch `~/.claude.json` automatically.

> **Windows note:** Do **not** manually wrap `npx` in `cmd /c` in your config. Claude Code's MCP launcher already spawns Windows MCP servers as `cmd.exe /d /s /c "npx ..."` internally. A manual wrapper causes double-wrapping.

### MySQL

Installed as a user-level MCP in `~/.claude.json` → `mcpServers.mcp_server_mysql`.

#### ~/.claude.json entry
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

#### Environment variables
| Variable | Default | Purpose |
|----------|---------|---------|
| `MYSQL_HOST` | `127.0.0.1` | Database host |
| `MYSQL_PORT` | `3306` | Database port |
| `MYSQL_USER` | `root` | Username |
| `MYSQL_PASS` | (none) | Password |
| `MYSQL_DB` | (none) | Default database |

#### Install
```bash
npm install -g @benborla29/mcp-server-mysql
```

#### Verify
```python
mcp__mcp_server_mysql__mysql_query(query="SELECT 1 AS test")
# Expected: {"column_names": ["test"], "rows": [[1]]}
```

---

### Code Review Graph (Code Analysis)

Builds a structural knowledge graph of your codebase using Tree-sitter AST parsing. 22 MCP tools for blast radius, reviews, refactoring, and architecture analysis. Full docs: `references/code-review-graph.md`.

#### Install
```bash
pip install code-review-graph
code-review-graph install --platform claude-code
code-review-graph build   # in your project directory
```

Requires Python 3.10+. Auto-configures MCP in `~/.claude.json`.

#### ~/.claude.json entry (auto-created by install)
```json
{
  "mcpServers": {
    "code-review-graph": {
      "type": "stdio",
      "command": "code-review-graph",
      "args": ["serve"]
    }
  }
}
```

#### Verify
```bash
code-review-graph status   # in a project directory after build
```

#### Update
```bash
pip install --upgrade code-review-graph
```

---

### Chrome DevTools

Installed via the `chrome-devtools-plugins` plugin marketplace, not via manual `mcpServers` config. The plugin ships its own `.mcp.json` at:

```
~/.claude/plugins/cache/chrome-devtools-plugins/chrome-devtools-mcp/latest/.mcp.json
```

Default content (do not modify — the healthcheck verifies it):
```json
{
  "chrome-devtools": {
    "command": "npx",
    "args": ["chrome-devtools-mcp@latest"]
  }
}
```

Install / update the plugin via the Claude Code plugin manager. Verify with:
```python
mcp__plugin_chrome-devtools-mcp_chrome-devtools__list_pages()
```

#### Connect to an existing browser (advanced)
If you need to drive a specific, already-running browser instance (e.g. a pre-authenticated profile, or Edge), start the browser with a remote debugging port and point the MCP at it via `--browserUrl`:
```bash
# start browser (Chrome or Edge) with remote debugging
start chrome --remote-debugging-port=9222 --user-data-dir="C:/tmp/debug-profile"
# or: start msedge --remote-debugging-port=9222 --user-data-dir="C:/tmp/debug-profile"
```
Then override the plugin `.mcp.json` args to `["chrome-devtools-mcp@latest", "--browserUrl=http://127.0.0.1:9222"]` and restart Claude Code. Note: the `-e`/`--executablePath` flag is **not** a reliable way to redirect the MCP at a non-Chrome browser — Puppeteer's launch validation falls back to a bundled Chrome if the binary isn't recognized.

---

### ClickUp (CLI, not MCP)

This skill uses the standalone `clickup` CLI (installed via the CLI Tools table above), **not** an MCP server. Authenticate with:

```bash
clickup auth login           # interactive OAuth/API-token flow
clickup space select         # pick default workspace/space
```

See `references/clickup-cli.md` for the full command surface.

---

## GWS Authentication

### Login (interactive)
```bash
gws auth login
```
Opens browser for Google OAuth. Grant requested permissions for Drive, Sheets, Docs, Slides, Gmail, Calendar.

### Verify
```bash
gws auth status
gws drive about
```

### Token refresh
Tokens auto-refresh. If expired/revoked:
```bash
gws auth logout
gws auth login
```

### Multiple accounts
```bash
gws auth login --account work
gws auth login --account personal
gws --account work drive files list
```

---

## LSP Plugins (Claude Code)

Claude Code official LSP plugins provide code intelligence (go-to-definition, hover, references) for the LSP tool. Install via the Claude Code plugin marketplace (`/plugin`).

| Plugin | Language Server | Install server | File types |
|--------|----------------|---------------|------------|
| `pyright-lsp` | `pyright-langserver` | `npm install -g pyright` | `.py`, `.pyi` |
| `typescript-lsp` | `typescript-language-server` | `npm install -g typescript-language-server typescript` | `.ts`, `.tsx`, `.js`, `.jsx`, `.mts`, `.cts`, `.mjs`, `.cjs` |
| `jdtls-lsp` | `jdtls` | See [install instructions below](#jdtls-install) | `.java` |
| `kotlin-lsp` | `kotlin-lsp` (JetBrains) | See [install instructions below](#kotlin-lsp-install) | `.kt`, `.kts` |

### jdtls install

Requires Java 17+ (JDK). Tested with Corretto 21.

```bash
# Download and extract
mkdir -p ~/.local/jdtls
curl -L "https://download.eclipse.org/jdtls/milestones/1.57.0/jdt-language-server-1.57.0-202602261110.tar.gz" \
  | tar xz -C ~/.local/jdtls

# Create launcher (Windows)
cat > ~/.local/bin/jdtls.bat << 'BATCH'
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
BATCH
```

### kotlin-lsp install

Uses [JetBrains/kotlin-lsp](https://github.com/Kotlin/kotlin-lsp) (official). Ships with its own JRE — no Java dependency needed. Much faster startup than fwcd/kotlin-language-server.

```bash
# Download and extract (Windows x64)
mkdir -p ~/.local/kls-jetbrains
curl -L "https://download-cdn.jetbrains.com/kotlin-lsp/262.2310.0/kotlin-lsp-262.2310.0-win-x64.zip" \
  -o /tmp/kotlin-lsp.zip
unzip /tmp/kotlin-lsp.zip -d ~/.local/kls-jetbrains/
```

The extracted directory contains `kotlin-lsp.cmd` — a native Windows launcher that the healthcheck patches into marketplace.json directly. No wrapper `.bat` needed.

### Windows `uv_spawn` fix

On Windows, npm-installed language servers are `.cmd`/shell shims, not native `.exe` files. Claude Code's LSP launcher uses Node.js `uv_spawn` without `shell: true`, which cannot execute shims — only Pyright happens to work out of the box.

**Fix:** Patch the marketplace.json to bypass shims:

```
~/.claude/plugins/marketplaces/claude-plugins-official/.claude-plugin/marketplace.json
```

**Node-based servers** (typescript, pyright) — point command at `node.exe` + JS entry:

```json
"command": "C:\\nvm4w\\nodejs\\node.exe",
"args": [
  "C:\\nvm4w\\nodejs\\node_modules\\typescript-language-server\\lib\\cli.mjs",
  "--stdio"
],
```

Adjust paths to match your install (`node -e "console.log(process.execPath)"` and `npm root -g`).

**Java-based servers** (jdtls, kotlin) — use `cmd.exe` to run `.bat` launcher:

```json
"command": "cmd.exe",
"args": ["/d", "/s", "/c", "C:\\Users\\prith\\.local\\bin\\jdtls.bat"],
```

> **Note:** This patch is overwritten when the marketplace auto-updates. The healthcheck (`scripts/healthcheck.py`) auto-applies it on every run.

### Known limitations

| Server | Issue | Workaround |
|--------|-------|------------|
| **Java (jdtls)** | Indexes all `.java` files under workspace root. Shows "non-project file" warnings for files outside a Maven/Gradle project. | Launch from the project root, or ignore warnings |
| **All (Windows)** | Marketplace auto-updates overwrite the `uv_spawn` patch | Run healthcheck after updates: `python ~/.claude/skills/claude-claw/scripts/healthcheck.py` |

### Verify

```bash
# In Claude Code, test with the LSP tool:
# Python
LSP hover C:/Users/prith/test.py line 1 char 5
# TypeScript
LSP hover C:/Users/prith/test.ts line 1 char 10
# Java (from a project directory)
LSP hover src/main/java/MyClass.java line 5 char 20
# Kotlin (from a project directory)
LSP hover src/main/kotlin/Main.kt line 1 char 5
```

---

## Troubleshooting

| Problem | Symptoms | Fix |
|---------|----------|-----|
| Python package not found | `ModuleNotFoundError: No module named 'xxx'` | `pip install PACKAGE_NAME` (use pip name, not import name) |
| Wrong pip/python | Package installs but still not found | Use `python -m pip install PACKAGE` to ensure correct environment |
| pymupdf import | `import fitz` fails | `pip install pymupdf` (pip name differs from import name) |
| python-docx import | `import docx` fails | `pip install python-docx` (not `docx`, which is a different package) |
| gws not found | `command not found: gws` | `npm install -g @anthropic/gws` then restart shell |
| gws auth expired | 401 errors from gws commands | `gws auth logout && gws auth login` |
| ffmpeg not found | `command not found: ffmpeg` | `winget install Gyan.FFmpeg` then restart shell |
| pandoc not found | `command not found: pandoc` | `winget install JohnMacFarlane.Pandoc` then restart shell |
| magick not found | `command not found: magick` | `winget install ImageMagick.ImageMagick` then restart shell |
| clickup not found | `command not found: clickup` | Download binary from [releases](https://github.com/triptechtravel/clickup-cli/releases) → `~/.local/bin/clickup.exe` |
| clickup auth failed | 401 or "not authenticated" | Run `clickup auth login` then `clickup space select` |
| MySQL MCP fails | Tool call returns connection error | Check MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASS in `~/.claude.json`; verify MySQL is running |
| MySQL access denied | `Access denied for user` | Verify credentials; check user grants with `SHOW GRANTS FOR 'user'@'host'` |
| MCP config change not picked up | Edited `.mcp.json` or `~/.claude.json`, tool still uses old behavior | `.mcp.json` is read once at Claude Code startup. Fully quit Claude Code (including background `node.exe` processes for the MCP server), then relaunch |
| `cmd /c` warning on an mcpServers entry | Config linter flags "Windows requires 'cmd /c' wrapper" | Ignore it — Claude Code auto-wraps `npx` on Windows (`cmd.exe /d /s /c "npx ..."`). Adding a manual wrapper causes double-wrapping |
| Chrome DevTools MCP launches Chrome instead of a custom browser | `-e` / `--executablePath` flag is ignored | Puppeteer validates the binary and falls back to bundled Chrome silently. Use `--browserUrl` against a manually started browser instead (see the "Connect to an existing browser" section above) |
| code-review-graph not found | `command not found` | `pip install code-review-graph` (requires Python 3.10+) |
| code-review-graph MCP not connecting | Tool calls fail | Check `~/.claude.json` has the entry; restart Claude Code |
| code-review-graph empty graph | No results from tools | Run `code-review-graph build` in the project directory first |
| LSP ENOENT on Windows | `uv_spawn 'typescript-language-server'` | Shim can't be spawned without shell. Run healthcheck to auto-patch marketplace.json, then restart Claude Code |
| LSP URI error on `/tmp/` | `path cannot begin with two slash characters` | Use a Windows-native path (e.g. `C:/Users/...`) instead of `/tmp/` |
| LSP not loading after patch | Still uses old command | LSP config is loaded at startup. Restart Claude Code after patching |
| npm global install fails | EACCES permission error | Run terminal as Administrator, or use `npx` instead of global install |
| PATH not updated | Tool installed but not found | Restart shell/terminal after installing CLI tools |
| Pandoc PDF fails | `pdflatex not found` | Install a LaTeX distribution (`winget install MiKTeX.MiKTeX`) or use `--pdf-engine=weasyprint` |
| Large file upload fails | Timeout on gws drive upload | Check file size; use resumable upload for files > 5MB |
| Pillow format error | Cannot identify image file | Verify file is not corrupt; check file extension matches actual format |
| openpyxl formula error | Formulas show as text | Ensure formula strings start with `=`; do not quote the formula |
| reportlab encoding | Unicode characters missing | Use a Unicode-capable font (register with `pdfmetrics.registerFont`) |
