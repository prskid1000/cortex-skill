# `claw drive` — Google Drive Reference

CLI wrapper over the Google Drive API (via `gws`). Works on any file type — Sheets, Docs, Slides, PDFs, binaries.

## Contents

- **CREATE / UPLOAD**
  - [Upload file](#11-upload) · [Copy file](#12-copy)
- **READ / DOWNLOAD**
  - [Download / Export](#21-download) · [List files](#22-list) · [File info](#23-info)
- **EDIT / MANAGE**
  - [Move file](#31-move) · [Rename file](#32-rename) · [Delete file](#33-delete)
- **SHARE**
  - [Grant access](#41-share) · [List permissions](#42-share-list) · [Revoke access](#43-share-revoke)

---

## Critical Rules

1. **ID vs Path** — Use `FILE_ID` for existing Drive items and standard local paths for uploads/downloads.
2. **Safe Deletes** — `delete` is permanent in Drive (does not use Trash). Use with caution.
3. **Conversion** — `upload` auto-converts `.xlsx`/`.csv`/`.docx`/`.pptx` to Google-native by default; pass `--no-convert` to keep them as binary blobs.
4. **Auth** — Depends on `gws auth login` being completed first.

---

## 1.1 upload
Upload a local file to Drive. Auto-converts office formats to Google-native unless `--no-convert`.
```bash
claw drive upload --from <LOCAL_FILE> [--name <DRIVE_NAME>] [--parent <FOLDER_ID>] [--convert/--no-convert] [--mime <TYPE>] [--description <TEXT>]
```

## 1.2 copy
Duplicate a file in Drive.
```bash
claw drive copy <FILE_ID> [--name <NEW_NAME>] [--json]
```

---

## 2.1 download
Download a Drive file. For Google-native files (Docs/Sheets/Slides), pass `--as <fmt>` to export.
```bash
claw drive download <FILE_ID> --out <OUT_PATH> [--as pdf|xlsx|csv|docx|md|txt|html|epub|...]
```

## 2.2 list
List files in Drive.
```bash
claw drive list [--query <Q>] [--parent <FOLDER_ID>] [--json]
```

## 2.3 info
Fetch metadata for a single file (name, mime, size, parents, owners, links).
```bash
claw drive info <FILE_ID> [--fields <CSV>] [--json]
```

---

## 3.1 move
Move a file to a different folder.
```bash
claw drive move <FILE_ID> --to <FOLDER_ID> [--json]
```

## 3.2 rename
Rename a file in Drive.
```bash
claw drive rename <FILE_ID> --name <NEW_NAME> [--json]
```

## 3.3 delete
Permanently delete a file.
```bash
claw drive delete <FILE_ID> [--force]
```

---

## 4.1 share
Grant access to a user, group, domain, or anyone.
```bash
claw drive share <FILE_ID> --role reader|commenter|writer [--email <ADDR>] [--domain <DOM>] [--anyone] [--json]
```

## 4.2 share-list
List all permissions (emails and roles) for a file.
```bash
claw drive share-list <FILE_ID> [--json]
```

## 4.3 share-revoke
Remove a user's access.
```bash
claw drive share-revoke <FILE_ID> --email <USER_EMAIL> [--json]
```

---

## Footguns
- **No Trash** — `claw drive delete` bypasses the Trash folder.
- **Conversion default** — `upload` defaults to converting office formats; pass `--no-convert` if you want a binary blob in Drive.
- **Native exports need `--as`** — Downloading a Google Doc/Sheet/Slide without `--as` errors out; pick a format.

## Escape Hatch
- [gws CLI reference](../gws-cli.md#drive) — Full access to advanced queries, fields, and metadata.

---

## Quick Reference
| Task | Command |
|------|---------|
| Upload & Convert | `claw drive upload --from data.xlsx` |
| Upload as Blob | `claw drive upload --from data.xlsx --no-convert` |
| Export Sheet to xlsx | `claw drive download FILE_ID --out report.xlsx --as xlsx` |
| Export Doc to PDF | `claw drive download FILE_ID --out doc.pdf --as pdf` |
| List Drive Files | `claw drive list --json` |
| File Metadata | `claw drive info FILE_ID --json` |
| Delete File | `claw drive delete FILE_ID --force` |
