#!/usr/bin/env node
/**
 * Claude Code Binary Patcher
 * Auto-discovers patch points by pattern matching in the JS bundle.
 * Configurable via CLI args. Stores in claude-claw skill for easy access.
 *
 * Usage:
 *   node claude-patcher.js [options]
 *
 * Options:
 *   --context-window <N>     Set context window size (default: 262000, must be 6 digits)
 *   --max-output <N>         Set max output token upper limit (e.g. 128000)
 *   --autocompact-buffer <N> Set autocompact buffer reservation (default: 13000)
 *   --summary-max <N>        Set max autocompact summary tokens (default: 40000)
 *   --all                    Apply all patches with defaults
 *   --restore                Restore from backup
 *   --dry-run                Show what would be patched without writing
 *   --binary <path>          Path to claude.exe (auto-detected if omitted)
 *   --help                   Show this help
 *
 * Examples:
 *   node claude-patcher.js --all
 *   node claude-patcher.js --context-window 500000 --max-output 200000
 *   node claude-patcher.js --restore
 */

const fs = require("fs");
const path = require("path");

// ─── CLI Parsing ────────────────────────────────────────────────────
const args = process.argv.slice(2);

function getArg(name) {
  const idx = args.indexOf(`--${name}`);
  if (idx === -1) return undefined;
  return args[idx + 1];
}
function hasFlag(name) {
  return args.includes(`--${name}`);
}

if (hasFlag("help") || args.length === 0) {
  const lines = fs.readFileSync(__filename, "utf8").split("\n");
  const helpStart = lines.findIndex(l => l.includes("* Usage:"));
  const helpEnd = lines.findIndex((l, i) => i > helpStart && l.includes("*/"));
  console.log(lines.slice(helpStart, helpEnd).map(l => l.replace(/^\s*\*\s?/, "")).join("\n"));
  process.exit(0);
}

// ─── Auto-detect binary ─────────────────────────────────────────────
function findBinary() {
  const candidates = [
    getArg("binary"),
    path.join(process.env.HOME || process.env.USERPROFILE, ".local", "bin", "claude.exe"),
    path.join(process.env.HOME || process.env.USERPROFILE, ".local", "bin", "claude"),
  ].filter(Boolean);

  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }

  // Try 'which claude' / 'where claude'
  try {
    const { execSync } = require("child_process");
    const cmd = process.platform === "win32" ? "where claude" : "which claude";
    const result = execSync(cmd, { encoding: "utf8" }).trim().split("\n")[0];
    if (result && fs.existsSync(result)) return result;
  } catch {}

  return null;
}

const TARGET = findBinary();
if (!TARGET) {
  console.error("ERROR: Could not find claude binary. Use --binary <path>");
  process.exit(1);
}
const BACKUP = TARGET + ".bak";
const applyAll = hasFlag("all");

// ─── Patch Definitions ──────────────────────────────────────────────

