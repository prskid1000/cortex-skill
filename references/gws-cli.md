# Google Workspace CLI (`gws`) Reference

Complete command reference for the `gws` CLI tool (version **0.16.0**). Covers Drive, Sheets, Docs, Slides, Gmail, Calendar, and Tasks.

---

## CRITICAL RULES (READ FIRST — VIOLATIONS CAUSE ERRORS)

### Rule 1: NO positional arguments. ALL IDs go inside `--params` JSON.

`gws` does NOT accept file IDs, document IDs, or any resource IDs as positional arguments.
There are NO flags like `--title`, `--name`, `--file`, `--toMimeType`, `--id`.
The ONLY way to pass IDs and query parameters is inside the `--params` JSON object.

```
WRONG: gws drive files get <FILE_ID>
WRONG: gws drive files get --file <FILE_ID>
WRONG: gws drive files get --id <FILE_ID>
WRONG: gws drive files get --fileId <FILE_ID>
WRONG: gws drive files create --name "My Doc" --mimeType "application/vnd.google-apps.document"
WRONG: gws drive files create --title "My Doc"
WRONG: gws drive files delete --file <FILE_ID>
WRONG: gws drive files convert --toMimeType "application/pdf"

RIGHT: gws drive files get --params '{"fileId": "<FILE_ID>"}'
RIGHT: gws drive files create --json '{"name": "My Doc", "mimeType": "application/vnd.google-apps.document"}'
RIGHT: gws drive files delete --params '{"fileId": "<FILE_ID>"}'
```

### Rule 2: `--params` vs `--json` — when to use which

| Flag | Purpose | Contains | HTTP mapping |
|------|---------|----------|--------------|
| `--params '{...}'` | URL path + query parameters | IDs (`fileId`, `documentId`, etc.), filters (`q`, `fields`), options (`pageSize`, `valueInputOption`) | Goes into the URL |
| `--json '{...}'` | Request body | Data to create/update: `name`, `mimeType`, `values`, `requests`, `role`, `content`, etc. | Goes into POST/PATCH/PUT body |

**Simple rule**: If it identifies or filters a resource, it goes in `--params`. If it's data you're sending, it goes in `--json`.

### Rule 3: Gmail requires `users` sub-resource

ALL Gmail commands use the path `gws gmail users <resource> <method>` and MUST include `"userId": "me"` in params.

```
WRONG: gws gmail messages list --params '{"q": "is:unread"}'
WRONG: gws gmail labels list
RIGHT: gws gmail users messages list --params '{"userId": "me", "q": "is:unread"}'
RIGHT: gws gmail users labels list --params '{"userId": "me"}'
```

### Rule 4: Sheets values path is `sheets spreadsheets values`

```
WRONG: gws sheets values get ...
RIGHT: gws sheets spreadsheets values get --params '{"spreadsheetId": "...", "range": "..."}'
```

### Rule 5: There is NO `convert` subcommand

To convert a file format, use `files export` (for Google-native files) or upload with the correct MIME type. There is no `gws drive files convert` command.

### Rule 6: Param names follow Google Discovery API exactly

| Service | Param name | NOT this |
|---------|-----------|----------|
| Drive | `fileId` | `file`, `id`, `file_id` |
| Sheets | `spreadsheetId` | `sheetId`, `sheet`, `id` |
| Docs | `documentId` | `docId`, `doc`, `id` |
| Slides | `presentationId` | `slideId`, `presentation`, `id` |
| Calendar | `calendarId`, `eventId` | `calendar`, `event`, `id` |
| Gmail | `userId` (always `"me"`), `id` (for messages/threads/labels/drafts) | `messageId`, `labelId`, `threadId` |
| Tasks | `tasklist`, `task` | `tasklistId`, `taskId`, `id` |
| Drive permissions | `permissionId` | `permission`, `id` |
| Drive comments | `commentId` | `comment`, `id` |
| Drive replies | `replyId` | `reply`, `id` |
| Drive revisions | `revisionId` | `revision`, `id` |
| Calendar settings | `setting` | `settingId`, `id` |

### Rule 7: `drive.comments` and `drive.replies` require `"fields": "*"` in params

```
WRONG: gws drive comments list --params '{"fileId": "<ID>"}'
RIGHT: gws drive comments list --params '{"fileId": "<ID>", "fields": "*"}'
```

### Rule 8: `calendar events update` requires FULL start/end in body

The Google Calendar API PATCH requires `start` and `end` even when only updating other fields like `summary`.

```
WRONG (400 error):
gws calendar events update --params '{"calendarId": "primary", "eventId": "<ID>"}' \
  --json '{"summary": "New Title"}'

RIGHT:
gws calendar events update --params '{"calendarId": "primary", "eventId": "<ID>"}' \
  --json '{"summary": "New Title", "start": {"dateTime": "2026-04-08T10:00:00+05:30"}, "end": {"dateTime": "2026-04-08T10:30:00+05:30"}}'
```

---

## General Syntax

```
gws <service> <resource> [sub-resource] <method> [--params '{...}'] [--json '{...}'] [FLAGS]
```

Use `gws schema <service>.<resource>.<method>` to inspect exact parameter/body shapes.

### Multiline Commands

For long commands, use backslash `\` line continuation (bash) or backtick `` ` `` (PowerShell):

**Bash (recommended):**
```bash
gws calendar events insert \
  --params '{"calendarId": "primary"}' \
  --json '{"summary": "Meeting", "start": {"dateTime": "2026-04-10T09:00:00+05:30"}, "end": {"dateTime": "2026-04-10T09:30:00+05:30"}}'
```

