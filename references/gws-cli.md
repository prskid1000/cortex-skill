# Google Workspace CLI (`gws`) Reference

Complete command reference for the `gws` CLI tool. Covers Drive, Sheets, Docs, Slides, Gmail, Calendar, and Tasks.

---

## General Syntax

```
gws <service> <resource> <method> [FLAGS]
```

---

## Global CLI Flags

| Flag | Purpose |
|------|---------|
| `--format table\|csv\|yaml\|json` | Set output format (default: table) |
| `--page-all` | Auto-paginate through all results (streams NDJSON) |
| `--upload <PATH>` | Attach a local file for upload |
| `--upload-content-type <MIME>` | MIME type of the uploaded file |
| `--output <PATH>` | Save binary response body to a local file |
| `--params '{...}'` | URL/query parameters as a JSON object |
| `--json '{...}'` | Request body as a JSON object |
| `--fields <FIELD_MASK>` | Partial response field mask (comma-separated) |

---

## Drive

### files

#### list
List files in Drive. Use `--params` to pass `q` (search query), `orderBy`, `pageSize`, `driveId`, `corpora`, etc.

```
gws drive files list --params '{"q": "mimeType=\"application/vnd.google-apps.spreadsheet\"", "pageSize": 10}'
gws drive files list --params '{"q": "name contains \"report\" and trashed = false"}' --page-all
gws drive files list --params '{"q": "\"<FOLDER_ID>\" in parents"}' --format json
```

#### get
Retrieve file metadata by ID.

```
gws drive files get <FILE_ID>
gws drive files get <FILE_ID> --fields "id,name,mimeType,size,modifiedTime"
```

#### create
Create a new file. Provide metadata via `--json` and optionally upload content via `--upload`.

```
# Create an empty Google Doc
gws drive files create --json '{"name": "My Document", "mimeType": "application/vnd.google-apps.document"}'

# Create a folder
gws drive files create --json '{"name": "My Folder", "mimeType": "application/vnd.google-apps.folder"}'

# Upload a local file
gws drive files create --json '{"name": "report.xlsx", "parents": ["<FOLDER_ID>"]}' \
  --upload /tmp/report.xlsx \
  --upload-content-type "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Upload a PDF
gws drive files create --json '{"name": "invoice.pdf"}' \
  --upload /tmp/invoice.pdf \
  --upload-content-type "application/pdf"
```

#### update
Update file metadata and/or content. Supply the file ID as the resource identifier.

```
# Rename a file
gws drive files update <FILE_ID> --json '{"name": "New Name"}'

# Replace file content
gws drive files update <FILE_ID> \
  --upload /tmp/updated.xlsx \
  --upload-content-type "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Move a file to a different folder
gws drive files update <FILE_ID> --params '{"addParents": "<NEW_FOLDER_ID>", "removeParents": "<OLD_FOLDER_ID>"}'
```

#### delete
Permanently delete a file (bypasses trash).

```
gws drive files delete <FILE_ID>
```

#### copy
Copy a file. Provide new metadata in `--json`.

```
gws drive files copy <FILE_ID> --json '{"name": "Copy of Report", "parents": ["<FOLDER_ID>"]}'
```

#### export
Export a Google Workspace document to a different format. Specify `mimeType` in `--params` and save with `--output`.

```
# Export Google Doc as PDF
gws drive files export <FILE_ID> --params '{"mimeType": "application/pdf"}' --output /tmp/doc.pdf

# Export Google Sheet as CSV
gws drive files export <FILE_ID> --params '{"mimeType": "text/csv"}' --output /tmp/sheet.csv

# Export Google Slides as PDF
gws drive files export <FILE_ID> --params '{"mimeType": "application/pdf"}' --output /tmp/slides.pdf

# Export Google Doc as DOCX
gws drive files export <FILE_ID> --params '{"mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}' --output /tmp/doc.docx
```

### permissions

#### create
Grant access to a file or folder.

```
gws drive permissions create <FILE_ID> --json '{"role": "reader", "type": "anyone"}'
gws drive permissions create <FILE_ID> --json '{"role": "writer", "type": "user", "emailAddress": "user@example.com"}'
gws drive permissions create <FILE_ID> --json '{"role": "reader", "type": "domain", "domain": "example.com"}'
```

