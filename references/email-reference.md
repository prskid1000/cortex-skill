# Email / MIME Composition + Gmail CLI Reference

---

## Python MIME (email.mime)

### Imports
```python
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email import encoders
import base64
```

---

### MIMEText

```python
# Plain text
msg = MIMEText("Hello, world!", "plain", "utf-8")

# HTML
msg = MIMEText("<h1>Hello</h1><p>World</p>", "html", "utf-8")
```

---

### MIMEMultipart

| Subtype | Purpose |
|---------|---------|
| `mixed` | Attachments alongside text body |
| `alternative` | Multiple representations (plain + HTML) |
| `related` | HTML with inline images (Content-ID references) |

```python
# Mixed (text + attachments)
msg = MIMEMultipart("mixed")
msg.attach(MIMEText("Body text", "plain"))

# Alternative (plain + HTML)
msg = MIMEMultipart("alternative")
msg.attach(MIMEText("Plain body", "plain"))
msg.attach(MIMEText("<h1>HTML body</h1>", "html"))

# Related (HTML with inline images)
msg = MIMEMultipart("related")
html = MIMEText('<img src="cid:logo_id">', "html")
msg.attach(html)
with open("logo.png", "rb") as f:
    img = MIMEImage(f.read())
    img.add_header("Content-ID", "<logo_id>")
    img.add_header("Content-Disposition", "inline", filename="logo.png")
    msg.attach(img)
```

---

### Attachments (MIMEBase + encode_base64)

```python
with open("report.pdf", "rb") as f:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename="report.pdf")
    msg.attach(part)
```

#### Shortcut with MIMEApplication
```python
with open("report.xlsx", "rb") as f:
    part = MIMEApplication(f.read(), Name="report.xlsx")
    part["Content-Disposition"] = 'attachment; filename="report.xlsx"'
    msg.attach(part)
```

---

### Headers

| Header | Purpose | Example |
|--------|---------|---------|
| `To` | Primary recipients | `msg["To"] = "a@x.com, b@x.com"` |
| `From` | Sender | `msg["From"] = "me@x.com"` |
| `Cc` | Carbon copy | `msg["Cc"] = "c@x.com"` |
| `Bcc` | Blind carbon copy | `msg["Bcc"] = "d@x.com"` |
| `Subject` | Subject line | `msg["Subject"] = "Report"` |
| `Reply-To` | Reply address | `msg["Reply-To"] = "reply@x.com"` |
| `In-Reply-To` | Message being replied to | `msg["In-Reply-To"] = "<msgid@x.com>"` |
| `References` | Thread chain | `msg["References"] = "<id1> <id2>"` |
| `Date` | Send date | `msg["Date"] = email.utils.formatdate(localtime=True)` |
| `Message-ID` | Unique message ID | `msg["Message-ID"] = email.utils.make_msgid()` |

---

### Gmail API Raw Format (base64url)

```python
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
# Use as: {"raw": raw} in Gmail API send
```

---

### Multiple Attachments Pattern

```python
msg = MIMEMultipart("mixed")
msg["To"] = "recipient@example.com"
msg["From"] = "sender@example.com"
msg["Subject"] = "Monthly Reports"

# Body
msg.attach(MIMEText("Please find the reports attached.", "plain"))

# Attach multiple files
for filepath in ["report.pdf", "data.xlsx", "chart.png"]:
    with open(filepath, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment",
                        filename=os.path.basename(filepath))
        msg.attach(part)
```

---

### Inline Images (Content-ID for HTML email)

```python
msg = MIMEMultipart("related")

html_body = """\
<html>
<body>
  <h1>Report</h1>
  <img src="cid:chart_img">
  <p>See the chart above.</p>
</body>
</html>
"""
msg.attach(MIMEText(html_body, "html"))

with open("chart.png", "rb") as f:
    img = MIMEImage(f.read(), _subtype="png")
    img.add_header("Content-ID", "<chart_img>")
    img.add_header("Content-Disposition", "inline", filename="chart.png")
    msg.attach(img)
```

---

### Reply Threading

```python
# Replying to an existing message
original_message_id = "<original-id@mail.gmail.com>"
original_references = "<ref1@mail.gmail.com> <ref2@mail.gmail.com>"

msg["In-Reply-To"] = original_message_id
msg["References"] = f"{original_references} {original_message_id}"
msg["Subject"] = "Re: Original Subject"

# For Gmail API, also set threadId in the send request:
# {"raw": raw, "threadId": "thread_id_here"}
```

---

---

## Gmail CLI (gws gmail)

### Messages

#### List
```bash
gws gmail messages list --query "SEARCH_QUERY" --maxResults 10
gws gmail messages list --query "from:boss@x.com after:2025/01/01 has:attachment"
gws gmail messages list --query "is:unread label:INBOX" --maxResults 25
gws gmail messages list --labelIds INBOX --maxResults 5
```

#### Get
```bash
gws gmail messages get --id MESSAGE_ID
gws gmail messages get --id MESSAGE_ID --format full
gws gmail messages get --id MESSAGE_ID --format metadata --metadataHeaders "From,Subject,Date"
gws gmail messages get --id MESSAGE_ID --format minimal
gws gmail messages get --id MESSAGE_ID --format raw
```

| Format | Returns |
|--------|---------|
| `full` | Parsed headers + body parts (default) |
| `metadata` | Headers only (use with `--metadataHeaders`) |
| `minimal` | IDs and labels only |
| `raw` | Full RFC 2822 base64url encoded |