**Single-line equivalent (always works):**
```bash
gws calendar events insert --params '{"calendarId": "primary"}' --json '{"summary": "Meeting", "start": {"dateTime": "2026-04-10T09:00:00+05:30"}, "end": {"dateTime": "2026-04-10T09:30:00+05:30"}}'
```

**When in doubt, use single-line commands** — they work everywhere without escaping issues.

### Windows / Python note

On Windows, `gws` is installed as a `.cmd` shim, so calling it from Python via `subprocess.run(["gws", ...])` will fail with `FileNotFoundError` unless you either:

- pass `shell=True`: `subprocess.run("gws drive files list --format json", shell=True, ...)`, or
- resolve the shim first: `subprocess.run([shutil.which("gws"), "drive", "files", "list"], ...)`.

---

## Global CLI Flags

| Flag | Purpose | Example |
|------|---------|---------|
| `--params '{...}'` | URL/path/query parameters (holds ALL IDs) | `--params '{"fileId": "abc123"}'` |
| `--json '{...}'` | Request body (POST/PATCH/PUT data) | `--json '{"name": "My File"}'` |
| `--format json\|table\|yaml\|csv` | Output format (default: json) | `--format json` |
| `--page-all` | Auto-paginate all results (NDJSON) | `--page-all` |
| `--page-limit <N>` | Max pages with `--page-all` (default 10) | `--page-limit 5` |
| `--page-delay <MS>` | Delay between pages in ms (default 100) | `--page-delay 200` |
| `--upload <PATH>` | Attach local file for upload | `--upload /tmp/report.pdf` |
| `--upload-content-type <MIME>` | MIME type of uploaded file | `--upload-content-type "application/pdf"` |
| `--output <PATH>` | Save binary response to local file | `--output /tmp/doc.pdf` |
| `--api-version <VER>` | Override API version | `--api-version v2` |
| `--dry-run` | Validate locally without sending | `--dry-run` |

---

## Ergonomic `+helper` Commands

High-level helpers (prefixed with `+`) wrap common workflows. They use normal CLI flags (NOT `--params`/`--json`). Prefer these when you don't need raw API control.

| Helper | Description | Example |
|---|---|---|
| `gws drive +upload <file>` | Upload local file (auto MIME) | `gws drive +upload ./report.pdf --parent <FOLDER_ID>` |
| `gws gmail +send` | Send plain-text or HTML email | `gws gmail +send --to alice@example.com --subject 'Hi' --body 'Hello'` |
| `gws gmail +triage` | Unread inbox summary | `gws gmail +triage --max 10 --query 'from:boss'` |
| `gws gmail +reply` | Reply to a message | `gws gmail +reply --message-id <MSG_ID> --body 'Thanks!'` |
| `gws gmail +reply-all` | Reply-all | `gws gmail +reply-all --message-id <MSG_ID> --body 'ack'` |
| `gws gmail +forward` | Forward a message | `gws gmail +forward --message-id <MSG_ID> --to dave@example.com --body 'FYI'` |
| `gws gmail +watch` | Stream new emails (NDJSON) | `gws gmail +watch` |
| `gws sheets +append` | Append row(s) | `gws sheets +append --spreadsheet <SSID> --values 'Alice,100,true'` |
| `gws sheets +read` | Read a range | `gws sheets +read --spreadsheet <SSID> --range 'Sheet1!A1:D10'` |
| `gws docs +write` | Append text to a Doc | `gws docs +write --document <DOC_ID> --text 'New paragraph'` |
| `gws calendar +insert` | Create a simple event | `gws calendar +insert --summary 'Standup' --start 2026-04-10T09:00:00-07:00 --end 2026-04-10T09:30:00-07:00` |
| `gws calendar +agenda` | Upcoming events | `gws calendar +agenda --today` |

Run `gws <service> +<helper> --help` for full option lists.

---

## Auth

```bash
gws auth login                    # OAuth2 browser flow (interactive)
gws auth login --readonly         # Read-only scopes
gws auth login -s drive,gmail     # Restrict scope picker to listed services
gws auth status                   # Current auth state (JSON)
gws auth logout                   # Clear saved creds and token cache
gws auth export                   # Print decrypted credentials to stdout
gws auth setup --project <GCP>    # Configure GCP project + OAuth client
```

---

## Drive

### files

#### list — List files in Drive

**Params** (all optional):
| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Search query (Drive search syntax) |
| `pageSize` | integer | Results per page (1-1000, default 100) |
| `orderBy` | string | Sort: `name`, `modifiedTime`, `createdTime` |
| `fields` | string | Field mask for response |
| `driveId` | string | Shared drive ID |
| `corpora` | string | `user`, `drive`, `allDrives` |

```bash
# List all non-trashed files (max 10)
gws drive files list --params '{"q": "trashed = false", "pageSize": 10}'

# Search by name
gws drive files list --params '{"q": "name contains \"report\" and trashed = false"}'

# List files in a specific folder
gws drive files list --params '{"q": "\"<FOLDER_ID>\" in parents"}'

# List only spreadsheets
gws drive files list --params '{"q": "mimeType=\"application/vnd.google-apps.spreadsheet\"", "pageSize": 10}'

# Paginate through all results
gws drive files list --params '{"q": "trashed = false"}' --page-all
```