Roles: `owner`, `organizer`, `fileOrganizer`, `writer`, `commenter`, `reader`
Types: `user`, `group`, `domain`, `anyone`

#### list
List all permissions on a file.

```
gws drive permissions list <FILE_ID>
```

#### get
Get a specific permission by ID.

```
gws drive permissions get <FILE_ID> --params '{"permissionId": "<PERMISSION_ID>"}'
```

#### update
Update an existing permission (e.g., change role).

```
gws drive permissions update <FILE_ID> <PERMISSION_ID> --json '{"role": "writer"}'
```

#### delete
Revoke a permission.

```
gws drive permissions delete <FILE_ID> <PERMISSION_ID>
```

### comments

#### list
```
gws drive comments list <FILE_ID>
```

#### get
```
gws drive comments get <FILE_ID> <COMMENT_ID>
```

#### create
```
gws drive comments create <FILE_ID> --json '{"content": "Please review this section."}'
```

#### update
```
gws drive comments update <FILE_ID> <COMMENT_ID> --json '{"content": "Updated comment text."}'
```

#### delete
```
gws drive comments delete <FILE_ID> <COMMENT_ID>
```

### replies

#### list
```
gws drive replies list <FILE_ID> <COMMENT_ID>
```

#### get
```
gws drive replies get <FILE_ID> <COMMENT_ID> <REPLY_ID>
```

#### create
```
gws drive replies create <FILE_ID> <COMMENT_ID> --json '{"content": "Acknowledged."}'
```

#### update
```
gws drive replies update <FILE_ID> <COMMENT_ID> <REPLY_ID> --json '{"content": "Updated reply."}'
```

#### delete
```
gws drive replies delete <FILE_ID> <COMMENT_ID> <REPLY_ID>
```

### revisions

#### list
```
gws drive revisions list <FILE_ID>
```

#### get
```
gws drive revisions get <FILE_ID> <REVISION_ID>
```

#### update
```
gws drive revisions update <FILE_ID> <REVISION_ID> --json '{"keepForever": true}'
```

#### delete
```
gws drive revisions delete <FILE_ID> <REVISION_ID>
```

### drives (Shared Drives)

#### list
```
gws drive drives list
gws drive drives list --params '{"pageSize": 50}'
```

#### get
```
gws drive drives get <DRIVE_ID>
```

#### create
Provide a unique `requestId` in `--params`.

```
gws drive drives create --params '{"requestId": "unique-id-123"}' --json '{"name": "Engineering Drive"}'
```

#### update
```
gws drive drives update <DRIVE_ID> --json '{"name": "Renamed Drive"}'
```

#### delete
```
gws drive drives delete <DRIVE_ID>
```

---

## Sheets

### spreadsheets

#### create
Create a new spreadsheet.

```
gws sheets spreadsheets create --json '{"properties": {"title": "My Spreadsheet"}}'
```

#### get
Get spreadsheet metadata (sheets, named ranges, etc.).

```
gws sheets spreadsheets get <SPREADSHEET_ID>
gws sheets spreadsheets get <SPREADSHEET_ID> --fields "spreadsheetId,properties.title,sheets.properties"
```

#### batchUpdate
Apply one or more structural changes (add/delete sheets, merge cells, formatting, charts, pivot tables, etc.).

```
gws sheets spreadsheets batchUpdate <SPREADSHEET_ID> --json '{
  "requests": [
    {"addSheet": {"properties": {"title": "New Tab"}}},
    {"deleteSheet": {"sheetId": 0}}
  ]
}'
```

### values

#### get
Read a range of cell values.

```
gws sheets values get <SPREADSHEET_ID> --params '{"range": "Sheet1!A1:D10"}'
gws sheets values get <SPREADSHEET_ID> --params '{"range": "Sheet1!A1:D10", "valueRenderOption": "FORMATTED_VALUE"}'
```

#### update
Write values to a range. Set `valueInputOption` to `USER_ENTERED` (applies formulas/formatting) or `RAW` (stores literal strings).

