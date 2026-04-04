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
| `git` | `git --version` | `winget install Git.Git` | Version control |
| `ffmpeg` | `ffmpeg -version` | `winget install Gyan.FFmpeg` | Video/audio processing, conversion, streaming |
| `pandoc` | `pandoc --version` | `winget install JohnMacFarlane.Pandoc` | Universal document converter (45+ input, 60+ output formats) |
| `magick` | `magick --version` | `winget install ImageMagick.ImageMagick` | CLI image processing (resize, convert, compose, batch) |
| `node` | `node --version` | `winget install OpenJS.NodeJS` | JavaScript runtime (required for npm-based tools) |
| `npm` | `npm --version` | (comes with node) | Package manager for JS/TS tools |

---

## MCP Servers

### MySQL

#### settings.json config
```json
{
  "mcpServers": {
    "mcp-server-mysql": {
      "command": "npx",
      "args": ["-y", "@benborla29/mcp-server-mysql"],
      "env": {
        "MYSQL_HOST": "127.0.0.1",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "root",
        "MYSQL_PASS": "password",
        "MYSQL_DB": "database_name"
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

### Chrome DevTools (Edge)

#### settings.json config
```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "@anthropic/chrome-devtools-mcp@latest"]
    }
  }
}
```

#### Launch Edge with remote debugging
```bash
start msedge --remote-debugging-port=9222 --user-data-dir="C:/tmp/edge-debug"
```

Always use Microsoft Edge, not Chrome. The `--remote-debugging-port=9222` flag enables DevTools Protocol access.

---

### ClickUp

#### settings.json config
```json
{
  "mcpServers": {
    "clickup": {
      "command": "npx",
      "args": ["-y", "@anthropic/clickup-mcp@latest"],
      "env": {
        "CLICKUP_API_TOKEN": "pk_..."
      }
    }
  }
}
```

#### API Token
Obtain from ClickUp: Settings > Apps > API Token. Store in the `CLICKUP_API_TOKEN` env var.

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
| MySQL MCP fails | Tool call returns connection error | Check MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASS in settings.json; verify MySQL is running |
| MySQL access denied | `Access denied for user` | Verify credentials; check user grants with `SHOW GRANTS FOR 'user'@'host'` |
| Chrome DevTools MCP fails | Cannot connect to browser | Launch Edge with `--remote-debugging-port=9222`; verify port not blocked |
| Edge already running | DevTools port conflict | Close all Edge instances first, then relaunch with debug flag |
| npm global install fails | EACCES permission error | Run terminal as Administrator, or use `npx` instead of global install |
| PATH not updated | Tool installed but not found | Restart shell/terminal after installing CLI tools |
| Pandoc PDF fails | `pdflatex not found` | Install a LaTeX distribution (`winget install MiKTeX.MiKTeX`) or use `--pdf-engine=weasyprint` |
| Large file upload fails | Timeout on gws drive upload | Check file size; use resumable upload for files > 5MB |
| Pillow format error | Cannot identify image file | Verify file is not corrupt; check file extension matches actual format |
| openpyxl formula error | Formulas show as text | Ensure formula strings start with `=`; do not quote the formula |
| reportlab encoding | Unicode characters missing | Use a Unicode-capable font (register with `pdfmetrics.registerFont`) |
