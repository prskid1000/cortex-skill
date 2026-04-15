# Claude Desktop Custom 3P (BYOM) Toggler

Script: `~/.claude/skills/claude-claw/scripts/claude-desktop-3p.py`

## What It Does

Activates Claude Desktop's built-in **Custom 3P** (third-party / BYOM)
deployment mode by writing Windows registry policies — no binary modification,
no asar repack. 3P mode bypasses the claude.ai login flow, serves a synthetic
Pro org with `capabilities: ["chat", "claude_pro"]` from local stub responses,
and routes inference to a user-specified gateway URL. Unlocks Cowork + Claude
Code surfaces in the UI on free Anthropic accounts.

## Why It's Needed

Claude Desktop's main UI is a webview of `https://claude.ai`. The Cowork/Code
tabs are gated by `account.capabilities`, which the claude.ai backend sets
based on subscription tier. Free accounts never see those tabs.

3P mode is Anthropic's own enterprise/BYOM deployment path — designed for
companies who want their employees to use Claude Desktop against an internal
LLM gateway. When activated, the Electron shell:

1. Skips claude.ai OAuth entirely.
2. Intercepts `/api/bootstrap`, `/api/account`, `/api/account_profile`,
   `/api/account/settings` etc. and returns synthetic data (function `DPe()`
   in `index.js` constructs a fake `account` object via `MRn()` → `BRn()`).
3. Constructs a fake org named `"Cowork 3P"` with `capabilities: ["chat",
   "claude_pro"]` — this is what unlocks the UI.
4. Routes the agent loop through `inferenceGatewayBaseUrl`, not
   `api.anthropic.com`.
5. Logs `[custom-3p] 3P mode active {provider: "..."}` on successful entry.

The script just writes the registry values that trigger this flow.

## Requirements

- **Windows** with Claude Desktop installed via MSIX (Microsoft Store or
  direct `.msix` install). The MSIX detection in `index.js` (`fu()` function)
  is what enables registry policy reading.
- **HTTPS gateway URL.** The schema validator
  (`N8 = ke().trim().url().refine(t => new URL(t).protocol === "https:",
  {message: "must use https"})`) rejects `http://`. For local-only testing
  expose telecode via Tailscale Funnel — telecode auto-starts it.
- **Admin privileges** for HKLM writes. The script triggers UAC. HKCU
  Policies subtree is also ACL-restricted on most Windows installs, so HKCU
  writes also require admin via the same UAC prompt.
- **Both HKCU + HKLM hives written.** MSIX merges both views and either can
  satisfy the policy read; we set both to be safe across user/system
  configurations.

## Usage

```bash
# Show current 3P state (no UAC needed)
python ~/.claude/skills/claude-claw/scripts/claude-desktop-3p.py status

# Enable — auto-detects Tailscale Funnel URL + uses defaults
python ~/.claude/skills/claude-claw/scripts/claude-desktop-3p.py enable

# Enable with explicit URL / model / org UUID
python ~/.claude/skills/claude-claw/scripts/claude-desktop-3p.py enable \
    --url https://my-gateway.example.com \
    --model my-local-model-id \
    --api-key arbitrary-string \
    --org-uuid 00000000-0000-0000-0000-000000000000

# Disable (deletes the policy keys, returns to 1P claude.ai login)
python ~/.claude/skills/claude-claw/scripts/claude-desktop-3p.py disable
```

After enable/disable, **fully quit Claude Desktop and relaunch**. Mode
detection (`yYr()` → `Rjt()` → `ks()` chain) only runs once at startup;
config changes mid-session aren't picked up.

## Verifying It Worked

The deployment-mode logger writes to
`C:\Users\<user>\AppData\Roaming\Claude\logs\main.log`.

