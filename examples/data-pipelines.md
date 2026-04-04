# Data Pipeline Examples

End-to-end working code blocks for multi-step data transformations.

---

## CSV to Styled Excel to Google Sheets

```python
import csv, subprocess
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# --- Step 1: Read CSV ---
csv_path = "/tmp/sales_data.csv"
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    headers = reader.fieldnames

# --- Step 2: Build styled Excel ---
wb = Workbook()
ws = wb.active
ws.title = "Sales Data"

hdr_font = Font(bold=True, color="FFFFFF", size=11)
hdr_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
thin = Border(
    left=Side("thin"), right=Side("thin"),
    top=Side("thin"), bottom=Side("thin"),
)

for col_idx, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col_idx, value=h)
    cell.font = hdr_font
    cell.fill = hdr_fill
    cell.alignment = Alignment(horizontal="center")
    cell.border = thin

for row_idx, row in enumerate(rows, 2):
    for col_idx, h in enumerate(headers, 1):
        val = row[h]
        # Attempt numeric conversion
        try:
            val = float(val)
            if val == int(val):
                val = int(val)
        except (ValueError, TypeError):
            pass
        cell = ws.cell(row=row_idx, column=col_idx, value=val)
        cell.border = thin

# Auto-width
for col_idx, h in enumerate(headers, 1):
    max_len = max(len(str(h)), *(len(str(r[h])) for r in rows)) if rows else len(str(h))
    ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 4, 40)

ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(rows) + 1}"

xlsx_path = "/tmp/sales_data.xlsx"
wb.save(xlsx_path)

# --- Step 3: Upload to Google Sheets ---
result = subprocess.run([
    "gws", "drive", "files", "create",
    "--json", '{"name": "Sales Data Import", "mimeType": "application/vnd.google-apps.spreadsheet"}',
    "--upload", xlsx_path,
    "--upload-content-type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
], capture_output=True, text=True, check=True)
print(result.stdout)

# --- Step 4 (optional): Share with anyone who has the link ---
# Extract file ID from result, then:
# subprocess.run([
#     "gws", "drive", "permissions", "create", "<FILE_ID>",
#     "--json", '{"role": "reader", "type": "anyone"}',
# ], check=True)
```

---

## PDF to Extract Tables to Excel

```python
import pdfplumber
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side

pdf_path = "/tmp/financial_report.pdf"
wb = Workbook()

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for table_idx, table in enumerate(tables):
            if not table:
                continue

            sheet_name = f"Page{page_num + 1}_T{table_idx + 1}"[:31]
            ws = wb.create_sheet(title=sheet_name)

            hdr_fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
            hdr_font = Font(bold=True, color="FFFFFF")
            thin = Border(
                left=Side("thin"), right=Side("thin"),
                top=Side("thin"), bottom=Side("thin"),
            )

            for row_idx, row in enumerate(table, 1):
                for col_idx, val in enumerate(row, 1):
                    cell = ws.cell(row=row_idx, column=col_idx, value=val)
                    cell.border = thin
                    if row_idx == 1:
                        cell.font = hdr_font
                        cell.fill = hdr_fill

# Remove default empty sheet
if "Sheet" in wb.sheetnames:
    del wb["Sheet"]

xlsx_path = "/tmp/extracted_tables.xlsx"
wb.save(xlsx_path)
print(f"Extracted tables saved to {xlsx_path}")
```

---

## Google Sheet Download, Modify, Upload Back

