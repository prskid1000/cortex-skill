# `claw xml` — XPath / XSLT / Schema Reference

> Source directory: [scripts/claw/src/claw/xml/](../../scripts/claw/src/claw/xml/)

CLI wrapper around `lxml`. Covers XPath queries, XSLT transforms, schema validation (XSD / RelaxNG / DTD), canonicalization (C14N), streaming iteration for giant XML, and JSON conversion.

Library API for escape hatches: see [When `claw xml` Isn't Enough](#when-claw-xml-isnt-enough).

## Contents

- **QUERY with XPath**
  - [XPath (parameterized — no injection)](#11-xpath)
- **TRANSFORM with XSLT**
  - [XSLT 1.0 transform](#21-xslt)
- **VALIDATE against schema**
  - [XSD / RelaxNG / DTD](#31-validate)
- **CANONICALIZE (C14N)**
  - [C14N / C14N 2.0 for XML signatures](#41-canonicalize)
- **FORMAT output**
  - [Indent / sort attrs / pretty-print](#51-fmt)
- **STREAM large files**
  - [iterparse with XPath filter](#61-stream-xpath)
- **CONVERT to JSON**
  - [Lossless or objectify-style JSON](#71-to-json)
- **When `claw xml` isn't enough** — [escape hatches](#when-claw-xml-isnt-enough)

---

## Critical Rules

1. **XXE-safe by default** — the default parser runs with `resolve_entities=False`, `no_network=True`, `huge_tree=False`. External DTDs and SYSTEM entities are NOT fetched or expanded. Override explicitly with `--allow-entities` / `--allow-network` / `--huge-tree`; never do this on attacker-controlled XML.
2. **Parameterized XPath** — `--var NAME=VALUE` binds variables into the query so you never string-interpolate user input. `//item[@id=$id]` with `--var id=42` is safe; `//item[@id='$id']` is broken (literal string) and f-string interpolation is dangerous. `claw xml xpath` rejects queries that contain unbound `$` variables unless `--allow-undeclared-vars` is passed.
3. **Stdin / stdout glue** — pass `-` as the positional file to read from stdin. `--out -` (default) writes to stdout. Enables: `curl URL | claw xml xpath - "//price" --json`.
4. **Structured output** — every verb supports `--json`. `xpath` emits NDJSON (one hit per line); `validate` emits `{valid: bool, errors: [...]}`. Errors under `--json` emit `{error, code, hint, doc_url}` to stderr.
5. **Exit codes** — `0` success (validation: schema-conformant), `1` generic, `2` usage error, `3` partial (multi-file validate: some failed), `4` bad input (malformed XML), `5` system error, `6` validation failure (schema-non-conformant), `130` SIGINT.
6. **Help** — `claw xml --help`, `claw xml <verb> --help`, `--examples` prints runnable recipes, `--progress=json` streams one NDJSON line per top-level element during `stream-xpath`.
7. **Namespaces** — pass `--ns PREFIX=URI` (repeatable) to declare namespaces used in the XPath. Without this, `//ns:foo` queries against namespaced docs silently return zero hits.
8. **Common output flags** — every mutating verb inherits `--force`, `--backup`, `--dry-run`, `--json`, `--quiet`, `--mkdir` via the shared `@common_output_options` decorator. Individual verb blocks only call them out when the verb overrides the default; run `claw xml <verb> --help` for the authoritative per-verb flag list.

---

## 1. QUERY (XPath)

### 1.1 `xpath`

> Source: [scripts/claw/src/claw/xml/xpath.py](../../scripts/claw/src/claw/xml/xpath.py)

Run an XPath 1.0 expression against the document.

```
claw xml xpath <file|-> "EXPR" [--var NAME=VALUE]... [--ns PREFIX=URI]...
                               [--text|--html|--xml|--attr NAME|--count]
                               [--json] [--out FILE|-]
```

Flags:

- `--var` — bind XPath variables (safe against injection). `--var id=42` binds `$id` to `42`.
- `--ns` — declare a namespace prefix for use in the expression.
- `--text` — print `text()` content of each match.
- `--xml` (default) — print the serialized XML of each matched element.
- `--html` — HTML-style serialization.
- `--attr NAME` — print the named attribute on each match.
- `--count` — print the count only (useful for assertions).

Examples:

```
claw xml xpath catalog.xml "//book[@category=$c]/title/text()" --var c=Fantasy
```

```
claw xml xpath data.xml "//item" --count
```

```
claw xml xpath soap.xml "//soap:Body/*" --ns soap=http://schemas.xmlsoap.org/soap/envelope/
```

---

## 2. TRANSFORM (XSLT)

### 2.1 `xslt`

> Source: [scripts/claw/src/claw/xml/xslt.py](../../scripts/claw/src/claw/xml/xslt.py)

Apply an XSLT 1.0 stylesheet.

```
claw xml xslt <in.xml> <stylesheet.xsl> [--param KEY=VALUE]...
                                         [--out FILE|-] [--force]
                                         [--profile FILE]
```

Flags:

- `--param` — pass XSLT parameters. Values are quoted as strings; use `--param-xpath k=EXPR` for numeric / node-set params.
- `--profile FILE` — write XSLT profiling output to a separate file.

Examples:

```
claw xml xslt data.xml transform.xsl --out report.html
```

```
claw xml xslt invoice.xml invoice-to-html.xsl --param locale=en_US --out invoice.html
```

XSLT 2.0 / 3.0: `lxml` only supports 1.0. Use Saxon via `saxon-b` CLI for 2.0/3.0 workloads — `claw` does NOT try to bridge.

---

## 3. VALIDATE

### 3.1 `validate`

> Source: [scripts/claw/src/claw/xml/validate.py](../../scripts/claw/src/claw/xml/validate.py)

Validate an XML document against a schema. Exactly one of `--xsd` / `--rng` / `--rnc` / `--dtd` / `--sch`.

```
claw xml validate <file> (--xsd SCHEMA | --rng SCHEMA | --rnc SCHEMA
                          | --dtd SCHEMA | --sch SCHEMA)
                         [--all-errors] [--json]
```

Flags:

- `--all-errors` — report every validation error, not just the first. Default is first-fail.
- `--json` — `{valid: bool, errors: [{line, column, domain, type, message}]}` structured output.

Examples:

```
claw xml validate invoice.xml --xsd invoice.xsd
```

```
claw xml validate feed.atom --rng atom.rng --all-errors --json
```

Exit code 6 on validation failure (vs exit 0 on pass), for CI scripting.

---

## 4. CANONICALIZE

### 4.1 `canonicalize`

> Source: [scripts/claw/src/claw/xml/canonicalize.py](../../scripts/claw/src/claw/xml/canonicalize.py)

Emit the C14N canonical form of the document — required for XML signatures, diffing, and hashing.

```
claw xml canonicalize <file|-> [--version 1.0|1.1|2.0]
                               [--with-comments] [--exclusive]
                               [--out FILE|-]
```

Flags:

- `--version` — `1.0` (default), `1.1`, or `2.0`.
- `--exclusive` — exclusive canonicalization (XML-SIG's ExcC14N).
- `--with-comments` — preserve comments (default: strip).

Example:

```
claw xml canonicalize signed.xml --version 2.0 --out canonical.xml
```

---

## 5. FORMAT

### 5.1 `fmt`

> Source: [scripts/claw/src/claw/xml/fmt.py](../../scripts/claw/src/claw/xml/fmt.py)

Pretty-print an XML document.

```
claw xml fmt <file|-> [--indent 2] [--sort-attrs]
                      [--declaration] [--encoding utf-8]
                      [--out FILE|-]
```

Flags:

- `--indent N` — spaces per level (default 2).
- `--sort-attrs` — sort attributes alphabetically (deterministic output for diffing).
- `--declaration` — emit the XML declaration (`<?xml version="1.0" encoding="utf-8"?>`).

Example:

```
claw xml fmt raw.xml --indent 2 --sort-attrs --declaration --out formatted.xml
```

---

## 6. STREAM

### 6.1 `stream-xpath`

> Source: **NOT IMPLEMENTED** — no `xml/stream_xpath.py` exists.

Process multi-GB XML without loading it all. Uses `lxml.etree.iterparse` with memory clearing after each top-level element.

```
claw xml stream-xpath <file> --tag TAG "EXPR" [--var NAME=VAL]... [--ns PREFIX=URI]...
                             [--text|--xml|--attr NAME] [--json]
                             [--progress=json]
```

Flags:

- `--tag TAG` — the top-level repeating element (e.g. `record`, `item`). Memory is freed after each `--tag` element completes.
- `"EXPR"` — the XPath evaluated against each element (NOT against the root). Use relative paths: `title/text()`, not `//title/text()`.

Example — stream 10 GB of products:

```
claw xml stream-xpath products.xml --tag product \
  "concat(@sku, ':', price/text())" --json > prices.jsonl
```

This runs at near-disk-read speed with constant memory.

---

## 7. CONVERT

### 7.1 `to-json`

> Source: [scripts/claw/src/claw/xml/to_json.py](../../scripts/claw/src/claw/xml/to_json.py)

Convert XML to JSON. Two styles:

```
claw xml to-json <file|-> [--objectify | --literal]
                          [--out FILE|-]
```

Flags:

- `--literal` (default) — preserve XML structure: `{"tag": "...", "attrib": {...}, "text": "...", "children": [...]}`.
- `--objectify` — use `lxml.objectify` style: attribute access on element names, scalar auto-typing. `<item>42</item>` → `42` (int). Lossy but ergonomic.

Examples:

```
claw xml to-json catalog.xml --literal --out catalog.json
```

```
claw xml to-json config.xml --objectify | jq '.database.host'
```

---

## When `claw xml` Isn't Enough

Drop into `lxml` directly for:

| Use case | Why `claw` can't do it | Escape hatch |
|---|---|---|
| XPath 2.0 / 3.0 features (sequences, regex, date arithmetic) | `lxml` is 1.0-only; `claw` inherits that limit | Use Saxon HE (`saxon-b`) CLI or Python bindings |
| Schematron validation | Not wrapped (`--sch` is reserved for future; currently stubs to `code=NOT_IMPLEMENTED`) | `lxml.isoschematron.Schematron` |
| XSLT with Python extension functions | No plugin mechanism in CLI | `etree.XSLT.registerFunction` |
| Custom element classes / ObjectPath walks | Programmatic only | `lxml.objectify` + `ElementDefaultClassLookup` |
| XInclude processing | Not wrapped | `lxml.etree.ElementTree.xinclude()` |
| Digital signature sign/verify (xmldsig) | Out of scope | `signxml` library |
| Content-aware merging of two XML trees | No merge verb | `xmldiff` CLI or programmatic tree walk |

**lxml** — `pip install lxml` · [docs](https://lxml.de/)
- XPath 1.0 only — no sequences, no regex, no date functions; reach for Saxon if you need XPath/XSLT 2.0+.
- `//foo` against a document with a default namespace (`xmlns="..."`) returns zero hits; XPath 1.0 has no default-namespace syntax — declare a prefix and use `//n:foo`.
- `etree.parse()` with `resolve_entities=True` is a file-disclosure / billion-laughs vector on attacker-controlled XML; keep defaults.

## Footguns

- **XXE** — do NOT pass `--allow-entities --allow-network` on attacker-controlled XML. The defaults protect against billion-laughs, SSRF-via-DTD, and file-disclosure XXE. Loosen only when processing known-good internal XML.
- **XPath f-string injection** — never build `claw xml xpath ... "//x[@id='" + user_input + "']"`. Always use `--var`. `claw` refuses naked `$foo` without `--var foo=...` to force this habit.
- **Default-namespace XPath** — `//foo` against a document with `xmlns="http://ns.example"` returns zero hits. Declare a prefix and use it: `--ns n=http://ns.example` + `//n:foo`. There is no default-namespace XPath syntax in 1.0.
- **`to-json --objectify` round-trip loss** — attributes, mixed content, comments, and CDATA are dropped. Use `--literal` for anything you need to rebuild.
- **`stream-xpath` evaluates against the per-tag element, not the document root** — use `title/text()`, not `/root/product/title/text()`. `claw` injects the boundary automatically.
- **Huge trees** — by default `huge_tree=False` rejects documents with unreasonable depth (stack protection). Pass `--huge-tree` if the document is genuinely pathological but trusted.
- **XSLT with input as stdin** — the second positional (`stylesheet.xsl`) must be a file path; you can't stream the stylesheet over stdin, only the input XML.

---

## Quick Reference

| Task | One-liner |
|------|-----------|
| XPath text | `claw xml xpath f.xml "//title/text()"` |
| XPath with var | `claw xml xpath f.xml "//item[@id=$i]" --var i=42` |
| Count matches | `claw xml xpath f.xml "//item" --count` |
| XSLT transform | `claw xml xslt in.xml t.xsl --out out.html` |
| Validate XSD | `claw xml validate f.xml --xsd schema.xsd` |
| Canonicalize | `claw xml canonicalize f.xml --version 2.0` |
| Pretty-print | `claw xml fmt f.xml --sort-attrs` |
| Stream 10 GB | `claw xml stream-xpath big.xml --tag record "./id/text()"` |
| XML → JSON | `claw xml to-json f.xml --objectify` |
| Namespaced query | `claw xml xpath f.xml "//s:Body" --ns s=http://...` |