#### get — Get file metadata by ID

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `fileId` | string | YES | The file ID |
| `fields` | string | no | Field mask (e.g., `"id,name,mimeType,size,modifiedTime"`) |

```bash
gws drive files get --params '{"fileId": "<FILE_ID>"}'
gws drive files get --params '{"fileId": "<FILE_ID>", "fields": "id,name,mimeType,size,modifiedTime,webViewLink"}'
```

#### create — Create a new file (or upload)

**Params:** none required (metadata goes in `--json`, file content via `--upload`)

**Body (`--json`):**
| Field | Type | Description |
|-------|------|-------------|
| `name` | string | File name |
| `mimeType` | string | MIME type (see table below) |
| `parents` | string[] | Parent folder IDs |

```bash
# Create an empty Google Doc
gws drive files create --json '{"name": "My Document", "mimeType": "application/vnd.google-apps.document"}'

# Create a folder
gws drive files create --json '{"name": "My Folder", "mimeType": "application/vnd.google-apps.folder"}'

# Create a Google Doc inside a specific folder
gws drive files create --json '{"name": "Report", "mimeType": "application/vnd.google-apps.document", "parents": ["<FOLDER_ID>"]}'

# Upload a local file
gws drive files create --json '{"name": "report.xlsx", "parents": ["<FOLDER_ID>"]}' --upload /tmp/report.xlsx --upload-content-type "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Upload a PDF
gws drive files create --json '{"name": "invoice.pdf"}' --upload /tmp/invoice.pdf --upload-content-type "application/pdf"
```

#### update — Update file metadata and/or content

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `fileId` | string | YES | The file ID |
| `addParents` | string | no | Comma-separated parent IDs to add |
| `removeParents` | string | no | Comma-separated parent IDs to remove |

**Body (`--json`):** fields to update (e.g., `name`)

```bash
# Rename a file
gws drive files update --params '{"fileId": "<FILE_ID>"}' --json '{"name": "New Name"}'

# Replace file content
gws drive files update --params '{"fileId": "<FILE_ID>"}' --upload /tmp/updated.xlsx --upload-content-type "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Move a file to a different folder
gws drive files update --params '{"fileId": "<FILE_ID>", "addParents": "<NEW_FOLDER_ID>", "removeParents": "<OLD_FOLDER_ID>"}'
```

#### delete — Permanently delete a file (bypasses trash)

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `fileId` | string | YES | The file ID |

```bash
gws drive files delete --params '{"fileId": "<FILE_ID>"}'
```

#### copy — Copy a file

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `fileId` | string | YES | Source file ID |

**Body (`--json`):** new file metadata (name, parents, etc.)

```bash
gws drive files copy --params '{"fileId": "<FILE_ID>"}' --json '{"name": "Copy of Report", "parents": ["<FOLDER_ID>"]}'
```

#### export — Export Google Workspace document to another format

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `fileId` | string | YES | The file ID (must be a Google-native file) |
| `mimeType` | string | YES | Target export MIME type |

Use `--output` to save the exported file locally.

```bash
# Export Google Doc as PDF
gws drive files export --params '{"fileId": "<FILE_ID>", "mimeType": "application/pdf"}' --output /tmp/doc.pdf

# Export Google Sheet as CSV
gws drive files export --params '{"fileId": "<FILE_ID>", "mimeType": "text/csv"}' --output /tmp/sheet.csv

# Export Google Slides as PDF
gws drive files export --params '{"fileId": "<FILE_ID>", "mimeType": "application/pdf"}' --output /tmp/slides.pdf

# Export Google Doc as DOCX
gws drive files export --params '{"fileId": "<FILE_ID>", "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}' --output /tmp/doc.docx
```

### permissions

#### create — Grant access to a file

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `fileId` | string | YES | The file ID |
| `transferOwnership` | boolean | no | Required when `role` is `owner` |

**Body (`--json`):**
| Field | Type | Description |
|-------|------|-------------|
| `role` | string | `owner`, `organizer`, `fileOrganizer`, `writer`, `commenter`, `reader` |
| `type` | string | `user`, `group`, `domain`, `anyone` |
| `emailAddress` | string | Required for `user` and `group` types |
| `domain` | string | Required for `domain` type |

```bash
# Public link (anyone can view)
gws drive permissions create --params '{"fileId": "<FILE_ID>"}' --json '{"role": "reader", "type": "anyone"}'

# Share with specific user (edit access)
gws drive permissions create --params '{"fileId": "<FILE_ID>"}' --json '{"role": "writer", "type": "user", "emailAddress": "user@example.com"}'

# Share with domain
gws drive permissions create --params '{"fileId": "<FILE_ID>"}' --json '{"role": "reader", "type": "domain", "domain": "example.com"}'
```

#### list — List all permissions on a file

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `fileId` | string | YES |

```bash
gws drive permissions list --params '{"fileId": "<FILE_ID>"}'
```

#### get — Get a specific permission

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `fileId` | string | YES |
| `permissionId` | string | YES |

```bash
gws drive permissions get --params '{"fileId": "<FILE_ID>", "permissionId": "<PERMISSION_ID>"}'
```

#### update — Change a permission's role

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `fileId` | string | YES |
| `permissionId` | string | YES |

```bash
gws drive permissions update --params '{"fileId": "<FILE_ID>", "permissionId": "<PERMISSION_ID>"}' --json '{"role": "writer"}'
```

#### delete — Revoke a permission

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `fileId` | string | YES |
| `permissionId` | string | YES |

