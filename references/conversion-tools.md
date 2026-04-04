# Pandoc Conversion Reference

## Command Syntax

```
pandoc [OPTIONS] [INPUT-FILES]
pandoc input.md -o output.pdf
pandoc -f FORMAT -t FORMAT -o OUTPUT INPUT
```

---

## Input Formats (~45)

Specify with `-f FORMAT` or `--from FORMAT`.

| Format | Flag value | Notes |
|--------|-----------|-------|
| Markdown (Pandoc) | `markdown` | Pandoc-extended Markdown (default input) |
| CommonMark | `commonmark` | Strict CommonMark |
| CommonMark + ext | `commonmark_x` | CommonMark with Pandoc extensions |
| GFM | `gfm` | GitHub-Flavored Markdown |
| Markdown (strict) | `markdown_strict` | Original Markdown.pl |
| Markdown (MMD) | `markdown_mmd` | MultiMarkdown |
| Markdown (PHPExtra) | `markdown_phpextra` | PHP Markdown Extra |
| HTML | `html` | HTML4/5 |
| LaTeX | `latex` | LaTeX documents |
| DOCX | `docx` | Microsoft Word .docx |
| ODT | `odt` | OpenDocument Text |
| RTF | `rtf` | Rich Text Format |
| EPUB | `epub` | EPUB e-book |
| DocBook | `docbook` | DocBook XML |
| JATS | `jats` | Journal Article Tag Suite |
| TEI | `tei` | Text Encoding Initiative |
| reStructuredText | `rst` | Sphinx/Docutils rST |
| Org mode | `org` | Emacs Org-mode |
| MediaWiki | `mediawiki` | MediaWiki markup |
| Textile | `textile` | Textile markup |
| Creole | `creole` | Creole 1.0 wiki |
| TikiWiki | `tikiwiki` | Tiki Wiki CMS markup |
| TWiki | `twiki` | TWiki markup |
| Vimwiki | `vimwiki` | Vimwiki markup |
| DokuWiki | `dokuwiki` | DokuWiki markup |
| Djot | `djot` | Djot light markup |
| Typst | `typst` | Typst markup |
| Man page | `man` | groff man pages |
| Haddock | `haddock` | Haskell Haddock |
| Muse | `muse` | Emacs Muse |
| Jira | `jira` | Jira/Confluence wiki |
| CSV | `csv` | Comma-separated values (as table) |
| TSV | `tsv` | Tab-separated values (as table) |
| OPML | `opml` | Outline Processor Markup Language |
| BibTeX | `bibtex` | BibTeX bibliography |
| BibLaTeX | `biblatex` | BibLaTeX bibliography |
| CSL JSON | `csljson` | CSL JSON bibliography |
| CSL YAML | `cslyaml` | CSL YAML bibliography |
| RIS | `ris` | Research Info Systems |
| EndNote XML | `endnotexml` | EndNote XML bibliography |
| BITS | `bits` | BITS (Book Interchange Tag Suite) |
| CslJson | `csljson` | Citation Style Language JSON |
| fb2 | `fb2` | FictionBook2 e-book |
| ipynb | `ipynb` | Jupyter notebook |
| t2t | `t2t` | txt2tags |

---

## Output Formats (~60+)

Specify with `-t FORMAT` or `--to FORMAT`. Extension auto-detection works with `-o`.