function buildPatches() {
  const patches = [];

  // 1. Context window
  const ctxWindow = getArg("context-window") || (applyAll ? "262000" : null);
  if (ctxWindow) {
    const val = parseInt(ctxWindow, 10);
    if (isNaN(val) || val < 100000 || val > 999999) {
      console.error("ERROR: --context-window must be a 6-digit number (100000-999999)");
      console.error("       For 1M+, use model name with [1m] suffix instead.");
      process.exit(1);
    }
    patches.push({
      name: `Context window: 200000 -> ${val}`,
      find: Buffer.from("uJ7=200000,"),
      replace: Buffer.from(`uJ7=${val},`),
      description: "Default context window size for non-[1m] models",
    });
  }

  // 2. Max output token upper limit (requires same byte length)
  const maxOutput = getArg("max-output");
  if (maxOutput) {
    const val = parseInt(maxOutput, 10);
    if (isNaN(val) || val < 4096) {
      console.error("ERROR: --max-output must be >= 4096");
      process.exit(1);
    }
    // Patch the opus-4-6 upper limit: q=128000 -> q=<val>
    // Must be same byte length. 128000 = 6 chars
    const valStr = String(val);
    if (valStr.length !== 6) {
      console.error("ERROR: --max-output must be exactly 6 digits for binary patching (100000-999999)");
      process.exit(1);
    }
    patches.push({
      name: `Max output upper limit (opus-4-6): 128000 -> ${val}`,
      find: Buffer.from('opus-4-6")$=64000,q=128000'),
      replace: Buffer.from(`opus-4-6")$=64000,q=${valStr}`),
      description: "Upper limit for CLAUDE_CODE_MAX_OUTPUT_TOKENS on opus-4-6",
    });
    patches.push({
      name: `Max output upper limit (sonnet-4-6): 128000 -> ${val}`,
      find: Buffer.from('sonnet-4-6")$=32000,q=128000'),
      replace: Buffer.from(`sonnet-4-6")$=32000,q=${valStr}`),
      description: "Upper limit for CLAUDE_CODE_MAX_OUTPUT_TOKENS on sonnet-4-6",
    });
  }

  // 3. Autocompact buffer
  const acBuffer = getArg("autocompact-buffer");
  if (acBuffer) {
    const val = parseInt(acBuffer, 10);
    const valStr = String(val);
    // Original is j6$=13000 (5 chars for number)
    if (valStr.length !== 5) {
      console.error("ERROR: --autocompact-buffer must be exactly 5 digits (10000-99999)");
      process.exit(1);
    }
    patches.push({
      name: `Autocompact buffer: 13000 -> ${val}`,
      find: Buffer.from("j6$=13000,"),
      replace: Buffer.from(`j6$=${valStr},`),
      description: "Token buffer reserved for autocompact threshold calculation",
    });
  }

  // 4. Summary max tokens
  const summaryMax = getArg("summary-max");
  if (summaryMax) {
    const val = parseInt(summaryMax, 10);
    const valStr = String(val);
    if (valStr.length !== 5) {
      console.error("ERROR: --summary-max must be exactly 5 digits (10000-99999)");
      process.exit(1);
    }
    patches.push({
      name: `Summary max tokens: 40000 -> ${val}`,
      find: Buffer.from("maxTokens:40000"),
      replace: Buffer.from(`maxTokens:${valStr}`),
      contextCheck: "minTokens:",
      description: "Maximum tokens for autocompact summary output",
    });
  }

  return patches;
}

// ─── Helpers ─────────────────────────────────────────────────────────
function findAllOccurrences(buf, pattern) {
  const offsets = [];
  let idx = 0;
  while ((idx = buf.indexOf(pattern, idx)) !== -1) {
    offsets.push(idx);
    idx += 1;
  }
  return offsets;
}

function contextWindow(buf, offset, pattern, contextStr, windowSize = 300) {
  const start = Math.max(0, offset - windowSize);
  const end = Math.min(buf.length, offset + pattern.length + windowSize);
  const slice = buf.slice(start, end).toString("utf8");
  return slice.includes(contextStr);
}