| Log line | Meaning |
|---|---|
| `[custom-3p] 3P mode active {provider: "gateway"}` | ✅ Working — synthetic Pro account active |
| `[custom-3p] Credentials read failed, staying in 1P mode: <reason>` | ⚠️ Config validation rejected — see reason |
| `Enterprise config loaded: { ... inferenceProvider: 'gateway' ... }` | Debug-level; confirms registry was read |
| (no `[custom-3p]` at all) | Registry empty OR `Ijt()` not called — see [Recovery](#recovery-when-it-stops-working) |

Common rejection reasons in the error message:

| Message fragment | Cause | Fix |
|---|---|---|
| `baseUrl: must use https` | Gateway URL is `http://` | Use HTTPS (Tailscale Funnel, ngrok, real cert) |
| `either inferenceGatewayApiKey or inferenceCredentialHelper must be set` | API key field empty | Set any non-empty string |
| `inferenceProvider "X" is not recognized` | Provider name typo | Must be `gateway` / `vertex` / `bedrock` / `foundry` |
| `Invalid custom3p enterprise config: <field>: <zod error>` | Schema validation failure | Read the path, inspect that specific field |

For verbose detail, set debug logging in your launch wrapper:
```bat
set DESKTOP_LOG_LEVEL=debug
set CLAUDE_ENABLE_LOGGING=1
set DEBUG=custom-3p:*,account:*,oauth:*
```
(Already in `wrappers/claudedl.bat` — uncomment to enable.)

## Registry Schema

All values are `REG_SZ` strings under both `HKCU\SOFTWARE\Policies\Claude` and
`HKLM\SOFTWARE\Policies\Claude`. The registry path comes from
`SOFTWARE\Policies\${app.getName()}` where `app.getName()` returns `"Claude"`
(the `productName` from the app's `package.json` — stable across versions).

| Value | Type | Required | Purpose |
|---|---|---|---|
| `inferenceProvider` | string | yes | `gateway` / `vertex` / `bedrock` / `foundry` — flips on 3P mode |
| `inferenceGatewayBaseUrl` | URL string (https://) | yes (gateway) | Where chat/agent traffic goes |
| `inferenceGatewayApiKey` | any string | yes (gateway, unless helper set) | Sent as Bearer; telecode ignores |
| `inferenceCredentialHelper` | command string | alt to apiKey | Spawned to mint a fresh token (less common) |
| `fallbackModels` | JSON-array string | recommended | e.g. `["qwen3.5-35b-a3b"]` — what the model picker shows |
| `deploymentOrganizationUuid` | UUID string | optional | Synthetic org UUID (placeholder OK) |
| `managedMcpServers` | JSON-array string | optional | MCP servers preloaded into Cowork sessions |
| `forceLoginOrgUUID` | UUID/JSON-array string | optional | Restricts login to specific org (1P, not relevant for 3P) |

Other providers have their own field families:
- **Vertex:** `inferenceVertexProjectId`, `inferenceVertexRegion`,
  `inferenceVertexCredentialsFile`, `inferenceVertexBaseUrl`,
  `inferenceVertexOAuthClientId`, `inferenceVertexOAuthClientSecret`
- **Bedrock:** `inferenceBedrockBearerToken`, `inferenceBedrockBaseUrl`,
  AWS-region/profile fields
- **Foundry:** `inferenceFoundryResource`, `inferenceFoundryApiKey`

The complete schema lives in `app.asar/.vite/build/index.js` as the Zod
object `Ace = mt({...})`. Each field has a metadata object including
`scopes: ["3p"]` (3P-only) or `scopes: ["3p","1p"]` (both modes).

## After Claude Desktop Updates

The MSIX install path changes per version (e.g. `Claude_1.2581.0.0_x64__pzs8sxrjxfjjc`),
but registry policies are **independent of the install path** — no re-run needed
after updates unless Anthropic changes the schema (rare; this is their public
enterprise contract).

The `claudedl.bat` launcher uses `Get-AppxPackage -Name 'Claude'` to find the
new install path dynamically, so it survives updates too.

```bash
# Confirm 3P still active after an update
python ~/.claude/skills/claude-claw/scripts/claude-desktop-3p.py status
# Then quit + relaunch and check main.log for the [custom-3p] line
```

## Recovery When It Stops Working

If after a Claude Desktop update 3P stops working, walk this checklist:

### 1. Confirm registry survived
```bash
python ~/.claude/skills/claude-claw/scripts/claude-desktop-3p.py status
```
If keys are missing (the script prints `(empty)`), re-run `enable`.

### 2. Confirm gateway is reachable
```bash
# From PowerShell
Invoke-WebRequest https://your-gateway.ts.net/v1/models -UseBasicParsing | Select -ExpandProperty Content
# Should return a JSON model list. If 404 / connection refused, telecode/Tailscale isn't running.
```

### 3. Read the latest startup log
```bash
# The interesting window is the last "Starting app" entry forward
grep -n "Starting app\|custom-3p\|Enterprise config\|inferenceProvider" \
    "$APPDATA/Claude/logs/main.log" | tail -30
```
Decision tree:
- See `[custom-3p] 3P mode active` → working; problem is elsewhere (UI, network).
- See `[custom-3p] Credentials read failed: <reason>` → schema validation issue.
  Look up the reason in the [verifying table](#verifying-it-worked) above.
- See `Enterprise config loaded: ...` (debug only) but no `[custom-3p]` line →
  config was read but had no `inferenceProvider`. Registry write didn't land
  where the app reads — check `app.getName()` matches `Claude` (it should
  unless Anthropic renamed the product).
- No `Enterprise config loaded` at all (with debug on) → `Ijt()` wasn't called
  this startup. Likely a build that disabled enterprise config reading; check
  if `yYr()` is still invoked at app boot (search `app.asar/.vite/build/index.js`
  for `yYr(`).

### 4. Verify the schema field names didn't change

```bash
# Extract app.asar to a temp directory
mkdir -p /tmp/claude-desktop-extract
cd /tmp/claude-desktop-extract
APP_DIR=$(powershell -NoProfile -Command "(Get-AppxPackage -Name 'Claude').InstallLocation")
npx -y @electron/asar extract "$APP_DIR/app/resources/app.asar" ./app

# Find the Zod schema for enterprise config
node -e '
const fs=require("fs");
const s=fs.readFileSync("./app/.vite/build/index.js","utf8");
// Find all 3P-scoped field declarations
for (const m of s.matchAll(/([a-zA-Z]+):Ui\([^)]+,\{scopes:\["3p"[^}]*\}/g)) {
  console.log(m[1]);
}
' | sort -u
```

This prints every field name with `scopes:["3p"]` — compare to the `FIELDS`
tuple in `claude-desktop-3p.py` and the table in this doc. If a field was
renamed:
1. Update `FIELDS` in the script.
2. Update the table in this doc.
3. Re-run `enable`.

If 3P mode itself was removed (no fields with `scopes:["3p"]`), the script
no longer applies — Anthropic killed the BYOM path. Time to revisit the
asar-patch approach instead.

### 5. Verify the registry path didn't move

```bash
# In the extracted source:
grep -o 'SOFTWARE\\\\Policies\\\\\${[^}]*}' app/.vite/build/index.js | head
```
Should print `SOFTWARE\\Policies\\${...}` where `...` resolves to
`app.getName()` → `"Claude"`. If they hardcoded a different path, update
`KEY_PATH` in the script.

### 6. Verify the deployment-mode detector is still called

```bash
grep -o 'yYr({[^}]*' app/.vite/build/index.js
```
The function name (`yYr`) is minified and **does change** across versions —
but it'll always be a single-character or short identifier called once at
boot, with the signature `yYr({anthropicOriginUrl: ..., getApiHost: ...,
getOauthToken: ...})`. To find the new name in a future version, search for
that argument shape:
```bash
grep -oP '[a-zA-Z_$]{1,4}\(\{anthropicOriginUrl:' app/.vite/build/index.js
```

If this returns nothing, the deployment-mode plumbing was refactored; deeper
investigation needed.

## Research Notes — How This Was Discovered

Trail of investigation, in order. Useful if a future Anthropic update breaks
the path and you need to find a new one.

### Dead-ends ruled out first

1. **`ANTHROPIC_BASE_URL` env var** — works for Claude Code CLI but does
   nothing for Claude Desktop's main chat. The chat flows through claude.ai's
   backend, not direct `/v1/messages` calls. Confirmed by reading
   `package.json` (`"description": "Desktop application for Claude.ai"`) and
   tracing `loadURL` calls in `index.js` — they all use `jn()` which returns
   `https://claude.ai`.
2. **`CLAUDE_AI_URL` env var** — exists but gated behind
   `globalThis.isDeveloperApprovedDevUrlOverrideEnabled` (function `Z8()` at
   ~`@2345169`). That flag is never set in prod builds (`buildType === "prod"`
   is hardcoded in `package.json`).
3. **`CLAUDE_CODE_CUSTOM_OAUTH_URL`** — has an allowlist of 3 hardcoded URLs
   (`Ufn` array): `claude.fedstart.com`, `claude-staging.fedstart.com`,
   `beacon.claude-ai.staging.ant.dev`. Useless for arbitrary local URLs.
4. **`coworkScheduledTasksEnabled` / `ccdScheduledTasksEnabled` preferences** —
   set in `claude_desktop_config.json`, but the app **resets them to false on
   startup** when the entitlement check fails for a free account. Pure UI
   prefs, gated server-side.
5. **`sidebarMode: "code"` preference** — does set the load URL to
   `claude.ai/epitaxy`, but claude.ai redirects free users back to `/chat`.
   Confirmed in main.log: `Blocked permission check ... topFrameUrl:
   https://claude.ai/login?from=logout`.

### What surfaced 3P mode

Searching `index.js` for `"capabilities":["chat","claude_pro"]` led to function
`BRn(t)` at ~`@4964174`:
```js
function BRn(t) {
  return {
    uuid: t.orgUuid, id: 0, name: "Cowork 3P", settings: {},
    capabilities: ["chat", "claude_pro"],   // <-- the unlocking line
    billing_type: "stripe_subscription",
    rate_limit_tier: null,
    ...
  };
}
```
"Cowork 3P" is the name of the synthetic org. The constant `bne="-3p"` (used
as a path suffix for the 3P data dir) and the IPC namespace `Custom3pSetup`
both confirmed this is a first-party build-in.

### The activation chain

Tracing usage backward from `BRn`:
```
DPe(t, e)        — wraps BRn output in {account, locale, statsig, ...}
   ↓ called by
/api/account, /api/account_profile, /api/bootstrap, /edge-api/bootstrap stubs
   ↓ stubs activate when
yYr(t)           — at ~@2340676, the deployment-mode detector
   ↓ called once at startup with
yYr({anthropicOriginUrl: Z8, getApiHost: YWt, getOauthToken: JWt})
   ↓ which calls
Rjt()            — at ~@1588733, reads ks() and validates
   ↓ which checks
ks().inferenceProvider !== undefined
   ↓ where ks() is
Ijt() = Ajt() ⊕ Ejt()    — registry merge with JSON config
```

So: writing `inferenceProvider` to `HKCU/HKLM\SOFTWARE\Policies\Claude` causes
`Rjt()` to return non-null creds → `yYr()` instantiates the 3P manager (`hYr`
class at `@2331759`) → all `/api/*` claude.ai requests get stubbed → the React
UI sees a Pro org → tabs unlock.

### The HTTPS gotcha

First registry write used `http://localhost:1235`. main.log error:
```
[custom-3p] Credentials read failed, staying in 1P mode:
  Invalid custom3p enterprise config: baseUrl: must use https
```

Source of the check at `@1564016`:
```js
const N8 = ke().trim().url().refine(
  t => new URL(t).protocol === "https:",
  { message: "must use https" }
);
```
This is a hard refinement on the URL Zod validator — no env override, no
bypass flag. Solutions explored:
- Self-signed cert + local HTTPS proxy (works, adds dependency on stunnel/mitmproxy)
- mkcert-generated trusted local CA (works, more setup)
- **Tailscale Funnel** — telecode already auto-starts one when Tailscale is
  installed, exposing port 1235 at `https://<machine>.<tailnet>.ts.net`.
  Zero extra config, real cert, accepted by the validator. ← chose this

### MSIX registry virtualization concern (false alarm)

Initial worry: MSIX-packaged apps virtualize registry writes — does the app
see our `HKCU\SOFTWARE\Policies\Claude` writes or a sandboxed shadow? The
function `fu()` returns true (MSIX detected) and main.log shows
`[MSIX] Filesystem not virtualized` + `windowsStore=true`.

Verified by enabling `DESKTOP_LOG_LEVEL=debug` and watching for
`Enterprise config loaded: { inferenceProvider: 'gateway', ... }` — the values
were read correctly from real HKCU. So MSIX virtualization wasn't blocking
reads (only writes are virtualized; reads see the merged real+private view).

### Why both HKCU + HKLM

`Ajt()` at `@1584699` enumerates BOTH hives:
```js
for (const c of ["HKCU","HKLM"]) for (const l of cv) {
    r.push({hive: c, keyPath: e, valueName: l});
    ...
}
```
Either satisfies the read. We set both because:
- HKCU is per-user, doesn't survive new user accounts
- HKLM is system-wide, persists for all users
- Some MSIX configurations have stricter HKCU policy ACL — HKLM as fallback

### Schema source of truth

The complete enterprise-config schema lives in
`app.asar/.vite/build/index.js` as the Zod object `Ace = mt({...})` starting
around `@1566392`. Each field is wrapped in a `Ui(zodSchema, metadata)` call
where metadata includes `scopes`, `title`, `appMin`, `description`. To dump
all 3P fields:
```js
// Run after extracting app.asar:
const s = require("fs").readFileSync("./app/.vite/build/index.js", "utf8");
for (const m of s.matchAll(/([a-zA-Z]+):Ui\(([^,]+),\{[^}]*scopes:\["3p"[^}]*\}/g)) {
  console.log(m[1] + " — " + m[2].slice(0, 80));
}
```

### Useful debugging session

- Set `DESKTOP_LOG_LEVEL=debug` + `CLAUDE_ENABLE_LOGGING=1` in the launcher
- Tail `%APPDATA%\Claude\logs\main.log`
- Look for these landmark lines in order:
  1. `[MSIX] Package family from native API: Claude_pzs8sxrjxfjjc`
  2. `Enterprise config loaded: { ... }` (debug level — confirms registry read)
  3. `[custom-3p] 3P mode active {provider: "gateway"}` (info level — success)
- Absence of (2) → registry not read or `Ijt()` not called
- Absence of (3) but presence of (2) with no inferenceProvider → registry write
  didn't include the field
- (3) replaced by `[custom-3p] Credentials read failed: <reason>` → schema
  validation rejected; reason is in the message

## Limitations

- **Only Windows.** The script's `sys.platform != "win32"` guard exits early
  on macOS/Linux. Mac equivalent uses `defaults write
  com.anthropic.claudefordesktop` plist keys (function `bjt()` in
  `index.js`); Linux has no enterprise config reader at all.
- **Cowork marketplace surfaces** call out to claude.ai and fail silently —
  log line `No active account/org for marketplace operations` is harmless;
  the local Cowork session itself works.
- **Bundled Claude Code subprocesses** spawned by the desktop inherit env
  from the parent. Pair the registry policy with the `claudedl.bat` wrapper
  to also set `ANTHROPIC_BASE_URL` for those subprocesses.
- **Only the `gateway` provider has been tested.** Vertex/Bedrock/Foundry
  paths exist in the schema and would be configured analogously, but they
  haven't been exercised here.
- **Schema is Anthropic's public enterprise contract**, but it could change
  with no notice — that's why this doc has a [Recovery](#recovery-when-it-stops-working)
  section.
