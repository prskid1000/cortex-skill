# Database Query & Export Examples

Working code blocks for MySQL queries via MCP and export to various formats.

All queries use the MCP tool `mcp__mcp_server_mysql__mysql_query`. In Python scripts, use `subprocess` to call `gws` or direct library exports.

---

## Database Exploration

### Show Databases and Tables

```
-- List all databases
SHOW DATABASES;

-- Switch to a database and list tables
USE my_database;
SHOW TABLES;

-- List tables matching a pattern
SHOW TABLES LIKE '%order%';
```

### Describe Table Schema

```
-- Column names, types, keys
DESCRIBE orders;

-- Full column details
SHOW FULL COLUMNS FROM orders;

-- Show CREATE TABLE statement (complete schema)
SHOW CREATE TABLE orders;

-- Show indexes
SHOW INDEX FROM orders;
```

---

## Query Patterns

### Basic SELECT with WHERE, ORDER BY, LIMIT

```sql
-- Simple filtered query
SELECT id, customer_name, order_date, total_amount
FROM orders
WHERE status = 'completed'
  AND order_date >= '2025-01-01'
ORDER BY order_date DESC
LIMIT 100;

-- Multiple conditions with IN
SELECT id, product_name, category, price
FROM products
WHERE category IN ('Electronics', 'Books', 'Clothing')
  AND price BETWEEN 10 AND 500
  AND is_active = 1
ORDER BY price ASC;

-- Pattern matching
SELECT id, name, email
FROM customers
WHERE name LIKE '%Smith%'
   OR email LIKE '%@company.com'
ORDER BY name;
```

### JOIN Query (INNER, LEFT)

```sql
-- INNER JOIN: orders with customer details
SELECT
    o.id AS order_id,
    c.name AS customer_name,
    c.email,
    o.order_date,
    o.total_amount,
    o.status
FROM orders o
INNER JOIN customers c ON o.customer_id = c.id
WHERE o.order_date >= '2025-01-01'
ORDER BY o.order_date DESC;

-- LEFT JOIN: all customers with their order count (including those with 0 orders)
SELECT
    c.id,
    c.name,
    c.email,
    COUNT(o.id) AS order_count,
    COALESCE(SUM(o.total_amount), 0) AS total_spent
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name, c.email
ORDER BY total_spent DESC;

-- Multi-table JOIN
SELECT
    o.id AS order_id,
    c.name AS customer,
    p.product_name,
    oi.quantity,
    oi.unit_price,
    (oi.quantity * oi.unit_price) AS line_total
FROM orders o
INNER JOIN customers c ON o.customer_id = c.id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
WHERE o.order_date BETWEEN '2025-01-01' AND '2025-03-31'
ORDER BY o.id, p.product_name;
```

### Aggregation (GROUP BY, COUNT, SUM, AVG)

```sql
-- Monthly revenue summary
SELECT
    DATE_FORMAT(order_date, '%Y-%m') AS month,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS avg_order_value,
    MIN(total_amount) AS min_order,
    MAX(total_amount) AS max_order
FROM orders
WHERE status = 'completed'
  AND order_date >= '2025-01-01'
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY month;

-- Top 10 customers by revenue
SELECT
    c.name,
    c.email,
    COUNT(o.id) AS orders,
    SUM(o.total_amount) AS total_revenue
FROM customers c
INNER JOIN orders o ON c.id = o.customer_id
WHERE o.status = 'completed'
GROUP BY c.id, c.name, c.email
ORDER BY total_revenue DESC
LIMIT 10;

-- Category breakdown
SELECT
    p.category,
    COUNT(DISTINCT p.id) AS product_count,
    SUM(oi.quantity) AS units_sold,
    SUM(oi.quantity * oi.unit_price) AS revenue
FROM products p
INNER JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.category
HAVING revenue > 1000
ORDER BY revenue DESC;
```

### Date Range Queries

```sql
-- Last 30 days
SELECT * FROM orders
WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);

-- This month
SELECT * FROM orders
WHERE order_date >= DATE_FORMAT(CURDATE(), '%Y-%m-01');

-- Last quarter
SELECT * FROM orders
WHERE QUARTER(order_date) = QUARTER(DATE_SUB(CURDATE(), INTERVAL 1 QUARTER))
  AND YEAR(order_date) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 QUARTER));

-- Year-over-year comparison
SELECT
    DATE_FORMAT(order_date, '%Y') AS year,
    DATE_FORMAT(order_date, '%m') AS month,
    COUNT(*) AS orders,
    SUM(total_amount) AS revenue
FROM orders
WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
GROUP BY year, month
ORDER BY month, year;
```

### Full-Text Search Patterns

```sql
-- LIKE-based search (works on any column, slower)
SELECT * FROM products
WHERE product_name LIKE '%wireless%'
   OR description LIKE '%bluetooth%';

-- FULLTEXT index search (requires FULLTEXT index)
SELECT *, MATCH(product_name, description) AGAINST('wireless bluetooth' IN NATURAL LANGUAGE MODE) AS relevance
FROM products
WHERE MATCH(product_name, description) AGAINST('wireless bluetooth' IN NATURAL LANGUAGE MODE)
ORDER BY relevance DESC;

-- Boolean mode
SELECT * FROM products
WHERE MATCH(product_name, description) AGAINST('+wireless -wired' IN BOOLEAN MODE);
```