```
gws sheets values update <SPREADSHEET_ID> --params '{"range": "Sheet1!A1", "valueInputOption": "USER_ENTERED"}' \
  --json '{"values": [["Name", "Score"], ["Alice", 95], ["Bob", 87]]}'
```

#### append
Append rows after the last row with data in the given range.

```
gws sheets values append <SPREADSHEET_ID> --params '{"range": "Sheet1!A:D", "valueInputOption": "USER_ENTERED"}' \
  --json '{"values": [["Charlie", 92], ["Diana", 88]]}'
```

#### clear
Clear values from a range (preserves formatting).

```
gws sheets values clear <SPREADSHEET_ID> --params '{"range": "Sheet1!A1:D10"}'
```

#### batchGet
Read multiple ranges in one call.

```
gws sheets values batchGet <SPREADSHEET_ID> --params '{"ranges": ["Sheet1!A1:B5", "Sheet2!A1:C3"]}'
```

#### batchUpdate
Write to multiple ranges in one call.

```
gws sheets values batchUpdate <SPREADSHEET_ID> --json '{
  "valueInputOption": "USER_ENTERED",
  "data": [
    {"range": "Sheet1!A1", "values": [["Header1", "Header2"]]},
    {"range": "Sheet2!A1", "values": [["Data1", "Data2"]]}
  ]
}'
```

### sheets

#### copyTo
Copy a sheet to another spreadsheet.

```
gws sheets sheets copyTo <SPREADSHEET_ID> <SHEET_ID> --json '{"destinationSpreadsheetId": "<TARGET_SPREADSHEET_ID>"}'
```

---

## Docs

### documents

#### create
Create a new Google Doc.

```
gws docs documents create --json '{"title": "My Document"}'
```

#### get
Retrieve document content and metadata.

```
gws docs documents get <DOCUMENT_ID>
```

#### batchUpdate
Apply structural edits: insert/delete text, apply formatting, insert tables, images, page breaks, etc.

```
gws docs documents batchUpdate <DOCUMENT_ID> --json '{
  "requests": [
    {"insertText": {"location": {"index": 1}, "text": "Hello, World!\n"}},
    {"updateTextStyle": {
      "range": {"startIndex": 1, "endIndex": 14},
      "textStyle": {"bold": true, "fontSize": {"magnitude": 18, "unit": "PT"}},
      "fields": "bold,fontSize"
    }}
  ]
}'
```

---

## Slides

### presentations

#### create
Create a new presentation.

```
gws slides presentations create --json '{"title": "My Presentation"}'
```

#### get
Retrieve presentation metadata and slide content.

```
gws slides presentations get <PRESENTATION_ID>
```

#### batchUpdate
Apply changes: create slides, insert text, add images, update layouts, etc.

```
gws slides presentations batchUpdate <PRESENTATION_ID> --json '{
  "requests": [
    {"createSlide": {"insertionIndex": 1, "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"}}}
  ]
}'
```

### pages

#### get
Get a specific page (slide, layout, or master).

```
gws slides presentations pages get <PRESENTATION_ID> <PAGE_ID>
```

#### getThumbnail
Get a thumbnail image of a page. Save with `--output`.

```
gws slides presentations pages getThumbnail <PRESENTATION_ID> <PAGE_ID> \
  --params '{"thumbnailProperties.mimeType": "PNG", "thumbnailProperties.thumbnailSize": "LARGE"}' \
  --output /tmp/slide-thumb.png
```

---

## Gmail

### messages

#### list
List messages matching a query.

```
gws gmail messages list --params '{"q": "is:unread", "maxResults": 20}'
gws gmail messages list --params '{"q": "from:boss@example.com newer_than:7d"}' --page-all
```

#### get
Get a specific message. Use `format` param: `full`, `metadata`, `minimal`, `raw`.

```
gws gmail messages get <MESSAGE_ID>
gws gmail messages get <MESSAGE_ID> --params '{"format": "full"}'
gws gmail messages get <MESSAGE_ID> --params '{"format": "raw"}' --output /tmp/email.eml
```

#### send
Send an email. Provide the RFC 2822 message as a base64url-encoded `raw` field, or use the simplified JSON body.

```
gws gmail messages send --json '{"raw": "<BASE64URL_ENCODED_RFC2822>"}'
```