| Format | Flag value | Typical extension |
|--------|-----------|-------------------|
| HTML5 | `html` / `html5` | .html |
| HTML4 | `html4` | .html |
| Chunked HTML | `chunkedhtml` | directory |
| PDF | `pdf` | .pdf (requires engine) |
| DOCX | `docx` | .docx |
| ODT | `odt` | .odt |
| RTF | `rtf` | .rtf |
| EPUB2 | `epub2` | .epub |
| EPUB3 | `epub` / `epub3` | .epub |
| LaTeX | `latex` | .tex |
| Beamer | `beamer` | .tex (slides) |
| ConTeXt | `context` | .tex |
| Texinfo | `texi` / `texinfo` | .texi |
| Groff man | `man` | .1 - .8 |
| Groff ms | `ms` | .ms |
| PowerPoint | `pptx` | .pptx |
| Reveal.js | `revealjs` | .html |
| Slidy | `slidy` | .html |
| DZSlides | `dzslides` | .html |
| S5 | `s5` | .html |
| Plain text | `plain` | .txt |
| ANSI terminal | `ansi` | (stdout) |
| Markdown (Pandoc) | `markdown` | .md |
| CommonMark | `commonmark` | .md |
| GFM | `gfm` | .md |
| Markdown strict | `markdown_strict` | .md |
| Markdown PHPExtra | `markdown_phpextra` | .md |
| Markdown MMD | `markdown_mmd` | .md |
| reStructuredText | `rst` | .rst |
| AsciiDoc | `asciidoc` / `asciidoctor` | .adoc |
| Org mode | `org` | .org |
| MediaWiki | `mediawiki` | .wiki |
| DokuWiki | `dokuwiki` | .txt |
| ZimWiki | `zimwiki` | .txt |
| XWiki | `xwiki` | .txt |
| Jira | `jira` | .jira |
| Textile | `textile` | .textile |
| DocBook5 | `docbook` / `docbook5` | .xml |
| DocBook4 | `docbook4` | .xml |
| JATS (archiving) | `jats` / `jats_archiving` | .xml |
| JATS (articleauthoring) | `jats_articleauthoring` | .xml |
| JATS (publishing) | `jats_publishing` | .xml |
| TEI | `tei` | .xml |
| OPML | `opml` | .opml |
| Haddock | `haddock` | .hs |
| Muse | `muse` | .muse |
| Typst | `typst` | .typ |
| Markua | `markua` | .md |
| Vimdoc | `vimdoc` | .txt |
| ICML | `icml` | .icml (InDesign) |
| FB2 | `fb2` | .fb2 |
| ipynb | `ipynb` | .ipynb |
| BibTeX | `bibtex` | .bib |
| BibLaTeX | `biblatex` | .bib |
| CSL JSON | `csljson` | .json |
| CSL YAML | `cslyaml` | .yaml |

---

## Templates

### Use a template
```
pandoc --template=mytemplate.tex -o output.pdf input.md
pandoc --print-default-template=html > default.html
```

### Template syntax
| Syntax | Purpose |
|--------|---------|
| `$variable$` | Insert variable value |
| `$for(variable)$...$endfor$` | Loop over list variable |
| `$if(variable)$...$endif$` | Conditional |
| `$if(variable)$...$else$...$endif$` | Conditional with else |
| `$if(variable)$...$elseif(var2)$...$endif$` | Chained conditionals |
| `$partial("file.tmpl")$` | Include partial template |
| `$variable/uppercase$` | Pipe function (uppercase) |
| `$variable/lowercase$` | Pipe function (lowercase) |
| `$variable/pairs$` | Iterate key-value pairs |
| `$variable/first$` | First item of list |
| `$variable/last$` | Last item of list |
| `$variable/rest$` | All but first |
| `$variable/allbutlast$` | All but last |
| `$variable/length$` | Length of list |
| `$~` / `~$` | Strip whitespace (left/right) |

### Template variables (common)
`title`, `author`, `date`, `lang`, `dir`, `header-includes`, `toc`, `toc-title`, `body`, `include-before`, `include-after`, `highlighting-css`, `css`, `math`, `documentclass`, `classoption`, `geometry`, `fontsize`, `mainfont`, `monofont`

---

## Reference Documents

Use a styled document as template for formatting:

```
pandoc --reference-doc=template.docx -o output.docx input.md
pandoc --reference-doc=template.pptx -o output.pptx input.md
pandoc --reference-doc=template.odt -o output.odt input.md
```

Create a default reference doc to customize:
```
pandoc -o custom-reference.docx --print-default-data-file reference.docx
pandoc -o custom-reference.pptx --print-default-data-file reference.pptx
```