```python
import subprocess, json
from openpyxl import load_workbook

SHEET_FILE_ID = "<GOOGLE_SHEET_FILE_ID>"

# --- Step 1: Export Google Sheet as XLSX ---
subprocess.run([
    "gws", "drive", "files", "export", SHEET_FILE_ID,
    "--params", '{"mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}',
    "--output", "/tmp/downloaded.xlsx",
], check=True)

# --- Step 2: Modify locally ---
wb = load_workbook("/tmp/downloaded.xlsx")
ws = wb.active

# Example: add a "Status" column
status_col = ws.max_column + 1
ws.cell(row=1, column=status_col, value="Status")
for row in range(2, ws.max_row + 1):
    revenue = ws.cell(row=row, column=3).value  # assume column C is revenue
    try:
        val = float(revenue)
        ws.cell(row=row, column=status_col, value="High" if val > 100000 else "Normal")
    except (TypeError, ValueError):
        ws.cell(row=row, column=status_col, value="N/A")

wb.save("/tmp/modified.xlsx")

# --- Step 3: Upload back (replace content) ---
subprocess.run([
    "gws", "drive", "files", "update", SHEET_FILE_ID,
    "--upload", "/tmp/modified.xlsx",
    "--upload-content-type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
], check=True)

print("Sheet updated successfully.")
```

---

## Database to Excel Report (Styled)

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter

# Data from database query (via MCP tool or script)
data = [
    {"month": "2025-01", "revenue": 125000, "orders": 450, "customers": 280},
    {"month": "2025-02", "revenue": 132000, "orders": 478, "customers": 295},
    {"month": "2025-03", "revenue": 141000, "orders": 512, "customers": 310},
    {"month": "2025-04", "revenue": 128000, "orders": 465, "customers": 288},
    {"month": "2025-05", "revenue": 155000, "orders": 540, "customers": 325},
    {"month": "2025-06", "revenue": 163000, "orders": 568, "customers": 340},
]

wb = Workbook()
ws = wb.active
ws.title = "Monthly Report"

# Styles
hdr_font = Font(bold=True, color="FFFFFF", size=11)
hdr_fill = PatternFill(start_color="1A5276", end_color="1A5276", fill_type="solid")
thin = Border(
    left=Side("thin"), right=Side("thin"),
    top=Side("thin"), bottom=Side("thin"),
)
alt_fill = PatternFill(start_color="EBF5FB", end_color="EBF5FB", fill_type="solid")

# Headers
headers = ["Month", "Revenue", "Orders", "Customers", "Avg Order Value"]
for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h)
    cell.font = hdr_font
    cell.fill = hdr_fill
    cell.alignment = Alignment(horizontal="center")
    cell.border = thin

# Data rows
for i, row in enumerate(data, 2):
    ws.cell(row=i, column=1, value=row["month"]).border = thin
    ws.cell(row=i, column=2, value=row["revenue"]).border = thin
    ws.cell(row=i, column=2).number_format = '#,##0'
    ws.cell(row=i, column=3, value=row["orders"]).border = thin
    ws.cell(row=i, column=4, value=row["customers"]).border = thin
    ws.cell(row=i, column=5).value = f"=B{i}/C{i}"
    ws.cell(row=i, column=5).number_format = '#,##0.00'
    ws.cell(row=i, column=5).border = thin
    if i % 2 == 0:
        for col in range(1, 6):
            ws.cell(row=i, column=col).fill = alt_fill

# Totals row
total_row = len(data) + 2
ws.cell(row=total_row, column=1, value="TOTAL").font = Font(bold=True)
ws.cell(row=total_row, column=2).value = f"=SUM(B2:B{total_row - 1})"
ws.cell(row=total_row, column=2).number_format = '#,##0'
ws.cell(row=total_row, column=2).font = Font(bold=True)
ws.cell(row=total_row, column=3).value = f"=SUM(C2:C{total_row - 1})"
ws.cell(row=total_row, column=3).font = Font(bold=True)

# Column widths
for col in range(1, 6):
    ws.column_dimensions[get_column_letter(col)].width = 18

# Bar chart
chart = BarChart()
chart.title = "Monthly Revenue"
chart.y_axis.title = "Revenue"
chart.x_axis.title = "Month"
chart.style = 10
chart.width = 20
chart.height = 12