#### trash
Move a message to trash.

```
gws gmail messages trash <MESSAGE_ID>
```

#### untrash
Remove a message from trash.

```
gws gmail messages untrash <MESSAGE_ID>
```

#### delete
Permanently delete a message (irreversible).

```
gws gmail messages delete <MESSAGE_ID>
```

#### modify
Add or remove labels on a message.

```
gws gmail messages modify <MESSAGE_ID> --json '{"addLabelIds": ["UNREAD"], "removeLabelIds": ["INBOX"]}'
```

#### batchModify
Modify labels on multiple messages at once.

```
gws gmail messages batchModify --json '{
  "ids": ["<MSG_ID_1>", "<MSG_ID_2>"],
  "addLabelIds": ["Label_123"],
  "removeLabelIds": ["UNREAD"]
}'
```

### drafts

#### list
```
gws gmail drafts list
```

#### get
```
gws gmail drafts get <DRAFT_ID>
```

#### create
```
gws gmail drafts create --json '{"message": {"raw": "<BASE64URL_ENCODED_RFC2822>"}}'
```

#### update
```
gws gmail drafts update <DRAFT_ID> --json '{"message": {"raw": "<BASE64URL_ENCODED_RFC2822>"}}'
```

#### send
```
gws gmail drafts send --json '{"id": "<DRAFT_ID>"}'
```

#### delete
```
gws gmail drafts delete <DRAFT_ID>
```

### labels

#### list
```
gws gmail labels list
```

#### get
```
gws gmail labels get <LABEL_ID>
```

#### create
```
gws gmail labels create --json '{"name": "Projects/Active", "labelListVisibility": "labelShow", "messageListVisibility": "show"}'
```

#### update
```
gws gmail labels update <LABEL_ID> --json '{"name": "Projects/Archive"}'
```

#### delete
```
gws gmail labels delete <LABEL_ID>
```

### threads

#### list
```
gws gmail threads list --params '{"q": "subject:weekly report"}'
```

#### get
```
gws gmail threads get <THREAD_ID>
```

#### modify
```
gws gmail threads modify <THREAD_ID> --json '{"addLabelIds": ["IMPORTANT"]}'
```

#### trash
```
gws gmail threads trash <THREAD_ID>
```

#### untrash
```
gws gmail threads untrash <THREAD_ID>
```

#### delete
```
gws gmail threads delete <THREAD_ID>
```

### history

#### list
List history of changes since a given `startHistoryId`.

```
gws gmail history list --params '{"startHistoryId": "12345", "historyTypes": ["messageAdded", "labelAdded"]}'
```

### Gmail Search Operators

Use these in the `q` parameter for `messages list` and `threads list`.

| Operator | Description |
|----------|-------------|
| `from:sender@example.com` | Messages from a specific sender |
| `to:recipient@example.com` | Messages to a specific recipient |
| `subject:keyword` | Messages with keyword in subject |
| `has:attachment` | Messages with attachments |
| `is:unread` | Unread messages |
| `is:read` | Read messages |
| `is:starred` | Starred messages |
| `newer_than:7d` | Messages newer than 7 days (`d`, `m`, `y`) |
| `older_than:30d` | Messages older than 30 days |
| `after:2025/01/01` | Messages after a date (YYYY/MM/DD) |
| `before:2025/12/31` | Messages before a date |
| `label:projects` | Messages with a specific label |
| `filename:pdf` | Messages with attachment filename matching |
| `larger:5M` | Messages larger than 5 MB |
| `smaller:1M` | Messages smaller than 1 MB |
| `"exact phrase"` | Messages containing an exact phrase |
| `in:inbox` | Messages in inbox |
| `in:sent` | Messages in sent mail |
| `in:trash` | Messages in trash |
| `in:anywhere` | Messages in all folders including spam/trash |
| `category:primary` | Messages in Primary category |
| `category:social` | Messages in Social category |
| `category:promotions` | Messages in Promotions category |
| `category:updates` | Messages in Updates category |
| `category:forums` | Messages in Forums category |

Combine operators with spaces (implicit AND) or `OR`:
```
from:alice@example.com subject:invoice newer_than:30d
from:alice@example.com OR from:bob@example.com has:attachment
```