---

## Table of Contents

| Flag | Purpose |
|------|---------|
| `--toc` | Generate table of contents |
| `--toc-depth=N` | Heading depth to include (default: 3) |
| `--number-sections` | Number section headings |
| `--shift-heading-level-by=N` | Shift all headings by N levels |

---

## Bibliography / Citations

```
pandoc --citeproc --bibliography=refs.bib -o output.pdf input.md
pandoc --citeproc --csl=ieee.csl --bibliography=refs.bib input.md -o out.pdf
```

| Flag | Purpose |
|------|---------|
| `--citeproc` | Process citations (replaces pandoc-citeproc filter) |
| `--bibliography=FILE` | BibTeX (.bib), BibLaTeX, CSL JSON/YAML, RIS, EndNote XML |
| `--csl=FILE` | Citation Style Language style file |
| `--citation-abbreviations=FILE` | Journal abbreviation database |
| `--natbib` | Use natbib for LaTeX output (instead of citeproc) |
| `--biblatex` | Use biblatex for LaTeX output |

Cite in Markdown: `[@key]`, `[@key, p. 10]`, `[-@key]` (suppress author), `@key` (in-text)

---

## Math Rendering

| Flag | Rendering method |
|------|-----------------|
| `--mathjax[=URL]` | MathJax (default for HTML) |
| `--katex[=URL]` | KaTeX (faster, less complete) |
| `--mathml` | Native MathML |
| `--webtex[=URL]` | External image service |
| `--gladtex` | GladTeX preprocessor |
| (LaTeX output) | Native LaTeX math (no flag needed) |

---

## Syntax Highlighting

```
pandoc --highlight-style=pygments input.md -o output.html
pandoc --list-highlight-styles
pandoc --print-highlight-style=pygments > my-style.theme
pandoc --highlight-style=my-style.theme input.md -o output.html
```

### Built-in styles
`pygments` (default), `kate`, `breezedark`, `espresso`, `haddock`, `monochrome`, `tango`, `zenburn`

| Flag | Purpose |
|------|---------|
| `--highlight-style=STYLE` | Set style (name or .theme JSON file) |
| `--no-highlight` | Disable syntax highlighting |
| `--syntax-definition=FILE` | Custom KDE-style syntax XML |
| `--list-highlight-languages` | List supported languages |

---

## Filters

### Lua filters (recommended, built-in)
```
pandoc --lua-filter=filter.lua input.md -o output.pdf
```

### JSON filters
```
pandoc --filter=pandoc-crossref input.md -o output.pdf
```

### pandoc-crossref
Cross-referencing for figures, tables, equations, sections:
```
pandoc --filter pandoc-crossref --citeproc input.md -o output.pdf
```
Always place `--filter pandoc-crossref` BEFORE `--citeproc`.

### Filter execution order
Filters run left-to-right in command-line order. Lua filters and JSON filters can be intermixed.

---

## PDF Engines

Specify with `--pdf-engine=ENGINE`:

| Engine | Type | Install |
|--------|------|---------|
| `pdflatex` | LaTeX (default) | TeX Live / MiKTeX |
| `xelatex` | LaTeX (Unicode fonts) | TeX Live / MiKTeX |
| `lualatex` | LaTeX (Lua scripting) | TeX Live / MiKTeX |
| `tectonic` | LaTeX (self-contained) | `winget install tectonic` |
| `latexmk` | LaTeX (auto-compile) | TeX Live / MiKTeX |
| `context` | ConTeXt | ConTeXt standalone |
| `weasyprint` | HTML-to-PDF | `pip install weasyprint` |
| `prince` | HTML-to-PDF | prince installer |
| `wkhtmltopdf` | HTML-to-PDF (WebKit) | `winget install wkhtmltopdf` |
| `pagedjs-cli` | HTML-to-PDF (Paged.js) | `npm install -g pagedjs-cli` |
| `pdfroff` | groff-to-PDF | groff |
| `typst` | Typst | `winget install typst` |