```bash
gws drive permissions delete --params '{"fileId": "<FILE_ID>", "permissionId": "<PERMISSION_ID>"}'
```

### comments

> **IMPORTANT**: All comments commands require `"fields": "*"` in params.

#### list

```bash
gws drive comments list --params '{"fileId": "<FILE_ID>", "fields": "*"}'
```

#### get

```bash
gws drive comments get --params '{"fileId": "<FILE_ID>", "commentId": "<COMMENT_ID>", "fields": "*"}'
```

#### create

```bash
gws drive comments create --params '{"fileId": "<FILE_ID>", "fields": "*"}' --json '{"content": "Please review this section."}'
```

#### update

```bash
gws drive comments update --params '{"fileId": "<FILE_ID>", "commentId": "<COMMENT_ID>", "fields": "*"}' --json '{"content": "Updated comment text."}'
```

#### delete

```bash
gws drive comments delete --params '{"fileId": "<FILE_ID>", "commentId": "<COMMENT_ID>"}'
```

### replies

> **IMPORTANT**: All replies commands (except delete) require `"fields": "*"` in params.

#### list

```bash
gws drive replies list --params '{"fileId": "<FILE_ID>", "commentId": "<COMMENT_ID>", "fields": "*"}'
```

#### get

```bash
gws drive replies get --params '{"fileId": "<FILE_ID>", "commentId": "<COMMENT_ID>", "replyId": "<REPLY_ID>", "fields": "*"}'
```

#### create

```bash
gws drive replies create --params '{"fileId": "<FILE_ID>", "commentId": "<COMMENT_ID>", "fields": "*"}' --json '{"content": "Acknowledged."}'
```

#### update

```bash
gws drive replies update --params '{"fileId": "<FILE_ID>", "commentId": "<COMMENT_ID>", "replyId": "<REPLY_ID>", "fields": "*"}' --json '{"content": "Updated reply."}'
```

#### delete

```bash
gws drive replies delete --params '{"fileId": "<FILE_ID>", "commentId": "<COMMENT_ID>", "replyId": "<REPLY_ID>"}'
```

### revisions

#### list

```bash
gws drive revisions list --params '{"fileId": "<FILE_ID>"}'
```

#### get

```bash
gws drive revisions get --params '{"fileId": "<FILE_ID>", "revisionId": "<REVISION_ID>"}'
```

#### update

```bash
gws drive revisions update --params '{"fileId": "<FILE_ID>", "revisionId": "<REVISION_ID>"}' --json '{"keepForever": true}'
```

#### delete

```bash
gws drive revisions delete --params '{"fileId": "<FILE_ID>", "revisionId": "<REVISION_ID>"}'
```

### drives (Shared Drives)

#### list

```bash
gws drive drives list
gws drive drives list --params '{"pageSize": 50}'
```

#### get

```bash
gws drive drives get --params '{"driveId": "<DRIVE_ID>"}'
```

#### create

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `requestId` | string | YES | Unique idempotency key |

```bash
gws drive drives create --params '{"requestId": "unique-id-123"}' --json '{"name": "Engineering Drive"}'
```

#### update

```bash
gws drive drives update --params '{"driveId": "<DRIVE_ID>"}' --json '{"name": "Renamed Drive"}'
```

#### delete

```bash
gws drive drives delete --params '{"driveId": "<DRIVE_ID>"}'
```

---

## Sheets

### spreadsheets

#### create — Create a new spreadsheet

**Body (`--json`):**
| Field | Type | Description |
|-------|------|-------------|
| `properties.title` | string | Spreadsheet title |

```bash
gws sheets spreadsheets create --json '{"properties": {"title": "My Spreadsheet"}}'
```

**Response includes:** `spreadsheetId`, `spreadsheetUrl`, `sheets[].properties.sheetId`

#### get — Get spreadsheet metadata

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `spreadsheetId` | string | YES |
| `fields` | string | no |

```bash
gws sheets spreadsheets get --params '{"spreadsheetId": "<SPREADSHEET_ID>"}'
gws sheets spreadsheets get --params '{"spreadsheetId": "<SPREADSHEET_ID>", "fields": "spreadsheetId,properties.title,sheets.properties"}'
```

#### batchUpdate — Structural changes (add/delete sheets, formatting, charts)

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `spreadsheetId` | string | YES |

**Body:** `{"requests": [...]}`

```bash
# Add a new sheet tab
gws sheets spreadsheets batchUpdate --params '{"spreadsheetId": "<SPREADSHEET_ID>"}' --json '{"requests": [{"addSheet": {"properties": {"title": "New Tab"}}}]}'

# Delete a sheet tab (by sheetId integer, NOT spreadsheetId)
gws sheets spreadsheets batchUpdate --params '{"spreadsheetId": "<SPREADSHEET_ID>"}' --json '{"requests": [{"deleteSheet": {"sheetId": 0}}]}'
```

### spreadsheets values

> **Path**: `gws sheets spreadsheets values <method>` (NOT `gws sheets values`)

#### get — Read cell values

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `spreadsheetId` | string | YES | The spreadsheet ID |
| `range` | string | YES | A1 notation range (e.g., `"Sheet1!A1:D10"`) |
| `valueRenderOption` | string | no | `FORMATTED_VALUE`, `UNFORMATTED_VALUE`, `FORMULA` |

```bash
gws sheets spreadsheets values get --params '{"spreadsheetId": "<SPREADSHEET_ID>", "range": "Sheet1!A1:D10"}'
```

