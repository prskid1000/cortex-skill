# Claude Code Binary Patcher v2

Script: `~/.claude/skills/claude-claw/scripts/claude-patcher.js`

## What It Does

Patches the compiled Claude Code binary to override hardcoded limits. Finds constants by **value + structural context** (not minified variable names), so it survives version updates.

## Patchable Constants

| Flag | Default → Patched | Digits | Anchor |
|------|-------------------|--------|--------|
| `--context-window` | 200000 → 262000 | 6 | Near token constant cluster |
| `--max-output` | 128000 | 6 | After model name `includes()` |
| `--autocompact` | 13000 → 20000 | 5 | Near `autocompact` string + 20000/3000 cluster |
| `--summary-max` | 40000 → 80000 | 5 | `minTextBlockMessages:N,maxTokens:N` key |

## Usage

```bash
# Scan — show all discovered constants (no changes)
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --scan

# Apply all defaults (262k context, 20k autocompact, 80k summary)
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --all

# Custom value
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --context-window 300000

# Preview without writing
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --all --dry-run

# Restore original
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --restore
```

## After Claude Code Updates

Re-run — updates overwrite the binary. Backup is preserved.

```bash
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --all
```

## How It Works

- Finds constants by their **actual values** in structural context (not variable names)
- Uses anchors: model name strings, config key names, nearby known constants
- Patches **all occurrences** (binary has 2 identical code copies)
- Same-length replacements preserve binary structure
- Creates `.bak` backup on first run
- Handles locked binary (writes `.patched` with copy instructions)
- Verifies all patches after writing

## Limitations

- Replacement must have same digit count as original (200000 → 6 digits only)
- For 1M+ context, use model name with `[1m]` suffix instead