chart_data = Reference(ws, min_col=2, min_row=1, max_row=len(data) + 1)
categories = Reference(ws, min_col=1, min_row=2, max_row=len(data) + 1)
chart.add_data(chart_data, titles_from_data=True)
chart.set_categories(categories)
chart.shape = 4

ws.add_chart(chart, "A" + str(total_row + 2))

ws.freeze_panes = "A2"
wb.save("/tmp/monthly_report.xlsx")
print("Saved /tmp/monthly_report.xlsx")
```

---

## Database to Google Sheets (Direct)

```python
import subprocess, csv

# Data from database query
data = [
    ["Month", "Revenue", "Orders"],
    ["2025-01", 125000, 450],
    ["2025-02", 132000, 478],
    ["2025-03", 141000, 512],
]

csv_path = "/tmp/db_to_sheets.csv"
with open(csv_path, "w", newline="") as f:
    csv.writer(f).writerows(data)

result = subprocess.run([
    "gws", "drive", "files", "create",
    "--json", '{"name": "DB Export - Revenue", "mimeType": "application/vnd.google-apps.spreadsheet"}',
    "--upload", csv_path,
    "--upload-content-type", "text/csv",
], capture_output=True, text=True, check=True)
print(result.stdout)
```

---

## JSON to Excel

```python
import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# Load JSON (could be from API response, file, etc.)
with open("/tmp/api_response.json", "r") as f:
    records = json.load(f)

# Handle nested JSON: flatten one level
def flatten(obj, prefix=""):
    flat = {}
    for k, v in obj.items():
        key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
        if isinstance(v, dict):
            flat.update(flatten(v, key))
        elif isinstance(v, list):
            flat[key] = json.dumps(v)
        else:
            flat[key] = v
    return flat

flat_records = [flatten(r) for r in records]
all_keys = list(dict.fromkeys(k for r in flat_records for k in r))

wb = Workbook()
ws = wb.active
ws.title = "JSON Data"

hdr_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
hdr_font = Font(bold=True, color="FFFFFF")
thin = Border(left=Side("thin"), right=Side("thin"), top=Side("thin"), bottom=Side("thin"))

for col, key in enumerate(all_keys, 1):
    cell = ws.cell(row=1, column=col, value=key)
    cell.font = hdr_font
    cell.fill = hdr_fill
    cell.border = thin

for row_idx, record in enumerate(flat_records, 2):
    for col_idx, key in enumerate(all_keys, 1):
        cell = ws.cell(row=row_idx, column=col_idx, value=record.get(key))
        cell.border = thin

for col in range(1, len(all_keys) + 1):
    ws.column_dimensions[get_column_letter(col)].width = 20

ws.freeze_panes = "A2"
wb.save("/tmp/json_export.xlsx")
print("Saved /tmp/json_export.xlsx")
```

---

## HTML Table to Excel (BeautifulSoup)

```python
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side

html = open("/tmp/page.html", "r", encoding="utf-8").read()
soup = BeautifulSoup(html, "lxml")

wb = Workbook()

for table_idx, table in enumerate(soup.find_all("table")):
    ws = wb.create_sheet(title=f"Table_{table_idx + 1}"[:31])

    for row_idx, tr in enumerate(table.find_all("tr"), 1):
        cells = tr.find_all(["th", "td"])
        for col_idx, td in enumerate(cells, 1):
            text = td.get_text(strip=True)
            # Try numeric
            try:
                text = float(text.replace(",", "").replace("$", ""))
                if text == int(text):
                    text = int(text)
            except (ValueError, TypeError):
                pass

            cell = ws.cell(row=row_idx, column=col_idx, value=text)
            cell.border = Border(
                left=Side("thin"), right=Side("thin"),
                top=Side("thin"), bottom=Side("thin"),
            )
            if td.name == "th" or row_idx == 1:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")

if "Sheet" in wb.sheetnames:
    del wb["Sheet"]

