#!/usr/bin/env node
/**
 * Claude Code Binary Patcher v2 — Foolproof Edition
 * Finds constants by VALUE + structural context, not minified variable names.
 *
 * Usage:
 *   node claude-patcher.js --all              Apply all default patches
 *   node claude-patcher.js --scan             Show discovered constants
 *   node claude-patcher.js --context-window 300000
 *   node claude-patcher.js --max-output 256000
 *   node claude-patcher.js --autocompact 20000
 *   node claude-patcher.js --summary-max 80000
 *   node claude-patcher.js --restore          Restore from backup
 *   node claude-patcher.js --dry-run          Preview only
 */

const fs = require("fs");
const path = require("path");

// ─── CLI ────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const flag = (n) => args.includes(`--${n}`);
const arg = (n) => { const i = args.indexOf(`--${n}`); return i >= 0 ? args[i + 1] : null; };

if (flag("help") || args.length === 0) {
  console.log(`
Claude Code Binary Patcher v2

  --all                  Apply all patches with defaults
  --scan                 Show discovered constants (no changes)
  --context-window <N>   Context window size (6 digits, default: 262000)
  --max-output <N>       Max output token upper limit (6 digits)
  --autocompact <N>      Autocompact buffer reserve (5 digits)
  --summary-max <N>      Summary max tokens (5 digits)
  --restore              Restore original binary from backup
  --dry-run              Preview patches without writing
  --binary <path>        Override binary path
  --help                 Show this help
`);
  process.exit(0);
}

// ─── Find binary ────────────────────────────────────────────────────
function findBinary() {
  const home = process.env.HOME || process.env.USERPROFILE;
  const try_ = [
    arg("binary"),
    path.join(home, ".local", "bin", "claude.exe"),
    path.join(home, ".local", "bin", "claude"),
  ].filter(Boolean);
  for (const p of try_) if (fs.existsSync(p)) return p;
  try {
    const cmd = process.platform === "win32" ? "where claude" : "which claude";
    const r = require("child_process").execSync(cmd, { encoding: "utf8" }).trim().split("\n")[0];
    if (r && fs.existsSync(r)) return r;
  } catch {}
  return null;
}

const BIN = findBinary();
if (!BIN) { console.error("ERROR: Cannot find claude binary. Use --binary <path>"); process.exit(1); }
const BAK = BIN + ".bak";

// ─── Restore ────────────────────────────────────────────────────────
if (flag("restore")) {
  if (!fs.existsSync(BAK)) { console.error("No backup found at", BAK); process.exit(1); }
  try { fs.copyFileSync(BAK, BIN); console.log("Restored from backup."); }
  catch (e) { console.error(e.code === "EBUSY" ? "Binary locked — close Claude first." : e.message); }
  process.exit(0);
}

// ─── Read binary ────────────────────────────────────────────────────
console.log("=== Claude Code Binary Patcher v2 ===");
console.log(`Binary: ${BIN} (${(fs.statSync(BIN).size / 1e6).toFixed(1)} MB)\n`);
const buf = fs.readFileSync(BIN);
const txt = buf.toString("utf8");

// ─── Discovery helpers ──────────────────────────────────────────────
function allIndexes(str, sub) {
  const r = []; let i = 0;
  while ((i = str.indexOf(sub, i)) !== -1) { r.push(i); i++; }
  return r;
}

function ctx(offset, before, after) {
  return txt.slice(Math.max(0, offset - before), offset + after);
}