Pass engine options:
```
pandoc --pdf-engine=xelatex --pdf-engine-opt=-shell-escape input.md -o out.pdf
```

---

## Slide Shows

### Reveal.js
```
pandoc -t revealjs -s -o slides.html input.md
pandoc -t revealjs -s -V revealjs-url=https://unpkg.com/reveal.js/ -o slides.html input.md
pandoc -t revealjs -s -V theme=moon -o slides.html input.md
```
Themes: `beige`, `black`, `blood`, `league`, `moon`, `night`, `serif`, `simple`, `sky`, `solarized`, `white`

### Beamer (LaTeX PDF slides)
```
pandoc -t beamer -o slides.pdf input.md
pandoc -t beamer -V theme=Madrid -V colortheme=dolphin -o slides.pdf input.md
```
Themes: `default`, `AnnArbor`, `Berlin`, `Copenhagen`, `Darmstadt`, `Frankfurt`, `Madrid`, `Montpellier`, `Singapore`, `Warsaw`, etc.

### PowerPoint
```
pandoc -o slides.pptx input.md
pandoc --reference-doc=template.pptx -o slides.pptx input.md
```

### Slidy / DZSlides / S5
```
pandoc -t slidy -s -o slides.html input.md
pandoc -t dzslides -s -o slides.html input.md
pandoc -t s5 -s -o slides.html input.md
```

Slide separation: `---` (horizontal rule) or heading level set by `--slide-level=N`.

---

## EPUB Creation

```
pandoc -o book.epub input.md
pandoc --epub-cover-image=cover.jpg --epub-metadata=metadata.xml -o book.epub input.md
```

| Flag | Purpose |
|------|---------|
| `--epub-cover-image=FILE` | Cover image (JPG/PNG) |
| `--epub-metadata=FILE` | Dublin Core metadata XML |
| `--epub-stylesheet=FILE` | Custom CSS for EPUB |
| `--epub-embed-font=FILE` | Embed font (repeat for multiple) |
| `--epub-chapter-level=N` | Split into chapters at heading level N (default: 1) |
| `--epub-subdirectory=DIR` | Subdirectory for EPUB internals |
| `-t epub2` / `-t epub3` | EPUB version (default: epub3) |

---

## Key CLI Flags

| Flag | Purpose |
|------|---------|
| `-s` / `--standalone` | Produce full document (not fragment) |
| `--embed-resources` | Embed images, CSS, JS into single file (replaces `--self-contained`) |
| `--self-contained` | Legacy alias for `--embed-resources --standalone` |
| `--wrap=auto\|none\|preserve` | Line wrapping mode |
| `--columns=N` | Column width for wrapping (default: 72) |
| `--tab-stop=N` | Tab stop width (default: 4) |
| `--extract-media=DIR` | Extract media to directory |
| `--resource-path=DIRS` | Search paths for resources (separated by `:` or `;`) |
| `--data-dir=DIR` | Custom data directory |
| `--defaults=FILE` | YAML defaults file |
| `--verbose` | Verbose output |
| `--quiet` | Suppress warnings |
| `--fail-if-warnings` | Exit with error on warnings |
| `--log=FILE` | Write JSON log |
| `--list-input-formats` | List all input formats |
| `--list-output-formats` | List all output formats |
| `--list-extensions[=FORMAT]` | List extensions for format |
| `--strip-comments` | Strip HTML comments |
| `--ascii` | ASCII-only output |
| `--trace` | Debug: trace document transformations |

---

## Extensions System

Enable/disable per format:
```
pandoc -f markdown+hard_line_breaks-smart -o output.html input.md
pandoc -f gfm+footnotes input.md -o output.html
```

