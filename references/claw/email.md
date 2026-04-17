# `claw email` — Gmail Send / Reply / Forward / Search Reference

> Source directory: [scripts/claw/src/claw/email/](../../scripts/claw/src/claw/email/)

CLI wrapper around Python `email.mime` + `gws gmail`. Handles RFC 2822 assembly, base64url encoding, threading headers, and attachment MIME-type detection so you don't have to.

Library API for escape hatches: Python stdlib `email.mime` + [references/gws-cli.md § Gmail](../gws-cli.md#gmail). See [When `claw email` Isn't Enough](#when-claw-email-isnt-enough).

## Contents

- **SEND a new message**
  - [New email (plain / HTML / mixed)](#11-send) · [Save as draft](#12-draft)
- **REPLY to an existing thread**
  - [Reply / reply-all with threading headers](#21-reply)
- **FORWARD a message**
  - [Forward with optional re-edit](#31-forward)
- **SEARCH the mailbox**
  - [Gmail search operators, JSON output](#41-search)
- **DOWNLOAD attachments**
  - [By message + attachment id](#51-download-attachment)
- **When `claw email` isn't enough** — [escape hatches](#when-claw-email-isnt-enough)

---

## Critical Rules

1. **Safe-by-default sends** — no message is sent until MIME validates and headers parse. `--dry-run` prints the assembled RFC 2822 payload (truncated to 2 KiB per part) + computed headers, without touching Gmail. `claw email send --dry-run` is the canonical pre-flight check.
2. **Attachment syntax: `@` prefix** — `--attach @path/to/file.pdf` distinguishes a file path from a literal string, matching `swaks` convention. `--inline cid=@path/to/img.png` does the same for inline images. Paths without `@` are rejected with exit code 2.
3. **Threading headers are mandatory on `reply`/`forward`** — Gmail silently breaks threads (drops the message into a new conversation) when `In-Reply-To` / `References` are missing. `claw email reply` populates both automatically from the parent message; don't override unless you know what you're doing.
4. **Structured output** — every verb supports `--json`. `search` emits NDJSON (one message per line) on stdout; `send`/`reply`/`forward`/`draft` emit a single result object `{id, threadId, labelIds}`. Logs (progress, auth events) stay on stderr. Errors under `--json` emit `{error, code, hint, doc_url}` to stderr.
5. **Exit codes** — `0` success, `1` generic, `2` usage error, `3` partial (e.g. one of N recipients rejected), `4` bad input (missing attachment, malformed address), `5` auth / API error, `130` SIGINT.
6. **Help** — `claw email --help`, `claw email <verb> --help`, `--examples` prints runnable recipes, `--progress=json` streams upload progress (relevant for large attachments).
7. **Encoding** — UTF-8 everywhere. `--subject` and bodies are interpreted as UTF-8 from the command line; non-ASCII subjects are RFC 2047-encoded automatically.
8. **Auth** — `claw email` uses the `gws` OAuth session. If scopes are missing (`gmail.send`, `gmail.modify`, `gmail.readonly`), the first affected call fails with `code=AUTH_SCOPE` pointing at `claw doctor` for the re-login invocation.
9. **Common output flags** — every mutating verb inherits `--force`, `--backup`, `--dry-run`, `--json`, `--quiet`, `--mkdir` via the shared `@common_output_options` decorator. Individual verb blocks only call them out when the verb overrides the default; run `claw email <verb> --help` for the authoritative per-verb flag list.

### Gmail API auth footguns

- `gmail.send` does **not** imply `gmail.readonly` — `download-attachment` and `search` need their own scopes.
- `download-attachment` specifically needs `gmail.modify` (Gmail's scope model is quirky — `readonly` alone can't fetch attachment bodies on some org setups).
- The Cloud Console step of enabling the Gmail API is separate from the OAuth consent screen. `claw doctor` verifies both.

---

## 1. SEND

### 1.1 `send`

> Source: [scripts/claw/src/claw/email/send.py](../../scripts/claw/src/claw/email/send.py)

Compose and send a new message.

```
claw email send --to T [--cc C]... [--bcc B]... --subject S
                (--body TEXT | --body-file F | --body-stdin)
                [--html FILE] [--attach @PATH]... [--inline CID=@PATH]...
                [--from ADDR] [--reply-to ADDR] [--header K=V]...
                [--dry-run] [--json]
```

Flags:

- `--to`, `--cc`, `--bcc` — repeatable; comma-separated within a single value also works.
- `--body` — literal string. `--body-file F` — read plain-text body from file. `--body-stdin` — read from stdin (useful with shell pipelines).
- `--html FILE` — attach a parallel HTML alternative. When both plain body and `--html` are supplied, claw builds a `multipart/alternative` container.
- `--attach @PATH` — attach a file. MIME type auto-detected via `mimetypes` with an override table for common types (`.xlsx` → `openxmlformats...spreadsheetml.sheet`, `.eml` → `message/rfc822`). Use `--attach @file.bin:application/octet-stream` to force.
- `--inline CID=@PATH` — inline image referenced from HTML body as `<img src="cid:CID">`. Automatically sets `Content-ID: <CID>` and `Content-Disposition: inline`.
- `--from ADDR` — override the sender (Gmail must have SendAs delegation for this address; otherwise fails with `code=SEND_AS_NOT_CONFIGURED`).
- `--header K=V` — add arbitrary headers (`X-My-Thing: value`).

Examples:

```
claw email send --to alice@example.com --subject "Q3 numbers" \
  --body "Attached." --attach @/tmp/q3.xlsx
```

```
claw email send --to team@example.com --cc boss@example.com \
  --subject "Release notes" \
  --body-file notes.txt --html notes.html \
  --inline logo=@/tmp/logo.png
```

### 1.2 `draft`

> Source: [scripts/claw/src/claw/email/draft.py](../../scripts/claw/src/claw/email/draft.py)

Same flag surface as `send`, but creates a Gmail draft instead of sending.

```
claw email draft --to T --subject S --body TEXT [--attach @PATH]... [--json]
```

Example:

```
claw email draft --to alice@example.com --subject "Follow up" \
  --body "Let me know." --attach @/tmp/agenda.pdf
```

Output (with `--json`): `{"id": "<DRAFT_ID>", "message": {"id": "<MSG_ID>", "threadId": "<THREAD_ID>"}}`.

---

## 2. REPLY

### 2.1 `reply`

> Source: [scripts/claw/src/claw/email/reply.py](../../scripts/claw/src/claw/email/reply.py)

Reply to a specific message, preserving the thread. `claw` fetches the parent's `Message-Id` + `References` and injects them into the new message.

```
claw email reply <msg-id>
                 (--body B | --body-file F | --body-stdin)
                 [--all] [--remove EMAIL]... [--add-cc EMAIL]...
                 [--html FILE] [--attach @PATH]... [--inline CID=@PATH]...
                 [--subject S] [--dry-run] [--json]
```

Flags:

- `<msg-id>` — positional Gmail message id (the short hex id from `search`, not the RFC 2822 `Message-Id` header).
- `--all` — reply-all: populate `To` with the parent's `From` and `Cc` with everyone else on the thread (minus the authenticated user).
- `--remove EMAIL` — strip an address from the computed `To`/`Cc` lists (common on `--all`: "reply-all except Bob").
- `--subject` — override subject (defaults to `Re: <parent subject>` if not already prefixed).

Examples:

```
claw email reply 18e2f3a --body "Thanks, confirmed."
```

```
claw email reply 18e2f3a --all --remove bob@example.com \
  --body-file response.txt --attach @/tmp/updated.pdf
```

Gmail-silently-breaks-threads note: this verb exists precisely because manual `gws gmail users messages send` calls drop `In-Reply-To`/`References` and land in a new thread. Always prefer `claw email reply` over hand-rolling.

---

## 3. FORWARD

### 3.1 `forward`

> Source: [scripts/claw/src/claw/email/forward.py](../../scripts/claw/src/claw/email/forward.py)

Forward a message to new recipients. Attachments from the original are re-attached unless `--no-attachments` is set.

```
claw email forward <msg-id> --to T [--cc C]... [--bcc B]...
                   (--body B | --body-file F | --body-stdin)
                   [--subject S] [--no-attachments] [--strip-html]
                   [--attach @PATH]... [--dry-run] [--json]
```

Flags:

- `--subject` — defaults to `Fwd: <parent subject>`.
- `--no-attachments` — forward just the text/html body, drop original attachments.
- `--strip-html` — forward plain-text only; useful when the parent has inline images that don't make sense out of context.

Example:

```
claw email forward 18e2f3a --to dave@example.com \
  --body "FYI — original below." --no-attachments
```

---

## 4. SEARCH

### 4.1 `search`

> Source: [scripts/claw/src/claw/email/search.py](../../scripts/claw/src/claw/email/search.py)

Query the mailbox using Gmail's search operators. Returns metadata (no body by default — use `--format full` for the whole payload).

```
claw email search --q "QUERY" [--max N] [--format table|json|full]
                              [--include-spam-trash] [--label L]
```

Flags:

- `--q` — Gmail search operators (`from:`, `to:`, `subject:`, `has:attachment`, `newer_than:7d`, `label:Projects`, `before:2025/12/31`, `filename:pdf`, `larger:5M`). See [gws-cli.md § Gmail Search Operators](../gws-cli.md#gmail-search-operators).
- `--max N` — cap results (default 25). Large queries auto-paginate.
- `--format` — `table` (default, human-readable), `json` (NDJSON, one message per line), `full` (includes decoded body — slower).
- `--label L` — shortcut for `label:L` added to the query.

Examples:

```
claw email search --q "from:boss@example.com newer_than:7d has:attachment" --max 10
```

```
claw email search --q "is:unread subject:(invoice OR receipt)" --format json \
  | jq '.subject'
```

---

## 5. DOWNLOAD ATTACHMENT

### 5.1 `download-attachment`

> Source: [scripts/claw/src/claw/email/download_attachment.py](../../scripts/claw/src/claw/email/download_attachment.py)

Save an attachment to disk by message id + attachment id. Attachment ids are returned by `claw email search --format full` under `payload.parts[].body.attachmentId`.

```
claw email download-attachment <msg-id> <att-id> --out PATH
                               [--force] [--verify-hash SHA256]
```

Flags:

- `--force` — overwrite an existing file at `--out`.
- `--verify-hash` — check the decoded bytes against a known SHA-256; failure exits 4.

Example:

```
claw email download-attachment 18e2f3a ANGjdJ... --out /tmp/invoice.pdf
```

Scope reminder: needs `gmail.modify` on many org tenants. `gmail.readonly` alone can fail with `code=ATTACHMENT_FORBIDDEN`.

---

## When `claw email` Isn't Enough

Drop into the library / raw `gws` for:

| Use case | Why `claw` can't do it | Escape hatch |
|---|---|---|
| Bulk mail merge across >100 recipients with per-recipient variables | `send` sends one RFC 2822 per call; no backoff / batching | Python `email.mime` + `gws gmail users messages send` in a loop, with 1s sleep + retry-on-429 |
| Calendar invites (iCalendar `METHOD:REQUEST`) | Requires `text/calendar` part + `ATTENDEE;RSVP=TRUE` line | Build `MIMEText(ical, "calendar", "utf-8")` + `Content-Type: text/calendar; method=REQUEST` directly |
| S/MIME signing or PGP-encrypted bodies | No crypto surface | Use `email.mime.multipart` with detached signature part (`multipart/signed`) via `cryptography` / `python-gnupg` |
| Label mutation (`addLabelIds`, `removeLabelIds`) on fetched messages | Out of scope for `claw email` | [`gws gmail users messages modify`](../gws-cli.md#modify--addremove-labels) |
| Batch message delete / trash | No bulk verb | [`gws gmail users messages batchModify`](../gws-cli.md#batchmodify--modify-labels-on-multiple-messages) + `trash` |
| Streaming new-email watcher | Long-running connection | `gws gmail +watch` (NDJSON) — see [gws-cli.md § Ergonomic +helper](../gws-cli.md#ergonomic-helper-commands) |

**`email.mime` (Python stdlib)** — part of Python — [docs](https://docs.python.org/3/library/email.html)
- Gmail API expects the raw RFC 2822 as `base64url` (urlsafe with no padding stripped) in the `raw` field — `base64.urlsafe_b64encode(msg.as_bytes()).decode()`. Standard `b64encode` with `+`/`/` gets rejected with an opaque `Invalid value for message` error.
- The modern `email.message.EmailMessage` (3.6+) handles attachments via `add_attachment(data, maintype, subtype, filename=...)`; mixing it with the legacy `MIMEMultipart` / `MIMEBase` shape is what every Gmail tutorial gets wrong — pick one.
- Gmail caps the base64-encoded message at ~35 MB (~25 MB of raw bytes, ~18 MB of binary attachment); use a Drive upload + share link for anything larger.

## Footguns

- **Quoted commas in `--to` / `--cc`** — `--to "alice@x.com, bob@x.com"` works; `--to alice@x.com,bob@x.com` without quotes works too. Repeating `--to` is safest: `--to a@x --to b@x`.
- **`--from ADDR` without SendAs** — Gmail rejects with 400 if the address isn't in Settings → Accounts → Send mail as. Surfaces as `code=SEND_AS_NOT_CONFIGURED` with a hint.
- **Large attachments** — Gmail caps raw-message size at ~25 MB after base64 (≈18 MB of binary). Larger files fail with `code=SIZE_LIMIT`; use Drive upload + `claw sheet share` + link instead.
- **`--inline` without matching `cid:`** — a stray inline image with no reference in the HTML body just shows up as a regular attachment. `--dry-run` flags this with a warning.
- **Forward preserves Message-ID** — no, it doesn't. A forward is a new message; the original is attached (or inlined). Don't rely on forward identity for deduplication.

---

## Quick Reference

| Task | One-liner |
|------|-----------|
| Send plain | `claw email send --to a@x --subject S --body "hi"` |
| Send with attachment | `claw email send --to a@x --subject S --body B --attach @file.pdf` |
| Send HTML + inline image | `claw email send --to a@x --subject S --body-file t.txt --html h.html --inline logo=@logo.png` |
| Draft | `claw email draft --to a@x --subject S --body B` |
| Reply | `claw email reply <MSG_ID> --body "thanks"` |
| Reply-all minus Bob | `claw email reply <MSG_ID> --all --remove bob@x --body B` |
| Forward | `claw email forward <MSG_ID> --to d@x --body "fyi"` |
| Search unread w/ attachments | `claw email search --q "is:unread has:attachment" --format json` |
| Download attachment | `claw email download-attachment <MSG_ID> <ATT_ID> --out f.pdf` |
| Preview without sending | `claw email send ... --dry-run` |