// ─── Discover by value + structural anchor ──────────────────────────
function discover() {
  const found = {};

  // 1. CONTEXT WINDOW — find VAR=<6 digits>, where "return VAR}" sits in a function with "return 1e6"
  //    Value-agnostic: works for original (200000) and patched (e.g. 262000) states.
  {
    const retRe = /return ([a-zA-Z_$][a-zA-Z0-9_$]*)\}/g;
    const candidates = new Set();
    let rm;
    while ((rm = retRe.exec(txt)) !== null) {
      const funcCtx = txt.slice(Math.max(0, rm.index - 500), rm.index);
      if (funcCtx.includes("return 1e6")) candidates.add(rm[1]);
    }
    const hits = [];
    for (const varName of candidates) {
      const esc = varName.replace(/[$]/g, "\\$");
      const re = new RegExp(`${esc}=(\\d{6}),`, "g");
      let m;
      while ((m = re.exec(txt)) !== null) {
        hits.push({ varName, value: parseInt(m[1], 10), offset: m.index, pattern: `${varName}=${m[1]},` });
      }
    }
    if (hits.length >= 2) {
      found.contextWindow = { value: hits[0].value, digits: 6, hits, default: 262000,
        original: 200000, desc: "Context window default" };
    }
  }

  // 2. MAX OUTPUT — find =128000 after model name includes("opus-4-6") or includes("sonnet-4-6")
  //    Anchor: model name strings that never change
  {
    const re = /includes\("(opus-4-6|sonnet-4-6)"\)\)([a-zA-Z_$][a-zA-Z0-9_$]*)=(\d+),([a-zA-Z_$][a-zA-Z0-9_$]*)=(\d+)/g;
    let m, hits = [];
    while ((m = re.exec(txt)) !== null) {
      const upper = parseInt(m[5], 10);
      hits.push({
        model: m[1], offset: m.index, upperValue: upper,
        full: m[0], // the exact match for replacement
        defaultVar: m[2], defaultVal: m[3], upperVar: m[4], upperVal: m[5],
      });
    }
    if (hits.length >= 2) {
      found.maxOutput = { hits, desc: "Max output token upper limits" };
    }
  }

  // 3. AUTOCOMPACT BUFFER — target var is always declared immediately after "=1e6,"
  //    inside a cluster containing "=3000," and "autocompact". This is the stable
  //    structural anchor across Claude Code versions (var names are minified & unstable).
  {
    const re = /=1e6,([a-zA-Z_$][a-zA-Z0-9_$]*)=(\d{4,5}),/g;
    let m, hits = [];
    while ((m = re.exec(txt)) !== null) {
      const c = ctx(m.index, 300, 300);
      if (!c.includes("=3000,") || !c.includes("autocompact")) continue;
      const off = m.index + "=1e6,".length;
      hits.push({ varName: m[1], value: parseInt(m[2], 10), offset: off, pattern: `${m[1]}=${m[2]},` });
    }
    if (hits.length >= 2) {
      found.autocompact = { value: hits[0].value, digits: String(hits[0].value).length,
        hits, default: 20000, original: 13000, desc: "Autocompact buffer reserve" };
    }
  }

  // 4. SUMMARY MAX — find VAR=40000 immediately after the system-prompt override string
  //    Anchor: the literal CLAUDE.md instruction string is stable and unique across versions
  {
    const re = /exactly as written\.",([a-zA-Z_$][a-zA-Z0-9_$]*)=(\d{4,5}),/g;
    let m, hits = [];
    while ((m = re.exec(txt)) !== null) {
      const off = m.index + m[0].length - (m[1].length + 1 + m[2].length + 1);
      hits.push({ varName: m[1], offset: off, value: parseInt(m[2], 10),
        pattern: `${m[1]}=${m[2]},` });
    }
    if (hits.length >= 2) {
      found.summaryMax = { value: hits[0].value, digits: String(hits[0].value).length,
        hits, default: 80000, original: 40000, desc: "Summary max tokens" };
    }
  }

  return found;
}

const d = discover();

// ─── Scan mode ──────────────────────────────────────────────────────
if (flag("scan")) {
  console.log("=== Discovered Constants ===\n");
  const stateLabel = (info) => {
    const v = info.value ?? info.hits[0]?.upperValue;
    if (v == null) return "";
    if (info.default != null && v === info.default) return " (patched — at default)";
    if (info.original != null && v === info.original) return " (original — unpatched)";
    if (info.original != null && v !== info.original) return " (patched — custom)";
    return "";
  };
  const show = (key, info) => {
    if (!info) { console.log(`${key}: NOT FOUND\n`); return; }
    console.log(`${info.desc}:`);
    const v = info.value ?? info.hits[0]?.upperValue ?? "?";
    console.log(`  Current value: ${v}${stateLabel(info)}`);
    console.log(`  Occurrences:   ${info.hits.length}`);
    for (const h of info.hits) {
      console.log(`  @ offset ${h.offset}: ${h.pattern || h.full || ""}`);
    }
    console.log();
  };
  show("contextWindow", d.contextWindow);
  show("maxOutput", d.maxOutput);
  show("autocompact", d.autocompact);
  show("summaryMax", d.summaryMax);

  const missing = ["contextWindow", "maxOutput", "autocompact", "summaryMax"].filter(k => !d[k]);
  if (missing.length) console.log(`WARNING: Could not find: ${missing.join(", ")}`);
  process.exit(0);
}

// ─── Build patches ──────────────────────────────────────────────────
const patches = [];
const all = flag("all");
const dry = flag("dry-run");

// Context window
{
  const val = arg("context-window") || (all ? "262000" : null);
  if (val && d.contextWindow) {
    const n = parseInt(val, 10);
    if (String(n).length !== d.contextWindow.digits) {
      console.error(`ERROR: --context-window must be ${d.contextWindow.digits} digits`); process.exit(1);
    }
    for (const h of d.contextWindow.hits) {
      patches.push({ name: `Context window ${h.offset}`, find: h.pattern, replace: `${h.varName}=${n},` });
    }
  } else if (val && !d.contextWindow) {
    console.error("ERROR: Context window constant not found in binary"); process.exit(1);
  }
}