### Complex Query with CTE

```sql
-- Running total and ranking with CTEs
WITH monthly_sales AS (
    SELECT
        DATE_FORMAT(order_date, '%Y-%m') AS month,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
      AND order_date >= '2025-01-01'
    GROUP BY DATE_FORMAT(order_date, '%Y-%m')
),
running_totals AS (
    SELECT
        month,
        revenue,
        SUM(revenue) OVER (ORDER BY month) AS cumulative_revenue,
        LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue
    FROM monthly_sales
)
SELECT
    month,
    revenue,
    cumulative_revenue,
    prev_month_revenue,
    CASE
        WHEN prev_month_revenue IS NOT NULL
        THEN ROUND((revenue - prev_month_revenue) / prev_month_revenue * 100, 1)
        ELSE NULL
    END AS growth_pct
FROM running_totals
ORDER BY month;
```

---

## Export to Various Formats

### Export to Excel (Styled with Headers)

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
import json, subprocess

# Step 1: Run query via MCP (returns JSON)
# In Claude Code, use mcp__mcp_server_mysql__mysql_query tool directly.
# In a script, you would have the data as a list of dicts:
data = [
    {"id": 1, "customer": "Acme Corp", "revenue": 125000, "orders": 45},
    {"id": 2, "customer": "Globex", "revenue": 98000, "orders": 32},
    {"id": 3, "customer": "Initech", "revenue": 87500, "orders": 28},
]

# Step 2: Build styled Excel
wb = Workbook()
ws = wb.active
ws.title = "Customer Report"

header_font = Font(bold=True, color="FFFFFF", size=11)
header_fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
thin_border = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"), bottom=Side(style="thin"),
)
money_fmt = '#,##0'

headers = list(data[0].keys())
for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h.replace("_", " ").title())
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal="center")
    cell.border = thin_border

for row_idx, row_data in enumerate(data, 2):
    for col_idx, key in enumerate(headers, 1):
        cell = ws.cell(row=row_idx, column=col_idx, value=row_data[key])
        cell.border = thin_border
        if key == "revenue":
            cell.number_format = money_fmt

# Auto-width columns
for col_idx, h in enumerate(headers, 1):
    max_len = max(len(str(h)), *(len(str(row[h])) for row in data))
    ws.column_dimensions[chr(64 + col_idx)].width = max_len + 4

# Freeze top row
ws.freeze_panes = "A2"

# Auto-filter
ws.auto_filter.ref = f"A1:{chr(64 + len(headers))}{len(data) + 1}"

wb.save("/tmp/customer_report.xlsx")
print("Saved /tmp/customer_report.xlsx")
```

### Export to CSV

```python
import csv

data = [
    {"id": 1, "customer": "Acme Corp", "revenue": 125000},
    {"id": 2, "customer": "Globex", "revenue": 98000},
]

with open("/tmp/export.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

print("Saved /tmp/export.csv")
```

### Export to Google Sheets (via gws)

```python
import subprocess, csv

# Step 1: Export data to CSV
data = [
    ["Customer", "Revenue", "Orders"],
    ["Acme Corp", 125000, 45],
    ["Globex", 98000, 32],
]

csv_path = "/tmp/export_for_sheets.csv"
with open(csv_path, "w", newline="") as f:
    csv.writer(f).writerows(data)

# Step 2: Create Google Sheet from CSV
result = subprocess.run([
    "gws", "drive", "files", "create",
    "--json", '{"name": "Customer Report", "mimeType": "application/vnd.google-apps.spreadsheet"}',
    "--upload", csv_path,
    "--upload-content-type", "text/csv",
], capture_output=True, text=True, check=True)

print(result.stdout)
```

### Export to JSON

```python
import json

data = [
    {"id": 1, "customer": "Acme Corp", "revenue": 125000},
    {"id": 2, "customer": "Globex", "revenue": 98000},
]

with open("/tmp/export.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False, default=str)

print("Saved /tmp/export.json")
```

### Export to PDF Report (reportlab)

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

data = [
    ["Customer", "Revenue", "Orders", "Avg Order"],
    ["Acme Corp", "$125,000", "45", "$2,778"],
    ["Globex", "$98,000", "32", "$3,063"],
    ["Initech", "$87,500", "28", "$3,125"],
]

doc = SimpleDocTemplate("/tmp/report.pdf", pagesize=A4)
styles = getSampleStyleSheet()
elements = []

# Title
elements.append(Paragraph("Customer Revenue Report", styles["Title"]))
elements.append(Spacer(1, 0.3 * inch))
elements.append(Paragraph("Generated from database export", styles["Normal"]))
elements.append(Spacer(1, 0.3 * inch))

# Table
table = Table(data, colWidths=[2 * inch, 1.5 * inch, 1 * inch, 1.5 * inch])
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 11),
    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ECF0F1")]),
    ("TOPPADDING", (0, 0), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
]))
elements.append(table)

doc.build(elements)
print("Saved /tmp/report.pdf")
```
