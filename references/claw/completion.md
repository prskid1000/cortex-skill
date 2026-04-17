# `claw completion` — Shell Completions

> Source: [scripts/claw/src/claw/completion.py](../../scripts/claw/src/claw/completion.py)

`claw completion` emits a source-able completion script for the shell you pick. Completions cover nouns, verbs, all declared flags, positional file arguments (TAB expands files), and enumerated values (e.g. `--color auto|always|never`). Dynamic values that would require a subprocess per keystroke (Gmail message IDs, Drive file IDs, pipeline step names) are intentionally left out.

## Contents

- **GENERATE a script**
  - [`claw completion` command](#1-claw-completion-command)
- **INSTALL per shell**
  - [bash](#2-bash) · [zsh](#3-zsh) · [fish](#4-fish) · [PowerShell](#5-powershell)
- **UNDERSTAND scope**
  - [What completes](#6-what-completes) · [What doesn't](#7-what-doesnt)

---

## Critical Rules

1. **Completion is static.** Scripts must not call `claw` at completion time — slow shells frustrate users. All data is baked into the emitted script.
2. **One source command, one script.** `claw completion bash` is the only source of truth; update `claw` to refresh completions.
3. **Flags respect scope.** `--sheet` completes inside `claw xlsx *`, not elsewhere. Don't pollute global flag lists.
4. **File arguments default to filesystem completion.** Typed filters (`.xlsx`, `.pdf`) apply only when the verb accepts a specific extension.
5. **Re-run after upgrading `claw`.** A new version may add verbs/flags; your shell snapshot won't reflect that until you re-source.

---

## 1. `claw completion` command

```
claw completion <shell>
```

| `<shell>` | Target |
|-----------|--------|
| `bash` | bash 4+ (via `complete -F`) |
| `zsh` | zsh (via `#compdef` + `_arguments`) |
| `fish` | fish 3+ (via `complete -c claw`) |
| `pwsh` | PowerShell 7+ (via `Register-ArgumentCompleter`) |

Writes the script to stdout; nothing else is printed. Exit `0` on success, `2` on unknown shell.

## 2. bash

### Install system-wide (preferred on Linux)

```bash
claw completion bash | sudo tee /etc/bash_completion.d/claw >/dev/null
# new shells pick it up automatically
```

### Install per-user

```bash
mkdir -p ~/.local/share/bash-completion/completions
claw completion bash > ~/.local/share/bash-completion/completions/claw
```

### Install via `.bashrc`

Append to `~/.bashrc`:

```bash
# claw completion
source <(claw completion bash)
```

Reload: `source ~/.bashrc`.

## 3. zsh

### Install to fpath

```zsh
mkdir -p ~/.zsh/completions
claw completion zsh > ~/.zsh/completions/_claw
```

Add to `~/.zshrc` (before `compinit`):

```zsh
fpath=(~/.zsh/completions $fpath)
autoload -Uz compinit && compinit
```

Reload: `exec zsh`.

### oh-my-zsh

```zsh
mkdir -p ~/.oh-my-zsh/custom/plugins/claw
claw completion zsh > ~/.oh-my-zsh/custom/plugins/claw/_claw
# add 'claw' to plugins=(...) in ~/.zshrc
```

## 4. fish

Fish auto-loads completions from `~/.config/fish/completions/`.

```fish
mkdir -p ~/.config/fish/completions
claw completion fish > ~/.config/fish/completions/claw.fish
```

No reload needed — fish rescans on next command.

## 5. PowerShell

Append to your profile (`$PROFILE`). Find it with `echo $PROFILE`; create if missing.

```pwsh
# One-time: write the completion script somewhere stable
claw completion pwsh | Out-File -Encoding utf8 "$HOME\Documents\PowerShell\claw-completion.ps1"

# In $PROFILE:
. "$HOME\Documents\PowerShell\claw-completion.ps1"
```

Reload: `. $PROFILE`.

Windows PowerShell 5.1 is not supported — PowerShell 7+ only (`Register-ArgumentCompleter` semantics differ).

## 6. What completes

| Token position | Completes to |
|----------------|--------------|
| After `claw` | Nouns: `xlsx docx pptx pdf img media convert email doc sheet web html xml browser pipeline doctor completion cache config help schema` |
| After `claw <noun>` | Verbs for that noun (e.g. `claw xlsx <TAB>` → `new from-csv from-json read style chart freeze filter conditional format table validate name-add print-setup protect meta pivots-list to-csv to-pdf sql stat append richtext-set image-add`) |
| After `claw <noun> <verb>` | Flags registered on that verb + filesystem completion for positional file args |
| After a flag that takes an enumerated value | The enum (e.g. `--color <TAB>` → `auto always never`) |
| After a flag that takes a path | Filesystem files filtered by declared extension if any (e.g. `claw pdf merge --out <TAB>` filters to `*.pdf`) |
| After `claw pipeline <TAB>` | `run validate list-steps graph` |
| After `claw completion <TAB>` | `bash zsh fish pwsh` |
| After `claw help <TAB>` | Any `<noun>` or `<noun> <verb>` combo |
| After `claw schema <TAB>` | Every `<noun>.<verb>` step type (same list as `claw pipeline list-steps`) |

Global flags (`--help`, `--json`, `--progress=json`, `--quiet`, `-v`, `-vv`, `-vvv`, `--force`, `--backup`, `--dry-run`, `--stream`, `--mkdir`, `--color`, `--version`) complete at every level.

## 7. What doesn't

Intentionally out of scope — completion would require `claw` subprocess calls:

- **Gmail message / thread IDs** — dynamic; use `gws gmail messages list` + `fzf` instead.
- **Drive file IDs** — same.
- **ClickUp task IDs** — same.
- **Sheet tab names** — would need to open the workbook.
- **Pipeline step IDs from a recipe file** — YAML parse on every TAB is too slow; paste from `claw pipeline list-steps` or `claw pipeline validate`.
- **LM Studio model IDs** — require an HTTP call to the running daemon.

For these, pair completion with `fzf` on demand:

```bash
# Example: pick a Drive file ID interactively
fid=$(gws drive files list --json | jq -r '.files[] | "\(.id)\t\(.name)"' | fzf | cut -f1)
claw doc export --file-id "$fid" --out /tmp/out.pdf
```

---

## Quick Reference

| Shell | Install |
|-------|---------|
| bash | `claw completion bash \| sudo tee /etc/bash_completion.d/claw` |
| zsh | `claw completion zsh > ~/.zsh/completions/_claw` then add to `fpath` |
| fish | `claw completion fish > ~/.config/fish/completions/claw.fish` |
| pwsh | `claw completion pwsh > claw-completion.ps1`, dot-source from `$PROFILE` |
| Refresh after upgrade | Re-run the install command above |