---

## Calendar

### events

#### list
List events on a calendar. Default calendar: `primary`.

```
gws calendar events list <CALENDAR_ID> --params '{"timeMin": "2025-01-01T00:00:00Z", "timeMax": "2025-12-31T23:59:59Z", "singleEvents": true, "orderBy": "startTime"}'
gws calendar events list primary --params '{"timeMin": "2025-04-01T00:00:00Z", "maxResults": 10, "singleEvents": true}'
```

#### get
```
gws calendar events get <CALENDAR_ID> <EVENT_ID>
```

#### insert
Create a new event.

```
gws calendar events insert <CALENDAR_ID> --json '{
  "summary": "Team Standup",
  "location": "Conference Room A",
  "description": "Daily sync meeting",
  "start": {"dateTime": "2025-04-10T09:00:00+05:30", "timeZone": "Asia/Kolkata"},
  "end": {"dateTime": "2025-04-10T09:30:00+05:30", "timeZone": "Asia/Kolkata"},
  "attendees": [
    {"email": "alice@example.com"},
    {"email": "bob@example.com"}
  ],
  "reminders": {"useDefault": false, "overrides": [{"method": "popup", "minutes": 10}]}
}'
```

#### update
Update an existing event.

```
gws calendar events update <CALENDAR_ID> <EVENT_ID> --json '{"summary": "Updated Meeting Title"}'
```

#### delete
```
gws calendar events delete <CALENDAR_ID> <EVENT_ID>
```

#### quickAdd
Create an event from a natural-language string.

```
gws calendar events quickAdd <CALENDAR_ID> --params '{"text": "Lunch with Alice at noon tomorrow at Cafe Mocha"}'
```

#### instances
List instances of a recurring event.

```
gws calendar events instances <CALENDAR_ID> <EVENT_ID> --params '{"timeMin": "2025-04-01T00:00:00Z", "timeMax": "2025-06-30T23:59:59Z"}'
```

#### move
Move an event to a different calendar.

```
gws calendar events move <CALENDAR_ID> <EVENT_ID> --params '{"destination": "<TARGET_CALENDAR_ID>"}'
```

#### watch
Set up push notifications for event changes.

```
gws calendar events watch <CALENDAR_ID> --json '{"id": "unique-channel-id", "type": "web_hook", "address": "https://example.com/webhook"}'
```

### calendarList

#### list
List all calendars on the user's calendar list.

```
gws calendar calendarList list
```

#### get
```
gws calendar calendarList get <CALENDAR_ID>
```

#### insert
Add an existing calendar to the user's list.

```
gws calendar calendarList insert --json '{"id": "shared-calendar@group.calendar.google.com"}'
```

#### update
```
gws calendar calendarList update <CALENDAR_ID> --json '{"colorId": "9", "selected": true}'
```

#### delete
Remove a calendar from the user's list.

```
gws calendar calendarList delete <CALENDAR_ID>
```

### settings

#### list
```
gws calendar settings list
```

#### get
```
gws calendar settings get <SETTING_ID>
```

### freebusy

#### query
Query free/busy information for one or more calendars.

```
gws calendar freebusy query --json '{
  "timeMin": "2025-04-10T00:00:00Z",
  "timeMax": "2025-04-10T23:59:59Z",
  "items": [{"id": "primary"}, {"id": "alice@example.com"}]
}'
```

---

## Tasks

### tasklists

#### list
```
gws tasks tasklists list
```

#### get
```
gws tasks tasklists get <TASKLIST_ID>
```

#### insert
```
gws tasks tasklists insert --json '{"title": "Work Tasks"}'
```

#### update
```
gws tasks tasklists update <TASKLIST_ID> --json '{"title": "Renamed Task List"}'
```

#### delete
```
gws tasks tasklists delete <TASKLIST_ID>
```

### tasks

#### list
```
gws tasks tasks list <TASKLIST_ID>
gws tasks tasks list <TASKLIST_ID> --params '{"showCompleted": false, "showHidden": false}'
```

#### get
```
gws tasks tasks get <TASKLIST_ID> <TASK_ID>
```