wb.save("/tmp/html_tables.xlsx")
print("Saved /tmp/html_tables.xlsx")
```

---

## Excel to PDF (reportlab Table)

```python
from openpyxl import load_workbook
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Load Excel
wb = load_workbook("/tmp/data.xlsx")
ws = wb.active

# Extract data
data = []
for row in ws.iter_rows(values_only=True):
    data.append([str(v) if v is not None else "" for v in row])

# Build PDF
doc = SimpleDocTemplate("/tmp/output.pdf", pagesize=landscape(A4))
styles = getSampleStyleSheet()
elements = []

elements.append(Paragraph(ws.title or "Data Export", styles["Title"]))
elements.append(Spacer(1, 0.3 * inch))

# Calculate column widths (distribute evenly)
num_cols = len(data[0]) if data else 1
available_width = landscape(A4)[0] - 2 * inch
col_width = available_width / num_cols

table = Table(data, colWidths=[col_width] * num_cols)
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F3F4")]),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
elements.append(table)

doc.build(elements)
print("Saved /tmp/output.pdf")
```

---

## Markdown to PDF (pandoc)

```bash
# Basic conversion
pandoc /tmp/document.md -o /tmp/document.pdf

# With custom margins and font size
pandoc /tmp/document.md -o /tmp/document.pdf \
  -V geometry:margin=1in -V fontsize=12pt

# With table of contents
pandoc /tmp/document.md -o /tmp/document.pdf --toc --toc-depth=3

# With syntax highlighting theme
pandoc /tmp/document.md -o /tmp/document.pdf --highlight-style=tango

# From multiple markdown files
pandoc /tmp/chapter1.md /tmp/chapter2.md /tmp/chapter3.md -o /tmp/book.pdf --toc
```

---

## Full Pipeline: DB Query to Process to Excel + PDF to Upload Drive to Email

```python
import subprocess, base64, csv, json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ============================================================
# Step 1: Query database (via MCP or simulated data)
# ============================================================
# In Claude Code, use: mcp__mcp_server_mysql__mysql_query with your SQL
# Here we use sample data as if returned from the query:
query_results = [
    {"region": "North", "q1": 125000, "q2": 132000, "q3": 141000, "q4": 155000},
    {"region": "South", "q1": 98000, "q2": 105000, "q3": 112000, "q4": 120000},
    {"region": "East", "q1": 87000, "q2": 91000, "q3": 95000, "q4": 101000},
    {"region": "West", "q1": 76000, "q2": 80000, "q3": 83000, "q4": 89000},
]

# ============================================================
# Step 2: Process data (add computed fields)
# ============================================================
for row in query_results:
    row["total"] = row["q1"] + row["q2"] + row["q3"] + row["q4"]
    row["growth_pct"] = round((row["q4"] - row["q1"]) / row["q1"] * 100, 1)

# ============================================================
# Step 3: Generate Excel report
# ============================================================
wb = Workbook()
ws = wb.active
ws.title = "Regional Sales"

hdr_font = Font(bold=True, color="FFFFFF", size=11)
hdr_fill = PatternFill(start_color="1A5276", end_color="1A5276", fill_type="solid")
thin = Border(left=Side("thin"), right=Side("thin"), top=Side("thin"), bottom=Side("thin"))

headers = ["Region", "Q1", "Q2", "Q3", "Q4", "Total", "Growth %"]
for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h)
    cell.font = hdr_font
    cell.fill = hdr_fill
    cell.alignment = Alignment(horizontal="center")
    cell.border = thin

for i, row in enumerate(query_results, 2):
    ws.cell(row=i, column=1, value=row["region"]).border = thin
    for j, q in enumerate(["q1", "q2", "q3", "q4", "total"], 2):
        cell = ws.cell(row=i, column=j, value=row[q])
        cell.number_format = '#,##0'
        cell.border = thin
    cell = ws.cell(row=i, column=7, value=row["growth_pct"])
    cell.number_format = '0.0"%"'
    cell.border = thin

