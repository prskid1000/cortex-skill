# Extending `claw` — agent playbook

> **Audience:** LLM agents extending or fixing `claw`. This is a checklist, not a tutorial. Follow it exactly.

## Contents

- **ADD a verb to an existing noun**
  - [Files to touch](#files-to-touch-new-verb) · [Verb module shape](#verb-module-shape) · [Register in `__init__.py`](#register-in-_init_py) · [Document it](#document-it) · [Smoke test](#smoke-test)
- **ADD a whole new noun**
  - [Files to touch](#files-to-touch-new-noun) · [Noun package shape](#noun-package-shape) · [Register in `__main__.py`](#register-in-_main_py) · [Declare deps](#declare-deps)
- **FIX a bug in an existing verb**
  - [Fix workflow](#fix-workflow)
- **ADD / DEPRECATE a flag**
  - [Add a flag](#add-a-flag) · [Deprecate a flag](#deprecate-a-flag)
- **PITFALLS**
  - [Code pitfalls](#code-pitfalls) · [Doc pitfalls](#doc-pitfalls) · [Anchor pitfalls](#anchor-pitfalls)

---

## Critical Rules

1. **Every verb is one file** at `scripts/claw/src/claw/<noun>/<verb_snake>.py` exporting a Click command whose Python name matches what `__init__.py VERBS` points at. User-facing verb name uses hyphens; file/function name uses underscores.
2. **Lazy-import heavy deps inside the function body.** Never top-level `import fitz` / `import openpyxl` / `import PIL`. Breaks `claw --help` startup time.
3. **Every write uses `claw.common.safe_write`.** Never `path.write_bytes(...)` directly.
4. **Every mutating verb uses `@common_output_options`** — gives it `--force --backup --json --dry-run --quiet -v --mkdir` with consistent semantics.
5. **`--json` flips *all* output** to NDJSON on stdout; logs stay on stderr.
6. **Exit codes**: `0` ok · `1` generic · `2` usage · `3` partial · `4` input/remote · `5` system · `130` SIGINT. Use `claw.common.die(msg, code=EXIT_*)`.
7. **Docs use the decision-tree `## Contents` format** (top-level VERBs in caps → nested anchor links). Body stays flat numbered H2 (`## 1.1`, `## 1.2`). Never impose the tree shape on code or tables.
8. **Anchors match SKILL.md.** Grep `SKILL.md` for the file you're editing before renaming any H2.

---

## ADD a verb to an existing noun

### Files to touch (new verb)

1. `scripts/claw/src/claw/<noun>/<verb_snake>.py` — create.
2. `scripts/claw/src/claw/<noun>/__init__.py` — add one line to `VERBS`.
3. `references/claw/<noun>.md` — add one verb subsection + one Contents entry.
4. `examples/claw-recipes.md` — add one one-liner recipe.

### Verb module shape

```python
"""claw <noun> <verb-with-hyphens> — one-line purpose."""
from __future__ import annotations
from pathlib import Path
import click
from claw.common import common_output_options, die, emit_json, safe_write, EXIT_INPUT


@click.command(name="<verb-with-hyphens>")
@click.argument("src", type=click.Path(path_type=Path))
@click.argument("dst", type=click.Path(path_type=Path))
@click.option("--flag", default=None, help="…")
@common_output_options
def <verb_snake>(src, dst, flag,
                 force, backup, as_json, dry_run, quiet, verbose, mkdir):
    """First line shown in `claw <noun> --help`.

    Longer description shown in `claw <noun> <verb> --help`.
    """
    try:
        from <lib> import <thing>
    except ImportError:
        die("install claw[<extra>]", hint="uv tool install 'claw[<extra>]'",
            code=EXIT_INPUT)

    # happy-path implementation

    if dry_run:
        click.echo(f"would write {dst}")
        return

    safe_write(dst, lambda f: ..., force=force, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"path": str(dst), "…": …})
    elif not quiet:
        click.echo(f"wrote {dst}")
```

### Register in `__init__.py`

In `scripts/claw/src/claw/<noun>/__init__.py`:

```python
VERBS: dict[str, tuple[str, str]] = {
    …
    "<verb-with-hyphens>": ("claw.<noun>.<verb_snake>", "<verb_snake>"),
}
```

Key = user-facing hyphenated name. Value = `(module_dotted_path, function_name)`. The `LazyGroup` imports only when the subcommand is invoked.

### Document it

In `references/claw/<noun>.md`:

- Add a Contents entry under the matching VERB bucket:
  ```markdown
  - **<VERB>**
    - [<verb-name> — purpose](#NN-verb-name)
  ```
- Add an H2 body section:
  ```markdown
  ### N.N verb-name

  Purpose: one line.

      claw <noun> <verb-name> <args> [--flag …]

  | Flag | Type | Default | Purpose |
  |------|------|---------|---------|
  | `--flag` | str | — | … |

  Example:

      claw <noun> <verb-name> in out --flag X
  ```

In `examples/claw-recipes.md`:

- Add a one-liner under the matching VERB heading. Keep it happy-path. Complex multi-step flows go in `examples/claw-pipelines.md` as YAML.

### Smoke test

```bash
uv pip install -e ./scripts/claw
claw <noun> <verb-with-hyphens> --help       # Click auto-generates
claw <noun> <verb-with-hyphens> <real-args>  # end-to-end
claw <noun> <verb-with-hyphens> --dry-run …   # dry-run path
claw <noun> <verb-with-hyphens> --json …      # valid NDJSON?
```

---

## ADD a whole new noun

Rare. Only for a genuinely new user-task category (not a new tool).

### Files to touch (new noun)

1. `scripts/claw/src/claw/<noun>/` — mkdir + `__init__.py`.
2. `scripts/claw/src/claw/__main__.py` — add entry to `NOUNS` dict.
3. `scripts/claw/pyproject.toml` — add extra if new deps.
4. `references/claw/<noun>.md` — new reference (copy `references/_TEMPLATE.md`).
5. `SKILL.md` — add the noun under the matching VERB branch in the File Map.
6. `examples/claw-recipes.md` — add a VERB section if the noun introduces one.

### Noun package shape

`scripts/claw/src/claw/<noun>/__init__.py`:

```python
"""claw <noun> — <one-line purpose>. See references/claw/<noun>.md."""

import click

from claw.common import LazyGroup

VERBS: dict[str, tuple[str, str]] = {
    "<verb>": ("claw.<noun>.<verb_snake>", "<verb_snake>"),
}


@click.command(cls=LazyGroup, lazy_commands=VERBS,
               context_settings={"help_option_names": ["-h", "--help"]})
def group() -> None:
    """<one-line purpose shown by `claw --help`>."""
```

### Register in `__main__.py`

```python
NOUNS = {
    …
    "<noun>": ("claw.<noun>", "group"),
}
```

### Declare deps

In `scripts/claw/pyproject.toml`:

```toml
[project.optional-dependencies]
<noun> = ["<pkg>>=<version>"]
all = [… existing … , "<pkg>>=<version>"]
```

---

## FIX a bug in an existing verb

### Fix workflow

1. Reproduce the bug with an exact command the user reported.
2. Write a failing pytest case at `scripts/claw/tests/test_<noun>_<verb>.py` using `click.testing.CliRunner`.
3. Edit only the verb module. Resist touching shared helpers unless the bug is a helper contract violation.
4. Re-run the failing test; confirm it passes.
5. If the verb's docs gave incorrect guidance (e.g., a flag example that would error), fix `references/claw/<noun>.md` too.

---

## ADD / DEPRECATE a flag

### Add a flag

1. `@click.option(...)` on the verb. Favor `click.Choice([...])` over free-form strings when the domain is small.
2. Update that verb's flag table in `references/claw/<noun>.md`.
3. If the flag enables a novel workflow, add a recipe to `examples/claw-recipes.md`.

### Deprecate a flag

1. Keep the flag accepted, mark `hidden=True` so it disappears from `--help`.
2. Log a warning when used:
   ```python
   if old_flag:
       click.echo("warning: --old-flag is deprecated; use --new-flag", err=True)
   ```
3. Remove at the next major version. Agents don't track versions — that's a human concern; just leave the warning in place until a human removes it.

---

## PITFALLS

### Code pitfalls

- **Don't top-level-import optional deps.** Gate inside `try: from … import …; except ImportError: die(…)`.
- **Don't use `os.rename` across filesystems.** `safe_write` uses `os.replace` which handles cross-volume atomically on modern OSes.
- **Windows subprocess shims**: always go through `claw.common.run("tool", …)`. Never `subprocess.run(["tool", …])` directly — PATH-resolution fails on `.cmd`/`.bat`.
- **`PageSelector("all").resolve(0)`** returns `[]`, not an error. Guard empty page-ranges at the verb level when that would be surprising.
- **`openpyxl data_only=True`** returns `None` for uncached formulas. Surface an actionable error, don't silently emit blanks.
- **`fitz.Document.save(same_path)`** raises unless `incremental=True`. `safe_write` writes to a temp path and then replaces — compatible with fitz if you save to the temp file.
- **`ffmpeg -pass N`** leaves `ffmpeg2pass-0.log` in CWD. Always `-passlogfile $(mktemp -d)/pass` to avoid clobbering parallel runs.
- **Gmail threading** silently breaks without `In-Reply-To` + `References` headers. `claw email reply` must fetch them from the source message first.
- **Coordinate origin** for `pdf` box flags: PyMuPDF uses top-left, reportlab uses bottom-left. Document which a verb uses in its `--help`.

### Doc pitfalls

- **Decision-tree format is for `## Contents` only** — not for body sections. Body stays flat numbered H2.
- **Quick Reference table** at the bottom: top-N commands. Keep it synced when verbs change.
- **Cross-links must point at existing anchors.** When adding a new H2, update the Contents tree. When renaming, grep `SKILL.md` and every sibling ref for the old anchor first.
- **Never duplicate library API docs.** Reference docs in `references/claw/<noun>.md` describe the CLI. The library API lives in `references/<library>.md` as an escape hatch.

### Anchor pitfalls

GitHub slugifier (used by all our markdown consumers):

1. Lowercase.
2. Strip punctuation (`.`, `?`, `!`, `(`, `)`, `:`, `/`, etc.).
3. Spaces → hyphens.
4. Duplicate headings get `-2`, `-3`, … suffixes.

Traps:

- Em-dash (`—`) is stripped; surrounding spaces collapse: `API — summary` → `api--summary` (two hyphens).
- `/` is dropped without hyphen insertion: `a/b` → `ab`.
- Parentheses dropped: `(experimental) flags` → `experimental-flags`.
- Code spans preserved literally inside heading text: `` ## `--flag` — purpose `` → `--flag--purpose`.

Verification:

```bash
grep -n "^## " references/claw/<noun>.md    # list headings
grep -nF "#<new-anchor>" -r references/ SKILL.md  # find inbound links
```

---

## Quick Reference

| Task | Files touched |
|------|---------------|
| New verb | verb `.py` + noun `__init__.py` `VERBS` + ref doc + recipe |
| New noun | verb + noun `__init__.py` + `__main__.py` `NOUNS` + ref doc + SKILL.md File Map + pyproject extras |
| Bugfix | verb `.py` + test in `tests/` |
| New flag | verb `.py` + ref doc flag table |
| Deprecate flag | verb `.py` (hidden=True + warning) |
| Any task: verify | `claw <cmd> --help`, `--dry-run`, `--json`, smoke e2e |
