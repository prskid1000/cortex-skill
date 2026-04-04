# Email Workflows Examples

Working code blocks for Python email composition and Gmail via `gws` CLI.

---

## Python Email Composition (MIME)

### Plain Text Email

```python
from email.mime.text import MIMEText

msg = MIMEText("Hello,\n\nThis is a plain text email.\n\nRegards,\nSender")
msg["Subject"] = "Monthly Update"
msg["From"] = "sender@example.com"
msg["To"] = "recipient@example.com"
msg["Cc"] = "cc@example.com"

# msg.as_string() gives the full RFC 2822 message
print(msg.as_string())
```

### HTML Email with Plain Text Fallback

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

msg = MIMEMultipart("alternative")
msg["Subject"] = "Sales Report"
msg["From"] = "sender@example.com"
msg["To"] = "recipient@example.com"

plain = MIMEText("Sales report attached. View in HTML for full formatting.", "plain")

html = MIMEText("""
<html>
<body>
  <h2 style="color: #2c3e50;">Monthly Sales Report</h2>
  <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
    <tr style="background: #3498db; color: white;">
      <th>Region</th><th>Revenue</th><th>Growth</th>
    </tr>
    <tr><td>North</td><td>$125,000</td><td style="color:green;">+12%</td></tr>
    <tr><td>South</td><td>$98,000</td><td style="color:green;">+8%</td></tr>
    <tr><td>West</td><td>$87,000</td><td style="color:red;">-3%</td></tr>
  </table>
  <p style="color: #7f8c8d; font-size: 12px;">Auto-generated report</p>
</body>
</html>
""", "html")

msg.attach(plain)
msg.attach(html)
```

### Email with Single Attachment (PDF)

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

msg = MIMEMultipart()
msg["Subject"] = "Invoice #1234"
msg["From"] = "billing@example.com"
msg["To"] = "client@example.com"

msg.attach(MIMEText("Please find your invoice attached.", "plain"))

with open("/tmp/invoice.pdf", "rb") as f:
    attachment = MIMEApplication(f.read(), _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename="invoice_1234.pdf")
    msg.attach(attachment)
```

### Email with Multiple Attachments (PDF + Excel + Image)

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from pathlib import Path

msg = MIMEMultipart()
msg["Subject"] = "Q4 Report Package"
msg["From"] = "reports@example.com"
msg["To"] = "team@example.com"

msg.attach(MIMEText("Attached: Q4 report (PDF), raw data (Excel), and summary chart (PNG).", "plain"))