#### update — Write values to a range

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `spreadsheetId` | string | YES | The spreadsheet ID |
| `range` | string | YES | A1 notation starting cell (e.g., `"Sheet1!A1"`) |
| `valueInputOption` | string | YES | `USER_ENTERED` (parses formulas) or `RAW` (literal strings) |

**Body:** `{"values": [[row1col1, row1col2], [row2col1, row2col2]]}`

```bash
gws sheets spreadsheets values update --params '{"spreadsheetId": "<SPREADSHEET_ID>", "range": "Sheet1!A1", "valueInputOption": "USER_ENTERED"}' --json '{"values": [["Name", "Score"], ["Alice", 95], ["Bob", 87]]}'
```

#### append — Append rows after last data

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `spreadsheetId` | string | YES | The spreadsheet ID |
| `range` | string | YES | Column range to append to (e.g., `"Sheet1!A:D"`) |
| `valueInputOption` | string | YES | `USER_ENTERED` or `RAW` |

```bash
gws sheets spreadsheets values append --params '{"spreadsheetId": "<SPREADSHEET_ID>", "range": "Sheet1!A:D", "valueInputOption": "USER_ENTERED"}' --json '{"values": [["Charlie", 92], ["Diana", 88]]}'
```

#### clear — Clear values (keeps formatting)

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `spreadsheetId` | string | YES |
| `range` | string | YES |

```bash
gws sheets spreadsheets values clear --params '{"spreadsheetId": "<SPREADSHEET_ID>", "range": "Sheet1!A1:D10"}'
```

#### batchGet — Read multiple ranges at once

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `spreadsheetId` | string | YES |
| `ranges` | string[] | YES |

```bash
gws sheets spreadsheets values batchGet --params '{"spreadsheetId": "<SPREADSHEET_ID>", "ranges": ["Sheet1!A1:B5", "Sheet2!A1:C3"]}'
```

#### batchUpdate — Write to multiple ranges at once

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `spreadsheetId` | string | YES |

**Body:**
```json
{
  "valueInputOption": "USER_ENTERED",
  "data": [
    {"range": "Sheet1!A1", "values": [["Header1", "Header2"]]},
    {"range": "Sheet2!A1", "values": [["Data1", "Data2"]]}
  ]
}
```

```bash
gws sheets spreadsheets values batchUpdate --params '{"spreadsheetId": "<SPREADSHEET_ID>"}' --json '{"valueInputOption": "USER_ENTERED", "data": [{"range": "Sheet1!A1", "values": [["Header1", "Header2"]]}]}'
```

### spreadsheets sheets

#### copyTo — Copy a sheet to another spreadsheet

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `spreadsheetId` | string | YES | Source spreadsheet ID |
| `sheetId` | integer | YES | Source sheet ID (integer, from `sheets.properties.sheetId`) |

```bash
gws sheets spreadsheets sheets copyTo --params '{"spreadsheetId": "<SPREADSHEET_ID>", "sheetId": 0}' --json '{"destinationSpreadsheetId": "<TARGET_SPREADSHEET_ID>"}'
```

---

## Docs

### documents

#### create — Create a new Google Doc

**Body:** `{"title": "Document Title"}`

```bash
gws docs documents create --json '{"title": "My Document"}'
```

**Response includes:** `documentId`

#### get — Get document content and metadata

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `documentId` | string | YES |

```bash
gws docs documents get --params '{"documentId": "<DOCUMENT_ID>"}'
```

#### batchUpdate — Insert/delete text, apply formatting, insert tables

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `documentId` | string | YES |

**Body:** `{"requests": [...]}`

Common requests:
- `insertText`: `{"location": {"index": 1}, "text": "Hello\n"}`
- `updateTextStyle`: bold, fontSize, foregroundColor, etc.
- `insertTable`: insert a table at an index
- `deleteContentRange`: remove text

```bash
# Insert text at the beginning of the doc
gws docs documents batchUpdate --params '{"documentId": "<DOCUMENT_ID>"}' --json '{"requests": [{"insertText": {"location": {"index": 1}, "text": "Hello, World!\n"}}]}'

# Insert text with bold formatting
gws docs documents batchUpdate --params '{"documentId": "<DOCUMENT_ID>"}' --json '{"requests": [{"insertText": {"location": {"index": 1}, "text": "Bold Title\n"}}, {"updateTextStyle": {"range": {"startIndex": 1, "endIndex": 12}, "textStyle": {"bold": true, "fontSize": {"magnitude": 18, "unit": "PT"}}, "fields": "bold,fontSize"}}]}'
```

---

## Slides

### presentations

#### create — Create a new presentation

**Body:** `{"title": "Presentation Title"}`

```bash
gws slides presentations create --json '{"title": "My Presentation"}'
```

**Response includes:** `presentationId`, `slides[].objectId`

#### get — Get presentation metadata and slides

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `presentationId` | string | YES |

```bash
gws slides presentations get --params '{"presentationId": "<PRESENTATION_ID>"}'
```

#### batchUpdate — Add slides, insert text, images, etc.

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `presentationId` | string | YES |

```bash
# Add a new slide
gws slides presentations batchUpdate --params '{"presentationId": "<PRESENTATION_ID>"}' --json '{"requests": [{"createSlide": {"insertionIndex": 1, "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"}}}]}'
```

### presentations pages

#### get — Get a specific slide/page

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `presentationId` | string | YES |
| `pageObjectId` | string | YES |

```bash
gws slides presentations pages get --params '{"presentationId": "<PRESENTATION_ID>", "pageObjectId": "<PAGE_ID>"}'
```

