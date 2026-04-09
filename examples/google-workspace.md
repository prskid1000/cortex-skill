# Google Workspace — Working Examples

Complete, runnable code blocks for Google Docs, Sheets, Slides, Gmail, and Calendar via `gws` CLI.

---

## Google Docs (gws CLI)

### Create and Populate a Formatted Google Doc

Creates a Google Doc with headings, paragraphs, and styled sections using `batchUpdate`. Handles Windows shell escaping and chunking.

```python
import subprocess
import shutil
import json
import time

NODE = shutil.which("node")
# Find your path: cat "$(which gws)" — look for the run-gws.js path
GWS_JS = "C:/nvm4w/nodejs/node_modules/@googleworkspace/cli/run-gws.js"

def gws_run(*args):
    """Call gws directly via node (bypasses .CMD shim, avoids shell escaping)."""
    r = subprocess.run([NODE, GWS_JS] + list(args),
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    out = r.stdout
    if out.startswith("Using keyring"):
        out = out[out.index("\n")+1:]
    return json.loads(out) if out.strip() else None

def batch_update(doc_id, requests):
    """Send batchUpdate requests to a Google Doc."""
    return gws_run('docs', 'documents', 'batchUpdate',
                   '--params', json.dumps({"documentId": doc_id}),
                   '--json', json.dumps({"requests": requests}))

# Step 1: Create the document
result = gws_run('docs', 'documents', 'create',
                 '--json', json.dumps({"title": "My Report"}))
doc_id = result["documentId"]
tab_id = "t.0"  # Default tab for newly created docs

# Step 2: Build content as (style, text) pairs
# Styles: TITLE, SUBTITLE, HEADING_1, HEADING_2, HEADING_3, NORMAL (no style change)
sections = [
    ("TITLE",    "Quarterly Report\n"),
    ("SUBTITLE", "Q1 2026 | Engineering Team\n"),
    ("NORMAL",   "\n"),
    ("HEADING_1", "1. Summary\n"),
    ("NORMAL",   "Revenue grew 15% quarter-over-quarter.\n\n"),
    ("HEADING_1", "2. Key Metrics\n"),
    ("HEADING_2", "2.1 Revenue\n"),
    ("NORMAL",   "Total: $1.2M | Target: $1.1M | Status: On track\n\n"),
    ("HEADING_2", "2.2 Users\n"),
    ("NORMAL",   "MAU: 45,000 | DAU: 12,000 | Retention: 82%\n\n"),
]

# Step 3: Convert to Google Docs API requests
STYLE_MAP = {
    "TITLE": "TITLE", "SUBTITLE": "SUBTITLE",
    "HEADING_1": "HEADING_1", "HEADING_2": "HEADING_2", "HEADING_3": "HEADING_3",
}

all_requests = []
idx = 1  # Google Docs content starts at index 1

for style, text in sections:
    # Insert the text
    all_requests.append({
        "insertText": {
            "location": {"index": idx, "tabId": tab_id},
            "text": text
        }
    })
    end_idx = idx + len(text)

    # Apply heading style (skip for NORMAL)
    if style in STYLE_MAP:
        all_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": idx, "endIndex": end_idx, "tabId": tab_id},
                "paragraphStyle": {"namedStyleType": STYLE_MAP[style]},
                "fields": "namedStyleType"
            }
        })

    idx = end_idx

# Step 4: Send in chunks (6-8 requests per batch for Windows safety)
CHUNK_SIZE = 6
for i in range(0, len(all_requests), CHUNK_SIZE):
    chunk = all_requests[i:i+CHUNK_SIZE]
    batch_update(doc_id, chunk)
    time.sleep(0.3)  # Rate limit courtesy

print(f"Done: https://docs.google.com/document/d/{doc_id}/edit")
```

**Key points:**
- Always include `"tabId": "t.0"` in every `location` and `range` — without it, content writes succeed silently but nothing appears
- Use `node run-gws.js` directly, never `shell=True` with JSON containing `|`, `&`, `>`
- Chunk requests (6-8 per batch) to stay under Windows' 32K command line limit
- Track `idx` across chunks — each insert shifts all subsequent indices
- Use `"includeTabsContent": true` when reading back document content