for col in range(1, 8):
    ws.column_dimensions[get_column_letter(col)].width = 15

# Add bar chart
chart = BarChart()
chart.title = "Quarterly Revenue by Region"
chart.y_axis.title = "Revenue"
chart.style = 10
chart.width = 22
chart.height = 12
data_ref = Reference(ws, min_col=2, max_col=5, min_row=1, max_row=len(query_results) + 1)
cats = Reference(ws, min_col=1, min_row=2, max_row=len(query_results) + 1)
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats)
ws.add_chart(chart, "A" + str(len(query_results) + 3))

ws.freeze_panes = "A2"
xlsx_path = "/tmp/regional_sales.xlsx"
wb.save(xlsx_path)
print(f"Excel saved: {xlsx_path}")

# ============================================================
# Step 4: Generate PDF summary
# ============================================================
doc = SimpleDocTemplate("/tmp/regional_sales.pdf", pagesize=A4)
styles = getSampleStyleSheet()
elements = []

elements.append(Paragraph("Regional Sales Report", styles["Title"]))
elements.append(Spacer(1, 0.2 * inch))
elements.append(Paragraph("Quarterly breakdown with year-over-year growth analysis.", styles["Normal"]))
elements.append(Spacer(1, 0.3 * inch))

table_data = [headers]
for row in query_results:
    table_data.append([
        row["region"],
        f"${row['q1']:,}", f"${row['q2']:,}",
        f"${row['q3']:,}", f"${row['q4']:,}",
        f"${row['total']:,}", f"{row['growth_pct']}%",
    ])

t = Table(table_data, colWidths=[1.2*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch, 1.0*inch, 0.9*inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A5276")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EBF5FB")]),
    ("TOPPADDING", (0, 0), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
]))
elements.append(t)

grand_total = sum(r["total"] for r in query_results)
elements.append(Spacer(1, 0.3 * inch))
elements.append(Paragraph(f"<b>Grand Total: ${grand_total:,}</b>", styles["Normal"]))

pdf_path = "/tmp/regional_sales.pdf"
doc.build(elements)
print(f"PDF saved: {pdf_path}")

# ============================================================
# Step 5: Upload both files to Google Drive
# ============================================================
for path, name, mime in [
    (xlsx_path, "Regional Sales Report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    (pdf_path, "Regional Sales Report.pdf", "application/pdf"),
]:
    result = subprocess.run([
        "gws", "drive", "files", "create",
        "--json", json.dumps({"name": name}),
        "--upload", path,
        "--upload-content-type", mime,
    ], capture_output=True, text=True, check=True)
    print(f"Uploaded {name}: {result.stdout.strip()}")

# ============================================================
# Step 6: Email with both attachments
# ============================================================
msg = MIMEMultipart()
msg["Subject"] = "Regional Sales Report - Q1-Q4"
msg["From"] = "me@gmail.com"
msg["To"] = "manager@company.com"
msg["Cc"] = "team@company.com"

msg.attach(MIMEText(f"""Hi Team,

Attached is the regional sales report covering Q1 through Q4.

Key highlights:
- Grand total revenue: ${grand_total:,}
- North region leads with ${query_results[0]['total']:,}
- All regions showed positive growth

Both Excel (with charts) and PDF summary versions are attached.
Files have also been uploaded to Google Drive.

Best regards""", "plain"))

for path, filename in [
    (xlsx_path, "Regional_Sales_Report.xlsx"),
    (pdf_path, "Regional_Sales_Report.pdf"),
]:
    with open(path, "rb") as f:
        att = MIMEApplication(f.read())
        att.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(att)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
subprocess.run([
    "gws", "gmail", "messages", "send",
    "--json", f'{{"raw": "{raw}"}}',
], check=True)

print("Pipeline complete: Excel + PDF generated, uploaded to Drive, and emailed.")
```