### Key extensions
| Extension | Default on | Purpose |
|-----------|-----------|---------|
| `smart` | markdown | Typographic quotes, dashes, ellipses |
| `auto_identifiers` | markdown | Auto-generate heading IDs |
| `pipe_tables` | markdown, gfm | Pipe-style tables |
| `grid_tables` | markdown | Grid-style tables |
| `multiline_tables` | markdown | Multiline tables |
| `table_captions` | markdown | Table captions |
| `footnotes` | markdown | `[^fn]` footnotes |
| `inline_notes` | markdown | `^[inline note]` |
| `citations` | markdown | `[@cite]` syntax |
| `yaml_metadata_block` | markdown | YAML front matter |
| `fenced_code_blocks` | markdown, gfm | Triple-backtick code blocks |
| `fenced_code_attributes` | markdown | `{.language #id .class}` |
| `backtick_code_blocks` | markdown | Backtick code |
| `definition_lists` | markdown | Definition lists |
| `task_lists` | gfm | `- [x]` checkboxes |
| `strikeout` | markdown, gfm | `~~text~~` |
| `superscript` | markdown | `^text^` |
| `subscript` | markdown | `~text~` |
| `tex_math_dollars` | markdown | `$...$` and `$$...$$` |
| `raw_html` | markdown, gfm | Pass through raw HTML |
| `raw_tex` | markdown | Pass through raw LaTeX |
| `hard_line_breaks` | (off) | Treat newlines as `<br>` |
| `emoji` | gfm | `:emoji:` shortcodes |
| `implicit_figures` | markdown | Solo image in paragraph becomes figure |
| `link_attributes` | markdown | `[text](url){.class}` |
| `header_attributes` | markdown | `# Heading {#id .class}` |
| `fenced_divs` | markdown | `:::` div blocks |
| `bracketed_spans` | markdown | `[text]{.class}` |
| `native_divs` | markdown | `<div>` becomes Div |
| `native_spans` | markdown | `<span>` becomes Span |
| `abbreviations` | (off) | `*[abbr]: expansion` |
| `lists_without_preceding_blankline` | (off) | Lists without blank line before |

List all extensions: `pandoc --list-extensions=markdown`

---

## Custom Readers / Writers

Write in Lua, invoke with:
```
pandoc -f custom-reader.lua -t html input.txt
pandoc -f markdown -t custom-writer.lua input.md
```

### Reader skeleton
```lua
function Reader(input, opts)
  return pandoc.Pandoc({pandoc.Para({pandoc.Str(tostring(input))})})
end
```

### Writer skeleton
```lua
function Writer(doc, opts)
  local output = {}
  for _, block in ipairs(doc.blocks) do
    table.insert(output, pandoc.utils.stringify(block))
  end
  return table.concat(output, "\n")
end
```

---

## Metadata

### YAML block in document
```yaml
---
title: My Document
author:
  - First Author
  - Second Author
date: 2025-01-15
lang: en-US
---
```

### CLI metadata
```
pandoc --metadata title="My Doc" --metadata author="Author" input.md -o out.pdf
pandoc --metadata-file=meta.yaml input.md -o out.pdf
```

---

## Include Files

| Flag | Inserts at |
|------|-----------|
| `--include-in-header=FILE` | End of `<head>` (HTML) or preamble (LaTeX) |
| `--include-before-body=FILE` | Beginning of `<body>` (HTML) or after `\begin{document}` |
| `--include-after-body=FILE` | End of `<body>` (HTML) or before `\end{document}` |

Repeat flags to include multiple files (inserted in order).

---

## Defaults Files

YAML file combining all CLI options:
```yaml
# defaults.yaml
from: markdown
to: pdf
output-file: output.pdf
pdf-engine: xelatex
standalone: true
toc: true
toc-depth: 2
number-sections: true
highlight-style: kate
variables:
  geometry: margin=1in
  fontsize: 12pt
  mainfont: "Segoe UI"
metadata:
  title: "Document Title"
  author: "Author Name"
filters:
  - pandoc-crossref
  - citeproc
bibliography: refs.bib
csl: ieee.csl
```

Invoke: `pandoc --defaults=defaults.yaml input.md`