attachments = [
    ("/tmp/report.pdf", "application", "pdf"),
    ("/tmp/data.xlsx", "application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
]

for filepath, maintype, subtype in attachments:
    with open(filepath, "rb") as f:
        part = MIMEApplication(f.read(), _subtype=subtype)
        part.add_header("Content-Disposition", "attachment", filename=Path(filepath).name)
        msg.attach(part)

# Image attachment
with open("/tmp/chart.png", "rb") as f:
    img_part = MIMEImage(f.read(), _subtype="png")
    img_part.add_header("Content-Disposition", "attachment", filename="chart.png")
    msg.attach(img_part)
```

### Reply to Thread (In-Reply-To + References + threadId)

```python
from email.mime.text import MIMEText

msg = MIMEText("Thanks for the update. I agree with the proposal.")
msg["Subject"] = "Re: Project Proposal"
msg["From"] = "me@example.com"
msg["To"] = "colleague@example.com"
msg["In-Reply-To"] = "<original-message-id@example.com>"
msg["References"] = "<original-message-id@example.com>"

# When sending via Gmail API, include threadId to keep in same thread
# See Gmail send section below
```

### Inline Image in HTML Email (Content-ID)

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

msg = MIMEMultipart("related")
msg["Subject"] = "Report with Chart"
msg["From"] = "sender@example.com"
msg["To"] = "recipient@example.com"

html = MIMEText("""
<html>
<body>
  <h2>Performance Summary</h2>
  <p>See the chart below:</p>
  <img src="cid:chart_image" width="600" />
  <p>Generated automatically.</p>
</body>
</html>
""", "html")
msg.attach(html)

with open("/tmp/chart.png", "rb") as f:
    img = MIMEImage(f.read(), _subtype="png")
    img.add_header("Content-ID", "<chart_image>")
    img.add_header("Content-Disposition", "inline", filename="chart.png")
    msg.attach(img)
```

---

## Gmail via `gws` CLI

### Search Unread Emails

```bash
# List unread emails
gws gmail messages list --params '{"q": "is:unread", "maxResults": 10}' --format json

# Search with multiple criteria
gws gmail messages list --params '{"q": "is:unread from:boss@company.com after:2025/01/01", "maxResults": 20}' --format json

# Search by subject
gws gmail messages list --params '{"q": "subject:\"monthly report\"", "maxResults": 5}' --format json
```

### Read Email with Metadata

```bash
# Get full message (headers + body)
gws gmail messages get <MESSAGE_ID> --format json

# Get specific fields only
gws gmail messages get <MESSAGE_ID> --fields "id,threadId,labelIds,payload/headers" --format json

# Get message with metadata format (headers only, no body)
gws gmail messages get <MESSAGE_ID> --params '{"format": "metadata", "metadataHeaders": ["From","To","Subject","Date"]}' --format json
```

### Send Email (base64 Raw)

```python
import subprocess, base64
from email.mime.text import MIMEText

msg = MIMEText("Hello from the pipeline!")
msg["Subject"] = "Automated Report"
msg["From"] = "me@gmail.com"
msg["To"] = "recipient@example.com"

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")

subprocess.run([
    "gws", "gmail", "messages", "send",
    "--json", f'{{"raw": "{raw}"}}',
], check=True)
```

### Send Email with Attachment (base64 Raw)

```python
import subprocess, base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

msg = MIMEMultipart()
msg["Subject"] = "Invoice Attached"
msg["From"] = "me@gmail.com"
msg["To"] = "client@example.com"
msg.attach(MIMEText("Please find the invoice attached.", "plain"))

with open("/tmp/invoice.pdf", "rb") as f:
    att = MIMEApplication(f.read(), _subtype="pdf")
    att.add_header("Content-Disposition", "attachment", filename="invoice.pdf")
    msg.attach(att)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")

subprocess.run([
    "gws", "gmail", "messages", "send",
    "--json", f'{{"raw": "{raw}"}}',
], check=True)
```

### Send Reply in Thread

```python
import subprocess, base64
from email.mime.text import MIMEText

msg = MIMEText("Confirmed, will proceed with the plan.")
msg["Subject"] = "Re: Project Plan"
msg["From"] = "me@gmail.com"
msg["To"] = "colleague@example.com"
msg["In-Reply-To"] = "<original-message-id@mail.gmail.com>"
msg["References"] = "<original-message-id@mail.gmail.com>"

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
thread_id = "18abc1234def5678"

subprocess.run([
    "gws", "gmail", "messages", "send",
    "--json", f'{{"raw": "{raw}", "threadId": "{thread_id}"}}',
], check=True)
```

### Mark as Read

```bash
gws gmail messages modify <MESSAGE_ID> --json '{"removeLabelIds": ["UNREAD"]}'
```

### Download Attachment

```bash
# List message to find attachment IDs
gws gmail messages get <MESSAGE_ID> --fields "payload/parts" --format json

# Download attachment
gws gmail messages attachments get <ATTACHMENT_ID> \
  --params '{"messageId": "<MESSAGE_ID>"}' \
  --output /tmp/downloaded_file.pdf
```

### List Emails with Search Operators

```bash
# Emails from specific sender in last 7 days
gws gmail messages list --params '{"q": "from:sender@example.com newer_than:7d"}' --format json

# Emails with attachments larger than 5MB
gws gmail messages list --params '{"q": "has:attachment larger:5M"}' --format json

# Emails in a specific label
gws gmail messages list --params '{"q": "label:projects/active", "maxResults": 50}' --format json

# Emails to me (not CC/BCC)
gws gmail messages list --params '{"q": "deliveredto:me@gmail.com is:unread"}' --format json
```

### Draft Creation

```python
import subprocess, base64
from email.mime.text import MIMEText

msg = MIMEText("Draft content here - will review before sending.")
msg["Subject"] = "Proposal Draft"
msg["From"] = "me@gmail.com"
msg["To"] = "recipient@example.com"

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")

subprocess.run([
    "gws", "gmail", "drafts", "create",
    "--json", f'{{"message": {{"raw": "{raw}"}}}}',
], check=True)
```

---

## Full Workflow: Generate Report, Compose Email, Send with Attachment

```python
import subprocess, base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# --- Step 1: Generate Excel report ---
wb = Workbook()
ws = wb.active
ws.title = "Sales Report"

header_font = Font(bold=True, color="FFFFFF", size=12)
header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
thin_border = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"), bottom=Side(style="thin"),
)

headers = ["Region", "Q1", "Q2", "Q3", "Q4", "Total"]
for col, header in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=header)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal="center")
    cell.border = thin_border

data = [
    ["North", 125000, 132000, 141000, 155000],
    ["South", 98000, 105000, 112000, 120000],
    ["East", 87000, 91000, 95000, 101000],
    ["West", 76000, 80000, 83000, 89000],
]
for row_idx, row_data in enumerate(data, 2):
    for col_idx, value in enumerate(row_data, 1):
        cell = ws.cell(row=row_idx, column=col_idx, value=value)
        cell.border = thin_border
        if col_idx > 1:
            cell.number_format = '#,##0'
    # Total formula
    total_cell = ws.cell(row=row_idx, column=6)
    total_cell.value = f"=SUM(B{row_idx}:E{row_idx})"
    total_cell.number_format = '#,##0'
    total_cell.border = thin_border
    total_cell.font = Font(bold=True)

for col in range(1, 7):
    ws.column_dimensions[chr(64 + col)].width = 15

report_path = "/tmp/sales_report.xlsx"
wb.save(report_path)

# --- Step 2: Compose email with attachment ---
msg = MIMEMultipart()
msg["Subject"] = "Q4 Sales Report"
msg["From"] = "me@gmail.com"
msg["To"] = "manager@example.com"
msg["Cc"] = "team@example.com"

msg.attach(MIMEText("""Hi Team,

Please find attached the quarterly sales report with regional breakdowns.

Key highlights:
- North region leads with $553K total
- All regions show positive growth
- Company-wide revenue up 11% YoY

Let me know if you have questions.

Best regards""", "plain"))

with open(report_path, "rb") as f:
    att = MIMEApplication(f.read(), _subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    att.add_header("Content-Disposition", "attachment", filename="Q4_Sales_Report.xlsx")
    msg.attach(att)

# --- Step 3: Send via Gmail ---
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")

subprocess.run([
    "gws", "gmail", "messages", "send",
    "--json", f'{{"raw": "{raw}"}}',
], check=True)

print("Report generated and emailed successfully.")
```
