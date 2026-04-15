# Claude Code Binary Patcher

Script: `~/.claude/skills/claude-claw/scripts/claude-patcher.js`

## What It Does

Patches numeric constants inside the compiled Claude Code binary
(`~/.local/bin/claude.exe` on Windows, `claude` elsewhere) — a Node SEA bundle
that contains all of Claude Code's minified JS as embedded source. The patcher
locates each constant by **value + structural anchor** (model name strings,
unique log strings, nearby fixed numbers), not by minified variable name, so it
survives Anthropic's per-release variable renaming.

## Patchable Constants

| Flag | Default → Patched | Digit Count | Original | Anchor Strategy |
|------|-------------------|-------------|----------|-----------------|
| `--context-window` | 200000 → 262000 | 6 | 200000 | `return VAR}` inside a function whose body contains `return 1e6` |
| `--max-output` | per-model | 6 | 32000/64000 | `includes("opus-4-6"\|"sonnet-4-6"))VAR=...,VAR2=NNNNNN` |
| `--autocompact` | 13000 → 20000 | 5 | 13000 | `=1e6,VAR=NNNNN,` inside cluster with `=3000,` and the literal `autocompact` |
| `--summary-max` | 40000 → 80000 | 5 | 40000 | `exactly as written.",VAR=NNNNN,` |

Each anchor is a string literal that survives minification (Anthropic doesn't
mangle string content), so renaming `Ajt` → `Bxq` between releases doesn't
break detection.

## Usage

```bash
# Scan — show all discovered constants, no changes
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --scan

# Apply all four with defaults
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --all

# One-off custom value
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --context-window 300000

# Preview without writing
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --all --dry-run

# Restore from backup
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --restore

# Different binary path
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --all --binary D:/tools/claude.exe
```

## After Claude Code Updates

Updates overwrite the binary at `~/.local/bin/claude.exe`. Backup is preserved
at `~/.local/bin/claude.exe.bak` from the **previous** version — re-run
`--all` after every update to re-apply patches against the new binary. The
patcher creates a fresh `.bak` only when one doesn't exist; if you want to
keep the old backup, move it before re-patching.

```bash
# Typical post-update flow
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --scan    # confirm constants still found
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --all     # re-apply
```

If `--scan` reports `NOT FOUND` for any constant, the anchor broke —
see [Recovery](#recovery-when-an-anchor-breaks) below.

## How It Works Internally

1. **Find binary** via `--binary`, then `~/.local/bin/claude.exe`, then
   `where claude`/`which claude`. Fails with explicit error if none found.
2. **Read entire binary** as both `Buffer` (for byte ops) and `utf8` string
   (for regex search — works because the JS source inside the SEA is valid UTF-8).
3. **`discover()`** runs the four anchor regexes and returns hit lists. Each
   constant must have **≥ 2 hits** (the binary has duplicate code copies); a
   single hit is treated as missing for safety.
4. **Build patches** as `{find, replace}` pairs preserving original digit count
   (replacement must be same length to keep byte offsets stable).
5. **Backup** to `<bin>.bak` if missing.
6. **Apply** — for each unique `find` string, locate ALL occurrences in the
   buffer and overwrite them. Same-length replacement = no offset shift.
7. **Write** binary; if EBUSY/EPERM (Windows file lock), write to `.patched`
   sibling and print copy command. The user closes Claude, then runs the copy.
8. **Verify** by reading written file and confirming each `replace` string is
   present.

## The Four Anchors In Detail

### 1. Context Window — `return 1e6` proximity
```js
// Inside discover():
const retRe = /return ([a-zA-Z_$][a-zA-Z0-9_$]*)\}/g;
// For each match, check the preceding 500 chars include "return 1e6"
// Then re-grep for VAR=NNNNNN, where N is 6 digits
```
**Why this anchor:** Claude Code's model-config table has a `1e6` (1 million
token) constant for the 1M-context Sonnet variant. Right next to it sits a
function returning the **default** model context. The function name is
minified, so we anchor on `return 1e6` instead.

**Failure modes:**
- Anthropic adds a new model with non-`1e6` literal (e.g. `2e6` for 2M context)
  → `return 1e6` substring still present? If yes, no break. If they switch
  EVERY model to a different format → break.
- Default context bumped to a non-6-digit value → digit-count assertion fails.

### 2. Max Output — model name string proximity
```js
// includes("opus-4-6"))VAR=NNNNN,VAR2=NNNNNN
const re = /includes\("(opus-4-6|sonnet-4-6)"\)\)([a-zA-Z_$][a-zA-Z0-9_$]*)=(\d+),([a-zA-Z_$][a-zA-Z0-9_$]*)=(\d+)/g;
```
**Why this anchor:** Model selection logic uses `name.includes("opus-4-6")` to
match — these strings are stable across Claude Code versions because they're
the actual model identifiers Anthropic ships. The two consecutive var
assignments are the model's `default` and `upper` output token values.

**Failure modes:**
- New model series ships (`opus-4-7`, `sonnet-5-0`) → regex misses the new
  branch. **Fix:** widen the alternation to `(opus-4-[0-9]+|sonnet-[0-9]-[0-9]+)`
  or add specific new model names.