// ─── Main ────────────────────────────────────────────────────────────
(function main() {
  console.log("=== Claude Code Binary Patcher ===");
  console.log(`Binary: ${TARGET}`);
  console.log(`Size:   ${(fs.statSync(TARGET).size / 1e6).toFixed(1)} MB`);
  console.log();

  // Restore mode
  if (hasFlag("restore")) {
    if (!fs.existsSync(BACKUP)) {
      console.error("ERROR: No backup found at", BACKUP);
      process.exit(1);
    }
    try {
      fs.copyFileSync(BACKUP, TARGET);
      console.log("Restored original from backup.");
    } catch (err) {
      if (err.code === "EBUSY" || err.code === "EPERM") {
        console.log("Binary is locked. Close Claude Code first, then retry.");
      } else throw err;
    }
    return;
  }

  // Build patches
  const patches = buildPatches();
  if (patches.length === 0) {
    console.log("No patches specified. Use --help to see options.");
    process.exit(0);
  }

  // Backup
  if (!fs.existsSync(BACKUP)) {
    console.log("Creating backup ->", BACKUP);
    fs.copyFileSync(TARGET, BACKUP);
  } else {
    console.log("Backup exists at", BACKUP);
  }

  const dryRun = hasFlag("dry-run");
  let buf = fs.readFileSync(TARGET);
  let totalPatched = 0;

  console.log();
  for (const patch of patches) {
    console.log(`--- ${patch.name} ---`);

    // Check if already patched (replacement pattern exists)
    const alreadyPatched = findAllOccurrences(buf, patch.replace);
    if (alreadyPatched.length > 0) {
      console.log(`  Already patched (${alreadyPatched.length} occurrence(s))`);
      console.log();
      continue;
    }

    const occurrences = findAllOccurrences(buf, patch.find);
    if (occurrences.length === 0) {
      if (patch.skip) {
        console.log("  Skipped (pattern not found, likely covered by another patch)");
      } else {
        console.error("  WARNING: Pattern not found. Binary version may differ.");
        console.error("  Pattern:", patch.find.toString("utf8").substring(0, 60));
      }
      console.log();
      continue;
    }

    let patchedCount = 0;
    for (const offset of occurrences) {
      if (patch.contextCheck && !contextWindow(buf, offset, patch.find, patch.contextCheck)) {
        console.log(`  Offset ${offset}: context check failed, skipping`);
        continue;
      }

      if (dryRun) {
        console.log(`  [DRY RUN] Would patch at offset ${offset}`);
      } else {
        patch.replace.copy(buf, offset);
        console.log(`  Patched at offset ${offset}`);
      }
      patchedCount++;
    }

    console.log(`  ${patchedCount}/${occurrences.length} occurrence(s) ${dryRun ? "found" : "patched"}`);
    console.log();
    totalPatched += patchedCount;
  }

  if (dryRun) {
    console.log(`Dry run complete. ${totalPatched} patch point(s) found.`);
    return;
  }

  if (totalPatched === 0) {
    console.log("No patches applied (all may already be applied or patterns changed).");
    process.exit(0);
  }

  // Write
  const TEMP = TARGET + ".patched";
  let writtenTo;
  try {
    fs.writeFileSync(TARGET, buf);
    writtenTo = TARGET;
    console.log(`Wrote patched binary -> ${TARGET}`);
  } catch (err) {
    if (err.code === "EBUSY" || err.code === "EPERM") {
      fs.writeFileSync(TEMP, buf);
      writtenTo = TEMP;
      console.log(`Binary is locked. Wrote to: ${TEMP}`);
      console.log();
      console.log("To finish:");
      console.log("  1. Close all Claude Code instances");
      if (process.platform === "win32") {
        console.log(`  2. Copy-Item -Force "${TEMP}" "${TARGET}"`);
      } else {
        console.log(`  2. cp "${TEMP}" "${TARGET}"`);
      }
      console.log("  3. Relaunch Claude Code");
    } else throw err;
  }

  // Verify
  console.log("\n=== Verification ===");
  const verify = fs.readFileSync(writtenTo);
  let allOk = true;
  for (const patch of patches) {
    if (patch.skip) continue;
    const found = findAllOccurrences(verify, patch.replace);
    const old = findAllOccurrences(verify, patch.find);
    const ok = found.length > 0;
    if (!ok && old.length === 0) continue; // pattern gone due to another patch
    const status = ok ? "OK" : "FAIL";
    if (!ok) allOk = false;
    console.log(`[${status}] ${patch.name}`);
  }
  console.log(allOk ? "\nAll patches verified." : "\nSome patches may need review.");
  console.log(`\nRestore: node ${__filename} --restore`);
})();