#### getThumbnail — Get slide thumbnail image

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `presentationId` | string | YES |
| `pageObjectId` | string | YES |
| `thumbnailProperties.mimeType` | string | no (`PNG`) |
| `thumbnailProperties.thumbnailSize` | string | no (`LARGE`) |

```bash
gws slides presentations pages getThumbnail --params '{"presentationId": "<PRESENTATION_ID>", "pageObjectId": "<PAGE_ID>", "thumbnailProperties.mimeType": "PNG", "thumbnailProperties.thumbnailSize": "LARGE"}' --output /tmp/slide-thumb.png
```

---

## Gmail

> **ALL Gmail commands** use `gws gmail users <resource> <method>` and MUST include `"userId": "me"` in params.

### users messages

#### list — List messages matching a query

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `userId` | string | YES | Always `"me"` |
| `q` | string | no | Gmail search query (see operators below) |
| `maxResults` | integer | no | Max results (default 100) |
| `labelIds` | string[] | no | Filter by label IDs |

```bash
gws gmail users messages list --params '{"userId": "me", "q": "is:unread", "maxResults": 20}'
gws gmail users messages list --params '{"userId": "me", "q": "from:boss@example.com newer_than:7d"}' --page-all
```

#### get — Get a specific message

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `userId` | string | YES | Always `"me"` |
| `id` | string | YES | Message ID |
| `format` | string | no | `full`, `metadata`, `minimal`, `raw` |

```bash
gws gmail users messages get --params '{"userId": "me", "id": "<MESSAGE_ID>"}'
gws gmail users messages get --params '{"userId": "me", "id": "<MESSAGE_ID>", "format": "metadata"}'
```

#### send — Send an email (raw RFC 2822)

For most cases, prefer `gws gmail +send` helper instead.

```bash
gws gmail users messages send --params '{"userId": "me"}' --json '{"raw": "<BASE64URL_ENCODED_RFC2822>"}'
```

#### trash / untrash

```bash
gws gmail users messages trash --params '{"userId": "me", "id": "<MESSAGE_ID>"}'
gws gmail users messages untrash --params '{"userId": "me", "id": "<MESSAGE_ID>"}'
```

#### delete — Permanently delete (irreversible)

```bash
gws gmail users messages delete --params '{"userId": "me", "id": "<MESSAGE_ID>"}'
```

#### modify — Add/remove labels

```bash
gws gmail users messages modify --params '{"userId": "me", "id": "<MESSAGE_ID>"}' --json '{"addLabelIds": ["UNREAD"], "removeLabelIds": ["INBOX"]}'
```

#### batchModify — Modify labels on multiple messages

```bash
gws gmail users messages batchModify --params '{"userId": "me"}' --json '{"ids": ["<MSG_ID_1>", "<MSG_ID_2>"], "addLabelIds": ["Label_123"], "removeLabelIds": ["UNREAD"]}'
```

### users drafts

> Drafts use the path parameter `id`, NOT `draftId`.

#### list / get / create / update / send / delete

```bash
gws gmail users drafts list --params '{"userId": "me"}'
gws gmail users drafts get --params '{"userId": "me", "id": "<DRAFT_ID>"}'
gws gmail users drafts create --params '{"userId": "me"}' --json '{"message": {"raw": "<BASE64URL_ENCODED_RFC2822>"}}'
gws gmail users drafts update --params '{"userId": "me", "id": "<DRAFT_ID>"}' --json '{"message": {"raw": "<BASE64URL_ENCODED_RFC2822>"}}'
gws gmail users drafts send --params '{"userId": "me"}' --json '{"id": "<DRAFT_ID>"}'
gws gmail users drafts delete --params '{"userId": "me", "id": "<DRAFT_ID>"}'
```

### users labels

> Labels use the path parameter `id`, NOT `labelId`.

#### list / get

```bash
gws gmail users labels list --params '{"userId": "me"}'
gws gmail users labels get --params '{"userId": "me", "id": "<LABEL_ID>"}'
```

#### create

**Body:**
| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Label name (use `/` for nesting: `"Projects/Active"`) |
| `labelListVisibility` | string | `labelShow`, `labelShowIfUnread`, `labelHide` |
| `messageListVisibility` | string | `show`, `hide` |

```bash
gws gmail users labels create --params '{"userId": "me"}' --json '{"name": "Projects/Active", "labelListVisibility": "labelShow", "messageListVisibility": "show"}'
```

#### update

```bash
gws gmail users labels update --params '{"userId": "me", "id": "<LABEL_ID>"}' --json '{"name": "Projects/Archive"}'
```

#### delete

```bash
gws gmail users labels delete --params '{"userId": "me", "id": "<LABEL_ID>"}'
```

### users threads

> Threads use the path parameter `id`, NOT `threadId`.

```bash
gws gmail users threads list --params '{"userId": "me", "q": "subject:weekly report"}'
gws gmail users threads get --params '{"userId": "me", "id": "<THREAD_ID>"}'
gws gmail users threads modify --params '{"userId": "me", "id": "<THREAD_ID>"}' --json '{"addLabelIds": ["IMPORTANT"]}'
gws gmail users threads trash --params '{"userId": "me", "id": "<THREAD_ID>"}'
gws gmail users threads untrash --params '{"userId": "me", "id": "<THREAD_ID>"}'
gws gmail users threads delete --params '{"userId": "me", "id": "<THREAD_ID>"}'
```

### users history

#### list