- Anthropic switches from `.includes()` to `.startsWith()` or a Map lookup →
  regex break. **Fix:** find the new pattern in extracted source, update the
  anchor.

### 3. Autocompact — `=1e6,` + `=3000,` + `autocompact` cluster
```js
// =1e6,VAR=NNNNN, where the surrounding 600 chars contain both
// "=3000," (some other constant) and the literal string "autocompact"
const re = /=1e6,([a-zA-Z_$][a-zA-Z0-9_$]*)=(\d{4,5}),/g;
// Then filter by ctx() containing "=3000," AND "autocompact"
```
**Why this anchor:** The autocompact buffer constant lives inside the same
config block as the 1M token constant and another 3000-token constant. The
literal string `"autocompact"` (used for log/telemetry) confirms we're in the
right block.

**Failure modes:**
- The `=3000,` co-constant changes value → break. **Fix:** scan binary for new
  cluster shape, update the secondary check.
- `autocompact` log string renamed → break. **Fix:** find new identifier in
  extracted source, update string check.

### 4. Summary Max — system-prompt instruction string
```js
// "exactly as written.",VAR=NNNNN,
const re = /exactly as written\.",([a-zA-Z_$][a-zA-Z0-9_$]*)=(\d{4,5}),/g;
```
**Why this anchor:** The literal phrase `exactly as written.` appears in
Claude Code's CLAUDE.md instruction text inside the summary-generation prompt.
The constant declared right after that string is the summary token cap.

**Failure modes:**
- Anthropic edits the system prompt text → break. Most fragile of the four.
  **Fix:** find a new short, unique substring of the system prompt that's
  immediately followed by `,VAR=NNNNN,`.

## Recovery When An Anchor Breaks

When `--scan` reports `NOT FOUND` for a constant:

1. **Confirm the binary version.** Compare to your last working version:
   ```bash
   ls -la ~/.local/bin/claude.exe ~/.local/bin/claude.exe.bak
   strings ~/.local/bin/claude.exe | grep -i "version\|claude-code" | head -5
   ```

2. **Extract the JS source for inspection.** The Node SEA bundle is one big
   binary with the JS embedded as UTF-8. Easiest way to inspect:
   ```bash
   # Find the JS region — it starts somewhere after the SEA header
   strings ~/.local/bin/claude.exe | grep -n "claude-code\|exactly as written\|autocompact" | head -20
   # Or dump everything and grep
   strings ~/.local/bin/claude.exe > /tmp/claude-strings.txt
   ```

3. **For each broken anchor, hunt the new pattern.**

   - **Context window broken?** Search for the string `1e6`:
     ```bash
     grep -bo "return 1e6" /tmp/claude-strings.txt | head
     ```
     If `1e6` is gone, find what replaced 1M context. Look for `1000000` or new
     model constants. Update the anchor in `discover()` § 1.

   - **Max output broken?** Search for current model identifiers:
     ```bash
     grep -bo 'opus-4-[0-9]\|sonnet-[0-9]-[0-9]\|haiku-[0-9]' /tmp/claude-strings.txt | head
     ```
     Update the alternation list in `discover()` § 2.

   - **Autocompact broken?** Search for the string:
     ```bash
     grep -bo "autocompact" /tmp/claude-strings.txt | head
     ```
     If the log string was renamed, find what replaced it. If the `=3000,`
     co-constant changed, locate it via context.

   - **Summary-max broken?** Search for the system-prompt phrase:
     ```bash
     grep -bo "exactly as written" /tmp/claude-strings.txt | head
     ```
     If the prompt was reworded, pick a new unique short substring from the
     summary section and update § 4.

4. **Edit `claude-patcher.js`.** Each anchor is an isolated `{ ... }` block
   inside `discover()` (see lines 96–168). Update only the regex + ctx check
   for the broken anchor; leave the others untouched.

5. **Test.**
   ```bash
   node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --scan
   # Should now show all four constants found
   node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --all --dry-run
   # Confirm patch points before writing
   node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --all
   ```

6. **Update the table at the top of this doc** with the new digit count or
   anchor description if it changed materially.

## When You Should NOT Patch

- **For 1M+ context windows.** The patcher's digit-count constraint means
  200000 → 999999 only. For 1M tokens, use the model name suffix
  `claude-opus-4-6[1m]` instead — that's Anthropic's public way to opt in.
- **If the binary is locked.** Close every Claude Code session first
  (`pkill -f claude` on Unix, end all `claude.exe` in Task Manager on Windows).
- **If you're testing official behavior.** Restore first:
  `node claude-patcher.js --restore`.

## Limitations

- **Same-length replacement only.** Replacement digit count must equal
  original; the binary's other byte offsets depend on this. (e.g. you can
  patch 200000 → 262000 but NOT 200000 → 1000000.)
- **Two anchors must hit per constant.** If the binary has only one copy of
  a constant cluster, the safety check skips it. Modify the `>= 2` threshold
  in `discover()` if you accept the risk.
- **Backup is single-slot.** Re-running `--all` against a freshly-updated
  binary creates `.bak` of the **already-updated** version, losing the
  pre-patch state of the earlier release. Move `.bak` aside before
  re-patching if you want to keep history.