#### Send
```bash
gws gmail messages send --to "a@x.com" --subject "Hello" --body "Message body"
gws gmail messages send --to "a@x.com" --subject "Report" --body "See attached" --attachments "/tmp/report.pdf"
gws gmail messages send --to "a@x.com" --cc "b@x.com" --bcc "c@x.com" --subject "S" --body "B"
gws gmail messages send --to "a@x.com" --subject "Re: Thread" --body "Reply" --threadId THREAD_ID --inReplyTo MESSAGE_ID
gws gmail messages send --raw BASE64URL_ENCODED_MESSAGE
```

#### Trash / Untrash / Delete
```bash
gws gmail messages trash --id MESSAGE_ID
gws gmail messages untrash --id MESSAGE_ID
gws gmail messages delete --id MESSAGE_ID              # permanent delete
```

#### Modify labels
```bash
gws gmail messages modify --id MESSAGE_ID --addLabelIds "STARRED" --removeLabelIds "UNREAD"
gws gmail messages batchModify --ids "ID1,ID2,ID3" --addLabelIds "Label_1"
```

---

### Drafts

```bash
gws gmail drafts list --maxResults 10
gws gmail drafts get --id DRAFT_ID
gws gmail drafts create --to "a@x.com" --subject "Draft" --body "Content"
gws gmail drafts update --id DRAFT_ID --subject "Updated"
gws gmail drafts send --id DRAFT_ID
gws gmail drafts delete --id DRAFT_ID
```

---

### Labels

```bash
gws gmail labels list
gws gmail labels get --id LABEL_ID
gws gmail labels create --name "Projects/Active"
gws gmail labels update --id LABEL_ID --name "Projects/Archive"
gws gmail labels delete --id LABEL_ID
```

System labels: `INBOX`, `SENT`, `DRAFT`, `TRASH`, `SPAM`, `STARRED`, `UNREAD`, `IMPORTANT`, `CATEGORY_PERSONAL`, `CATEGORY_SOCIAL`, `CATEGORY_PROMOTIONS`, `CATEGORY_UPDATES`, `CATEGORY_FORUMS`

---

### Threads

```bash
gws gmail threads list --query "subject:project" --maxResults 10
gws gmail threads get --id THREAD_ID
gws gmail threads modify --id THREAD_ID --addLabelIds "STARRED"
gws gmail threads trash --id THREAD_ID
gws gmail threads untrash --id THREAD_ID
gws gmail threads delete --id THREAD_ID
```

---

### Attachments

```bash
gws gmail attachments get --messageId MESSAGE_ID --id ATTACHMENT_ID --output "/tmp/file.pdf"
```

Retrieve attachment ID from message parts: look for `body.attachmentId` in parts with `filename`.

---

### History

```bash
gws gmail history list --startHistoryId HISTORY_ID --historyTypes "messageAdded,labelAdded"
```

History types: `messageAdded`, `messageDeleted`, `labelAdded`, `labelRemoved`

---

### Search Operators (Comprehensive)

| Operator | Purpose | Example |
|----------|---------|---------|
| `from:` | Sender | `from:alice@x.com` |
| `to:` | Recipient | `to:bob@x.com` |
| `cc:` | CC recipient | `cc:charlie@x.com` |
| `bcc:` | BCC recipient | `bcc:dave@x.com` |
| `subject:` | Subject line | `subject:meeting` |
| `label:` | Label | `label:work` |
| `has:attachment` | Has attachment | `has:attachment` |
| `has:drive` | Has Drive link | `has:drive` |
| `has:document` | Has Docs link | `has:document` |
| `has:spreadsheet` | Has Sheets link | `has:spreadsheet` |
| `has:presentation` | Has Slides link | `has:presentation` |
| `has:youtube` | Has YouTube link | `has:youtube` |
| `list:` | Mailing list | `list:info@group.com` |
| `filename:` | Attachment name | `filename:report.pdf` |
| `filename:pdf` | Attachment type | `filename:pdf` |
| `in:anywhere` | All mail | `in:anywhere` |
| `in:inbox` | Inbox | `in:inbox` |
| `in:sent` | Sent | `in:sent` |
| `in:drafts` | Drafts | `in:drafts` |
| `in:trash` | Trash | `in:trash` |
| `in:spam` | Spam | `in:spam` |
| `is:starred` | Starred | `is:starred` |
| `is:unread` | Unread | `is:unread` |
| `is:read` | Read | `is:read` |
| `is:important` | Important | `is:important` |
| `is:snoozed` | Snoozed | `is:snoozed` |
| `after:` | After date | `after:2025/01/15` |
| `before:` | Before date | `before:2025/02/01` |
| `older:` | Older than | `older:7d` |
| `newer:` | Newer than | `newer:2d` |
| `older_than:` | Relative age | `older_than:1m` (1 month) |
| `newer_than:` | Relative age | `newer_than:3d` |
| `size:` | Size threshold | `size:5000000` (5MB) |
| `larger:` | Larger than | `larger:10M` |
| `smaller:` | Smaller than | `smaller:1M` |
| `category:` | Category | `category:updates` |
| `deliveredto:` | Delivered to | `deliveredto:me@x.com` |
| `rfc822msgid:` | Message ID | `rfc822msgid:<id@x.com>` |
| `OR` | Boolean OR | `from:a OR from:b` |
| `-` | Negate | `-from:noreply@x.com` |
| `""` | Exact phrase | `"project deadline"` |
| `()` | Grouping | `(from:a OR from:b) has:attachment` |
| `AROUND` | Proximity | `meeting AROUND 5 friday` |