```bash
gws gmail users history list --params '{"userId": "me", "startHistoryId": "12345", "historyTypes": ["messageAdded", "labelAdded"]}'
```

### Gmail Search Operators

Use in the `q` parameter for message/thread list commands.

| Operator | Example |
|----------|---------|
| `from:sender@example.com` | From a specific sender |
| `to:recipient@example.com` | To a specific recipient |
| `subject:keyword` | Keyword in subject |
| `has:attachment` | Has attachments |
| `is:unread` / `is:read` | Read state |
| `is:starred` | Starred |
| `newer_than:7d` | Newer than 7 days (`d`/`m`/`y`) |
| `older_than:30d` | Older than 30 days |
| `after:2025/01/01` | After date (YYYY/MM/DD) |
| `before:2025/12/31` | Before date |
| `label:projects` | Has label |
| `filename:pdf` | Attachment filename |
| `larger:5M` / `smaller:1M` | Size filter |
| `"exact phrase"` | Exact phrase match |
| `in:inbox` / `in:sent` / `in:trash` | Location |
| `category:primary` | Gmail category |

Combine with spaces (AND) or `OR`:
```
from:alice@example.com subject:invoice newer_than:30d
from:alice@example.com OR from:bob@example.com has:attachment
```

---

## Calendar

### events

#### list — List events on a calendar

**Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `calendarId` | string | YES | Calendar ID (use `"primary"` for default) |
| `timeMin` | string | no | ISO 8601 datetime lower bound |
| `timeMax` | string | no | ISO 8601 datetime upper bound |
| `maxResults` | integer | no | Max events to return |
| `singleEvents` | boolean | no | Expand recurring events (required for `orderBy: startTime`) |
| `orderBy` | string | no | `startTime` (requires `singleEvents: true`) or `updated` |
| `q` | string | no | Free-text search |

```bash
gws calendar events list --params '{"calendarId": "primary", "timeMin": "2026-04-01T00:00:00Z", "maxResults": 10, "singleEvents": true, "orderBy": "startTime"}'
```

#### get — Get a specific event

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `calendarId` | string | YES |
| `eventId` | string | YES |

```bash
gws calendar events get --params '{"calendarId": "primary", "eventId": "<EVENT_ID>"}'
```

#### insert — Create a new event

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `calendarId` | string | YES |

**Body (`--json`):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `summary` | string | YES | Event title |
| `start` | object | YES | `{"dateTime": "ISO8601", "timeZone": "TZ"}` |
| `end` | object | YES | `{"dateTime": "ISO8601", "timeZone": "TZ"}` |
| `location` | string | no | Event location |
| `description` | string | no | Event description |
| `attendees` | object[] | no | `[{"email": "user@example.com"}]` |
| `reminders` | object | no | Override default reminders |

```bash
gws calendar events insert --params '{"calendarId": "primary"}' --json '{"summary": "Team Standup", "location": "Room A", "start": {"dateTime": "2026-04-10T09:00:00+05:30", "timeZone": "Asia/Kolkata"}, "end": {"dateTime": "2026-04-10T09:30:00+05:30", "timeZone": "Asia/Kolkata"}}'
```

#### update — Update an existing event

> **IMPORTANT**: Google Calendar API PATCH requires `start` and `end` even if you only change `summary`.

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `calendarId` | string | YES |
| `eventId` | string | YES |

```bash
gws calendar events update --params '{"calendarId": "primary", "eventId": "<EVENT_ID>"}' --json '{"summary": "Updated Title", "start": {"dateTime": "2026-04-10T09:00:00+05:30"}, "end": {"dateTime": "2026-04-10T09:30:00+05:30"}}'
```

#### delete

```bash
gws calendar events delete --params '{"calendarId": "primary", "eventId": "<EVENT_ID>"}'
```

#### quickAdd — Create event from natural language

**Params:**
| Param | Type | Required |
|-------|------|----------|
| `calendarId` | string | YES |
| `text` | string | YES |

```bash
gws calendar events quickAdd --params '{"calendarId": "primary", "text": "Lunch with Alice at noon tomorrow at Cafe Mocha"}'
```

#### instances — List instances of a recurring event

```bash
gws calendar events instances --params '{"calendarId": "primary", "eventId": "<EVENT_ID>", "timeMin": "2026-04-01T00:00:00Z", "timeMax": "2026-06-30T23:59:59Z"}'
```

#### move — Move event to different calendar

```bash
gws calendar events move --params '{"calendarId": "primary", "eventId": "<EVENT_ID>", "destination": "<TARGET_CALENDAR_ID>"}'
```

#### watch — Push notifications for event changes

```bash
gws calendar events watch --params '{"calendarId": "primary"}' --json '{"id": "unique-channel-id", "type": "web_hook", "address": "https://example.com/webhook"}'
```

### calendarList

```bash
gws calendar calendarList list
gws calendar calendarList get --params '{"calendarId": "primary"}'
gws calendar calendarList insert --json '{"id": "shared-calendar@group.calendar.google.com"}'
gws calendar calendarList update --params '{"calendarId": "<CALENDAR_ID>"}' --json '{"colorId": "9", "selected": true}'
gws calendar calendarList delete --params '{"calendarId": "<CALENDAR_ID>"}'
```

### settings

```bash
gws calendar settings list
gws calendar settings get --params '{"setting": "timezone"}'
```

> Note: `settings get` uses param name `setting`, NOT `settingId`.

### freebusy

#### query — Check free/busy across calendars

