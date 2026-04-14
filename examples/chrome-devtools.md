# Chrome DevTools MCP — Browser Launch Examples

## Contents

- [1. Launch Edge with User's Real Profile](#1-launch-edge-with-users-real-profile)
- [2. Launch Edge with a Throwaway Profile](#2-launch-edge-with-a-throwaway-profile)
- [3. Diagnose: Port Won't Open](#3-diagnose-port-wont-open)

> **API reference:** See [references/chrome-devtools.md](../references/chrome-devtools.md)

---

## 1. Launch Edge with User's Real Profile

Use when the user wants to drive their already-logged-in browser session (AWS console, GitHub, etc.).

```bash
# Step 1 — kill every Edge process. The default-profile data dir is locked
# while any process holds it, including background helpers.
taskkill //F //IM msedge.exe

# Step 2 — launch with the default profile + debug port
"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:/Users/$USER/AppData/Local/Microsoft/Edge/User Data" &

# Step 3 — verify the port is open before any MCP call
curl -s http://127.0.0.1:9222/json/version
```

Then call `mcp__...__list_pages` to attach.

---

## 2. Launch Edge with a Throwaway Profile

Use for automated testing or when no existing session is needed. Does not require killing anything.

```bash
"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:/temp/edge-debug" &

curl -s http://127.0.0.1:9222/json/version
```

The fresh profile starts at the welcome screen — log in to whatever the task needs.

---

## 3. Diagnose: Port Won't Open

Symptom: `curl http://127.0.0.1:9222/json/version` exits with code 7, or the MCP returns "Could not connect to Chrome".

```bash
# Check if any browser process slipped through — they all need to die
tasklist | grep -i msedge

# If the launch command exited instantly (within ~1 second), it attached
# to an existing instance and ignored --remote-debugging-port. Solution:
# kill everything and re-launch with --user-data-dir set.
taskkill //F //IM msedge.exe
"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:/temp/edge-debug" &

# Re-verify
curl -s http://127.0.0.1:9222/json/version
```

The `--user-data-dir` flag is what forces a separate browser process group; without it the OS reuses the existing one.
