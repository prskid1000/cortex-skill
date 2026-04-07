# Claude Code Binary Patcher

Script: `~/.claude/skills/claude-claw/scripts/claude-patcher.js`

## What It Does

Patches the compiled Claude Code binary to override hardcoded limits that can't be changed via env vars. Essential for **custom endpoint** users where Claude Code enforces Anthropic API limits regardless of actual backend capabilities.

## Patchable Constants

| Flag | Target | Default | Notes |
|------|--------|---------|-------|
| `--context-window <N>` | `uJ7` (context window) | 200000 -> 262000 | Must be 6 digits (100k-999k) |
| `--max-output <N>` | `S6H` upper limits | 128000 | Must be 6 digits |
| `--autocompact-buffer <N>` | `j6$` (autocompact reserve) | 13000 | Must be 5 digits |
| `--summary-max <N>` | `Dc8.maxTokens` | 40000 | Must be 5 digits |

## Usage

```bash
# Apply all patches with defaults (262k context window)
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --all

# Custom context window
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --context-window 300000

# Preview without writing
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --all --dry-run

# Restore original binary
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --restore
```

## After Claude Code Updates

Re-run the patcher — updates overwrite the binary. Backup is preserved.

```bash
node ~/.claude/skills/claude-claw/scripts/claude-patcher.js --all
```

## Recommended Env Vars (set alongside patches)

```bash
export ANTHROPIC_BASE_URL="https://your-custom-endpoint"
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000
export ENABLE_TOOL_SEARCH=true
```

**Note:** `ENABLE_TOOL_SEARCH=true` is required for ToolSearch/deferred tool loading on custom endpoints. This is an env var — no binary patch needed.

## How It Works

- Pattern-matches minified JS inside the PE binary (not hardcoded offsets)
- Same-length replacements to preserve binary structure
- Auto-detects binary location
- Creates `.bak` backup on first run
- Handles locked binary (writes `.patched` file with copy instructions)
- Verifies all patches after writing

## Limitations

- Context window must be 6 digits (100,000-999,999). For 1M+, use model name with `[1m]` suffix
- Max output must be 6 digits
- Minified variable names may change across major versions