#### insert
```
gws tasks tasks insert <TASKLIST_ID> --json '{"title": "Review PR #42", "notes": "Check edge cases", "due": "2025-04-15T00:00:00Z"}'
```

#### update
```
gws tasks tasks update <TASKLIST_ID> <TASK_ID> --json '{"title": "Updated task title", "status": "completed"}'
```

#### delete
```
gws tasks tasks delete <TASKLIST_ID> <TASK_ID>
```

#### move
Reorder a task or move it under a parent task.

```
gws tasks tasks move <TASKLIST_ID> <TASK_ID> --params '{"parent": "<PARENT_TASK_ID>", "previous": "<PREVIOUS_TASK_ID>"}'
```

#### clear
Remove all completed tasks from a task list.

```
gws tasks tasks clear <TASKLIST_ID>
```

---

## Common MIME Types

### Google Native Formats

| Format | MIME Type |
|--------|-----------|
| Google Doc | `application/vnd.google-apps.document` |
| Google Sheet | `application/vnd.google-apps.spreadsheet` |
| Google Slides | `application/vnd.google-apps.presentation` |
| Google Drawing | `application/vnd.google-apps.drawing` |
| Google Form | `application/vnd.google-apps.form` |
| Google Script | `application/vnd.google-apps.script` |
| Google Site | `application/vnd.google-apps.site` |
| Google Shortcut | `application/vnd.google-apps.shortcut` |
| Folder | `application/vnd.google-apps.folder` |

### Export MIME Types (for `files export`)

| Target Format | MIME Type |
|---------------|-----------|
| PDF | `application/pdf` |
| Plain text | `text/plain` |
| Rich text (RTF) | `application/rtf` |
| HTML | `text/html` |
| CSV | `text/csv` |
| TSV | `text/tab-separated-values` |
| DOCX | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| XLSX | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| PPTX | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| EPUB | `application/epub+zip` |
| Open Document Text | `application/vnd.oasis.opendocument.text` |
| Open Document Sheet | `application/vnd.oasis.opendocument.spreadsheet` |
| Open Document Presentation | `application/vnd.oasis.opendocument.presentation` |
| PNG (Drawings) | `image/png` |
| JPEG (Drawings) | `image/jpeg` |
| SVG (Drawings) | `image/svg+xml` |

### Upload MIME Types (for `files create` / `files update`)

| File Type | MIME Type |
|-----------|-----------|
| PDF | `application/pdf` |
| DOCX | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| XLSX | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| PPTX | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| CSV | `text/csv` |
| Plain text | `text/plain` |
| HTML | `text/html` |
| JSON | `application/json` |
| PNG | `image/png` |
| JPEG | `image/jpeg` |
| GIF | `image/gif` |
| SVG | `image/svg+xml` |
| MP4 | `video/mp4` |
| MP3 | `audio/mpeg` |
| WAV | `audio/wav` |
| ZIP | `application/zip` |

---

## Sharing Patterns

### Share with anyone (public link)

```
gws drive permissions create <FILE_ID> --json '{"role": "reader", "type": "anyone"}'
```

Retrieve the shareable link after granting permission:
```
gws drive files get <FILE_ID> --fields "webViewLink"
```

### Share with a specific user

```
# Read-only
gws drive permissions create <FILE_ID> --json '{"role": "reader", "type": "user", "emailAddress": "user@example.com"}'

# Edit access
gws drive permissions create <FILE_ID> --json '{"role": "writer", "type": "user", "emailAddress": "user@example.com"}'

# Comment-only
gws drive permissions create <FILE_ID> --json '{"role": "commenter", "type": "user", "emailAddress": "user@example.com"}'
```

### Share with a domain

```
gws drive permissions create <FILE_ID> --json '{"role": "reader", "type": "domain", "domain": "example.com"}'
```

### Share with a Google Group

```
gws drive permissions create <FILE_ID> --json '{"role": "writer", "type": "group", "emailAddress": "team@googlegroups.com"}'
```

### Transfer ownership

```
gws drive permissions create <FILE_ID> --json '{"role": "owner", "type": "user", "emailAddress": "newowner@example.com"}' \
  --params '{"transferOwnership": true}'
```