// Max output
{
  const val = arg("max-output") || (all ? null : null); // no default for --all, too model-specific
  if (val && d.maxOutput) {
    const n = parseInt(val, 10);
    for (const h of d.maxOutput.hits) {
      if (String(n).length !== h.upperVal.length) {
        console.error(`ERROR: --max-output must be ${h.upperVal.length} digits for ${h.model}`); process.exit(1);
      }
      const newFull = h.full.replace(new RegExp(`${h.upperVar}=${h.upperVal}`), `${h.upperVar}=${n}`);
      patches.push({ name: `Max output (${h.model}) ${h.offset}`, find: h.full, replace: newFull });
    }
  } else if (val && !d.maxOutput) {
    console.error("ERROR: Max output constants not found in binary"); process.exit(1);
  }
}

// Autocompact buffer
{
  const val = arg("autocompact") || (all ? String(d.autocompact?.default ?? 20000) : null);
  if (val && d.autocompact) {
    const n = parseInt(val, 10);
    if (String(n).length !== d.autocompact.digits) {
      console.error(`ERROR: --autocompact must be ${d.autocompact.digits} digits`); process.exit(1);
    }
    for (const h of d.autocompact.hits) {
      patches.push({ name: `Autocompact buffer ${h.offset}`, find: h.pattern, replace: `${h.varName}=${n},` });
    }
  } else if (val && !d.autocompact) {
    console.error("ERROR: Autocompact buffer not found in binary"); process.exit(1);
  }
}

// Summary max
{
  const val = arg("summary-max") || (all ? String(d.summaryMax?.default ?? 80000) : null);
  if (val && d.summaryMax) {
    const n = parseInt(val, 10);
    if (String(n).length !== d.summaryMax.digits) {
      console.error(`ERROR: --summary-max must be ${d.summaryMax.digits} digits`); process.exit(1);
    }
    for (const h of d.summaryMax.hits) {
      patches.push({ name: `Summary max ${h.offset}`, find: h.pattern, replace: `${h.varName}=${n},` });
    }
  } else if (val && !d.summaryMax) {
    console.error("ERROR: Summary max not found in binary"); process.exit(1);
  }
}

if (patches.length === 0) { console.log("Nothing to patch."); process.exit(0); }

// ─── Backup ─────────────────────────────────────────────────────────
if (!fs.existsSync(BAK)) {
  fs.copyFileSync(BIN, BAK);
  console.log(`Backup -> ${BAK}`);
} else {
  console.log(`Backup at ${BAK}`);
}

// ─── Apply ──────────────────────────────────────────────────────────
// Deduplicate patches by find string, then patch ALL occurrences
const uniquePatches = new Map();
for (const p of patches) {
  if (!uniquePatches.has(p.find)) uniquePatches.set(p.find, p);
}

let total = 0;
for (const [, p] of uniquePatches) {
  const findBuf = Buffer.from(p.find);
  const replaceBuf = Buffer.from(p.replace);

  // Find ALL occurrences
  const offsets = [];
  let searchFrom = 0;
  while (true) {
    const idx = buf.indexOf(findBuf, searchFrom);
    if (idx === -1) break;
    offsets.push(idx);
    searchFrom = idx + findBuf.length;
  }

  if (offsets.length === 0) {
    // Check if already patched
    if (buf.indexOf(replaceBuf) !== -1) {
      console.log(`[SKIP] ${p.name} — already patched`);
    } else {
      console.log(`[MISS] ${p.name} — pattern not found`);
    }
    continue;
  }

  for (const off of offsets) {
    if (dry) {
      console.log(`[DRY]  ${p.name} @ ${off}`);
    } else {
      replaceBuf.copy(buf, off);
      console.log(`[OK]   ${p.name} @ ${off}`);
    }
    total++;
  }
}

if (dry) { console.log(`\nDry run: ${total} patch points.`); process.exit(0); }
if (total === 0) { console.log("\nNo new patches applied."); process.exit(0); }

// ─── Write ──────────────────────────────────────────────────────────
const TMP = BIN + ".patched";
try {
  fs.writeFileSync(BIN, buf);
  console.log(`\nWritten -> ${BIN}`);
} catch (e) {
  if (e.code === "EBUSY" || e.code === "EPERM") {
    fs.writeFileSync(TMP, buf);
    console.log(`\nBinary locked. Written -> ${TMP}`);
    console.log(`Close Claude, then:\n  ${process.platform === "win32"
      ? `Copy-Item -Force "${TMP}" "${BIN}"`
      : `cp "${TMP}" "${BIN}"`}`);
  } else throw e;
}

// ─── Verify ─────────────────────────────────────────────────────────
console.log("\n=== Verify ===");
const v = fs.readFileSync(fs.existsSync(TMP) && !fs.existsSync(BIN) ? TMP : BIN);
let ok = 0, fail = 0;
for (const p of patches) {
  const found = v.indexOf(Buffer.from(p.replace)) !== -1;
  console.log(`[${found ? "OK" : "FAIL"}] ${p.name}`);
  found ? ok++ : fail++;
}
console.log(`\n${ok} OK, ${fail} failed. Restore: node ${__filename} --restore`);