```bash
gws calendar freebusy query --json '{"timeMin": "2026-04-10T00:00:00Z", "timeMax": "2026-04-10T23:59:59Z", "items": [{"id": "primary"}, {"id": "alice@example.com"}]}'
```

---

## Tasks

> **Requires scope**: `gws auth login -s tasks`
>
> Tasks uses param names `tasklist` and `task` (NOT `tasklistId` / `taskId`).

### tasklists

```bash
gws tasks tasklists list
gws tasks tasklists get --params '{"tasklist": "<TASKLIST_ID>"}'
gws tasks tasklists insert --json '{"title": "Work Tasks"}'
gws tasks tasklists update --params '{"tasklist": "<TASKLIST_ID>"}' --json '{"title": "Renamed Task List"}'
gws tasks tasklists delete --params '{"tasklist": "<TASKLIST_ID>"}'
```

### tasks

```bash
gws tasks tasks list --params '{"tasklist": "<TASKLIST_ID>"}'
gws tasks tasks list --params '{"tasklist": "<TASKLIST_ID>", "showCompleted": false}'
gws tasks tasks get --params '{"tasklist": "<TASKLIST_ID>", "task": "<TASK_ID>"}'
gws tasks tasks insert --params '{"tasklist": "<TASKLIST_ID>"}' --json '{"title": "Review PR #42", "notes": "Check edge cases", "due": "2026-04-15T00:00:00Z"}'
gws tasks tasks update --params '{"tasklist": "<TASKLIST_ID>", "task": "<TASK_ID>"}' --json '{"title": "Updated task", "status": "completed"}'
gws tasks tasks delete --params '{"tasklist": "<TASKLIST_ID>", "task": "<TASK_ID>"}'
gws tasks tasks move --params '{"tasklist": "<TASKLIST_ID>", "task": "<TASK_ID>", "parent": "<PARENT_TASK_ID>"}'
gws tasks tasks clear --params '{"tasklist": "<TASKLIST_ID>"}'
```

---

## Common MIME Types

### Google Native Formats (for `files create` with `--json`)

| Format | MIME Type |
|--------|-----------|
| Google Doc | `application/vnd.google-apps.document` |
| Google Sheet | `application/vnd.google-apps.spreadsheet` |
| Google Slides | `application/vnd.google-apps.presentation` |
| Google Drawing | `application/vnd.google-apps.drawing` |
| Google Form | `application/vnd.google-apps.form` |
| Folder | `application/vnd.google-apps.folder` |

### Export MIME Types (for `files export` `mimeType` param)

| Target | MIME Type |
|--------|-----------|
| PDF | `application/pdf` |
| Plain text | `text/plain` |
| HTML | `text/html` |
| CSV | `text/csv` |
| DOCX | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| XLSX | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| PPTX | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| EPUB | `application/epub+zip` |

### Upload MIME Types (for `--upload-content-type`)

| File Type | MIME Type |
|-----------|-----------|
| PDF | `application/pdf` |
| DOCX | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| XLSX | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| PPTX | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| CSV | `text/csv` |
| PNG | `image/png` |
| JPEG | `image/jpeg` |
| JSON | `application/json` |
| ZIP | `application/zip` |

---

## Sharing Patterns

### Make file publicly viewable

```bash
# Step 1: Grant anyone-reader permission
gws drive permissions create --params '{"fileId": "<FILE_ID>"}' --json '{"role": "reader", "type": "anyone"}'

# Step 2: Get the shareable link
gws drive files get --params '{"fileId": "<FILE_ID>", "fields": "webViewLink"}'
```

### Share with specific user

```bash
# Read-only
gws drive permissions create --params '{"fileId": "<FILE_ID>"}' --json '{"role": "reader", "type": "user", "emailAddress": "user@example.com"}'

# Edit access
gws drive permissions create --params '{"fileId": "<FILE_ID>"}' --json '{"role": "writer", "type": "user", "emailAddress": "user@example.com"}'

# Comment-only
gws drive permissions create --params '{"fileId": "<FILE_ID>"}' --json '{"role": "commenter", "type": "user", "emailAddress": "user@example.com"}'
```

### Transfer ownership

```bash
gws drive permissions create --params '{"fileId": "<FILE_ID>", "transferOwnership": true}' --json '{"role": "owner", "type": "user", "emailAddress": "newowner@example.com"}'
```

---

## Quick Decision Tree

**"I want to create a Google Doc/Sheet/Slides"**
-> Use `gws <service> <resource> create --json '{"title/properties.title": "..."}'`

**"I want to upload a local file to Drive"**
-> Use `gws drive +upload ./file.pdf` (simple) or `gws drive files create --json '{"name": "..."}' --upload /path --upload-content-type "..."` (full control)

**"I want to write text into a Google Doc"**
-> Use `gws docs +write --document <DOC_ID> --text 'content'` (simple) or `gws docs documents batchUpdate` with `insertText` request (full control)

**"I want to read/write spreadsheet cells"**
-> Use `gws sheets +read`/`+append` (simple) or `gws sheets spreadsheets values get/update/append` (full control)

**"I want to send an email"**
-> Use `gws gmail +send --to ... --subject ... --body ...`

**"I want to create a calendar event"**
-> Use `gws calendar +insert --summary ... --start ... --end ...` (simple) or `gws calendar events insert` (full control)

**"I want to download/export a Google file"**
-> Use `gws drive files export --params '{"fileId": "...", "mimeType": "..."}' --output /tmp/file.ext`
