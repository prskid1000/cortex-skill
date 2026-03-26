# Doc Forge — Document Creation Recipes

> Create Excel, Word, PowerPoint, and PDF documents with Python. Style them, add charts, upload to Drive.

**Related:** [workspace.md](workspace.md) | [pipelines.md](pipelines.md) | [mailbox.md](mailbox.md)

---

## Workflow

```
Create locally (Python) → Save to /tmp/ → Upload via gws drive files create --upload
```

## Excel — openpyxl

```python
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, PieChart, LineChart, Reference
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule, DataBarRule

wb = Workbook()
ws = wb.active
ws.title = "Report"

# --- Styled headers ---
headers = ["Name", "Status", "Value", "Date"]
hdr_font = Font(bold=True, color="FFFFFF", size=12)
hdr_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
border = Border(*(Side(style='thin') for _ in range(4)))

for col, h in enumerate(headers, 1):
    c = ws.cell(row=1, column=col, value=h)
    c.font, c.fill, c.alignment, c.border = hdr_font, hdr_fill, Alignment(horizontal='center'), border

# --- Data ---
data = [["Item A", "Done", 1200, "2026-03-25"], ["Item B", "Pending", 800, "2026-03-26"]]
for ri, row in enumerate(data, 2):
    for ci, val in enumerate(row, 1):
        c = ws.cell(row=ri, column=ci, value=val)
        c.border = border

# --- Column widths, freeze, filter ---
for col in range(1, len(headers) + 1):
    ws.column_dimensions[get_column_letter(col)].width = 18
ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(data)+1}"

# --- Charts ---
vals = Reference(ws, min_col=3, min_row=1, max_row=len(data)+1)
cats = Reference(ws, min_col=1, min_row=2, max_row=len(data)+1)

for ChartType, pos in [(BarChart, "F2"), (PieChart, "F18"), (LineChart, "P2")]:
    chart = ChartType()
    chart.add_data(vals, titles_from_data=True)
    chart.set_categories(cats)
    ws.add_chart(chart, pos)

# --- Conditional formatting ---
ws.conditional_formatting.add(f"B2:B{len(data)+1}",
    CellIsRule(operator='equal', formula=['"Done"'], fill=PatternFill(bgColor="C6EFCE")))
ws.conditional_formatting.add(f"C2:C{len(data)+1}",
    DataBarRule(start_type='min', end_type='max', color="4472C4"))

# --- Number format, hyperlink, merged cells ---
ws['C2'].number_format = '#,##0.00'
ws['D2'].number_format = 'YYYY-MM-DD'
ws['A2'].hyperlink = "https://example.com"

# --- Multiple sheets, formulas ---
ws2 = wb.create_sheet("Summary")
ws2["A1"], ws2["B1"] = "Total", f"=SUM(Report!C2:C{len(data)+1})"
ws2.merge_cells('A3:C3')

# --- Print setup ---
ws.print_title_rows = '1:1'
ws.page_setup.orientation = 'landscape'

wb.save('/tmp/report.xlsx')
```

### Reading Excel

```python
wb = load_workbook('/tmp/report.xlsx', data_only=True)
for row in wb.active.iter_rows(min_row=2, values_only=True):
    print(row)
```

## Word — python-docx

```python
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document()

# --- Default font ---
doc.styles['Normal'].font.name = 'Calibri'
doc.styles['Normal'].font.size = Pt(11)

# --- Title + subtitle ---
doc.add_heading('Report Title', level=0).alignment = WD_ALIGN_PARAGRAPH.CENTER
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('Generated: 2026-03-25')
run.font.size, run.font.color.rgb = Pt(10), RGBColor(128, 128, 128)

# --- Sections ---
doc.add_heading('Section 1: Overview', level=1)
doc.add_paragraph('Body text here.')

# --- Lists ---
doc.add_paragraph('Bullet point', style='List Bullet')
doc.add_paragraph('Step one', style='List Number')

# --- Inline formatting ---
p = doc.add_paragraph()
p.add_run('Bold').bold = True
p.add_run(' / ')
p.add_run('Italic').italic = True

# --- Table ---
table = doc.add_table(rows=3, cols=3, style='Table Grid')
table.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, h in enumerate(['Col A', 'Col B', 'Col C']):
    cell = table.rows[0].cells[i]
    cell.text = h
    cell.paragraphs[0].runs[0].font.bold = True

# --- Image ---
# doc.add_picture('/path/to/image.png', width=Inches(4))

# --- Page break + margins ---
doc.add_page_break()
section = doc.sections[0]
section.top_margin = section.bottom_margin = Cm(2)
section.left_margin = section.right_margin = Cm(2.5)

# --- Header / footer ---
section.header.paragraphs[0].text = "Company — Confidential"

doc.save('/tmp/report.docx')
```

## PowerPoint — python-pptx

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)  # 16:9

# --- Title slide ---
s = prs.slides.add_slide(prs.slide_layouts[0])
s.shapes.title.text = "Presentation Title"
s.placeholders[1].text = "Subtitle — Date"

# --- Bullet slide ---
s = prs.slides.add_slide(prs.slide_layouts[1])
s.shapes.title.text = "Key Points"
tf = s.placeholders[1].text_frame
tf.text = "First point"
p = tf.add_paragraph(); p.text = "Sub-point"; p.level = 1

# --- Custom text box ---
s = prs.slides.add_slide(prs.slide_layouts[6])
tx = s.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
tx.text_frame.text = "Custom text"
tx.text_frame.paragraphs[0].font.size = Pt(24)

# --- Table ---
shape = s.shapes.add_table(4, 3, Inches(1), Inches(3), Inches(8), Inches(3))
for i, h in enumerate(["Metric", "Q1", "Q2"]):
    shape.table.cell(0, i).text = h

# --- Chart slide ---
s = prs.slides.add_slide(prs.slide_layouts[6])
cd = CategoryChartData()
cd.categories = ['Jan', 'Feb', 'Mar']
cd.add_series('Revenue', (100, 150, 200))
cd.add_series('Cost', (80, 120, 160))
s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED,
    Inches(1), Inches(1), Inches(10), Inches(5.5), cd)

# --- Speaker notes ---
s.notes_slide.notes_text_frame.text = "Notes here"

prs.save('/tmp/presentation.pptx')
```

### PowerPoint — status deck from JSON (simplified)

**Input JSON**

```json
{
  "title": "Weekly Status Report",
  "subtitle": "Week 13 — March 2026",
  "author": "Team Name",
  "kpis": [
    {"name": "Revenue", "value": "$150K", "change": "+12%", "status": "green"},
    {"name": "Open Bugs", "value": "23", "change": "+5", "status": "red"}
  ],
  "tasks": {
    "done": ["Implemented auth flow"],
    "in_progress": ["API v2 migration"],
    "blocked": ["Cloud migration — waiting on vendor"]
  },
  "next_steps": ["Complete API v2", "Start load testing"]
}
```

**Generate deck**

```python
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

STATUS = {
    "green": RGBColor(0x28, 0xA7, 0x45),
    "amber": RGBColor(0xFF, 0xA5, 0x00),
    "red": RGBColor(0xDC, 0x35, 0x45),
}

def _bullets(tf, items):
    tf.clear()
    tf.text = items[0] if items else ""
    for it in (items or [])[1:]:
        p = tf.add_paragraph()
        p.text = it

def status_deck(data: dict, out_pptx: str):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(10), Inches(5.625)  # 16:9-ish

    # Title
    s = prs.slides.add_slide(prs.slide_layouts[0])
    s.shapes.title.text = data["title"]
    if len(s.placeholders) > 1:
        s.placeholders[1].text = f"{data.get('subtitle','')}\n{data.get('author','')}".strip()

    # KPIs
    kpis = data.get("kpis") or []
    if kpis:
        s = prs.slides.add_slide(prs.slide_layouts[5])  # blank
        s.shapes.title.text = "Key Metrics"
        cols = max(1, len(kpis))
        col_w = Inches(9) / cols
        left0 = Inches(0.5)
        for i, k in enumerate(kpis):
            left = left0 + col_w * i
            tb = s.shapes.add_textbox(left, Inches(2.0), col_w, Inches(0.8))
            p = tb.text_frame.paragraphs[0]
            p.text = str(k.get("value", ""))
            p.font.size = Pt(32)
            p.font.bold = True
            p.font.color.rgb = STATUS.get(k.get("status", "green"), RGBColor(0, 0, 0))
            p.alignment = PP_ALIGN.CENTER

            tb2 = s.shapes.add_textbox(left, Inches(2.85), col_w, Inches(0.4))
            p2 = tb2.text_frame.paragraphs[0]
            p2.text = str(k.get("change", ""))
            p2.font.size = Pt(14)
            p2.alignment = PP_ALIGN.CENTER

            tb3 = s.shapes.add_textbox(left, Inches(3.25), col_w, Inches(0.4))
            p3 = tb3.text_frame.paragraphs[0]
            p3.text = str(k.get("name", ""))
            p3.font.size = Pt(12)
            p3.font.color.rgb = RGBColor(0x70, 0x70, 0x70)
            p3.alignment = PP_ALIGN.CENTER

    # Tasks
    tasks = data.get("tasks") or {}
    if tasks:
        s = prs.slides.add_slide(prs.slide_layouts[5])
        s.shapes.title.text = "Task Progress"
        sections = [("Done", "done"), ("In Progress", "in_progress"), ("Blocked", "blocked")]
        for idx, (label, key) in enumerate(sections):
            left = Inches(0.7 + idx * 3.1)
            hdr = s.shapes.add_textbox(left, Inches(1.8), Inches(2.8), Inches(0.4))
            hp = hdr.text_frame.paragraphs[0]
            items = tasks.get(key) or []
            hp.text = f"{label} ({len(items)})"
            hp.font.bold = True
            box = s.shapes.add_textbox(left, Inches(2.3), Inches(2.8), Inches(3.0))
            _bullets(box.text_frame, items[:7])

    # Next steps
    steps = data.get("next_steps") or []
    if steps:
        s = prs.slides.add_slide(prs.slide_layouts[5])
        s.shapes.title.text = "Next Steps"
        box = s.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(8.8), Inches(3.6))
        tf = box.text_frame
        tf.clear()
        for i, step in enumerate(steps, 1):
            p = tf.paragraphs[0] if i == 1 else tf.add_paragraph()
            p.text = f"{i}. {step}"
            p.font.size = Pt(20)

    prs.save(out_pptx)

data = json.loads(Path("report_data.json").read_text(encoding="utf-8"))
status_deck(data, "/tmp/status-deck.pptx")
```

## PDF — reportlab (generate from scratch)

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors

doc = SimpleDocTemplate("/tmp/report.pdf", pagesize=A4,
    topMargin=2*cm, bottomMargin=2*cm, leftMargin=2.5*cm, rightMargin=2.5*cm)
styles = getSampleStyleSheet()
story = []

title = ParagraphStyle('T', parent=styles['Title'], fontSize=28, textColor=HexColor('#1a237e'))
heading = ParagraphStyle('H', parent=styles['Heading1'], fontSize=16, textColor=HexColor('#283593'))
body = ParagraphStyle('B', parent=styles['Normal'], fontSize=11, leading=16)

story += [Paragraph("Report Title", title), Spacer(1, 30)]
story += [Paragraph("1. Overview", heading), Paragraph("Content...", body)]

data = [['Name', 'Status', 'Value'], ['A', 'Done', '$1,200'], ['B', 'Pending', '$800']]
t = Table(data, colWidths=[200, 120, 100])
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), HexColor('#1a237e')),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
]))
story += [t, PageBreak()]
doc.build(story)
```

## PDF — pymupdf (read, edit, screenshot, merge)

```python
import fitz

# Read text
doc = fitz.open("input.pdf")
for page in doc: print(page.get_text())

# Extract tables → pandas
for page in doc:
    for tab in page.find_tables(): df = tab.to_pandas()

# Merge PDFs
result = fitz.open()
for p in ["a.pdf", "b.pdf"]: result.insert_pdf(fitz.open(p))
result.save("merged.pdf")

# Watermark
for page in doc:
    page.insert_text((100, 100), "CONFIDENTIAL", fontsize=40, color=(0.8, 0, 0), rotate=45)

# Page → image (screenshot)
pix = doc[0].get_pixmap(matrix=fitz.Matrix(3, 3))
pix.save("screenshot.png")

# Extract images
for page in doc:
    for img in page.get_images():
        fitz.Pixmap(doc, img[0]).save(f"img_{img[0]}.png")
```

### PDF — merge / split with PyPDF2 (simplified)

```python
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter, PdfMerger

def merge_pdfs(inputs: list[str], out_pdf: str):
    merger = PdfMerger()
    for p in inputs:
        p = str(p)
        merger.append(p, outline_item=Path(p).stem)
    merger.write(out_pdf)
    merger.close()

def split_pdf(input_pdf: str, pages: str, out_dir: str):
    """
    pages examples:
      "1-5,10-15" (1-indexed, inclusive)
      "3" (single page)
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(input_pdf)
    total = len(reader.pages)
    for part in pages.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            start, end = int(a) - 1, int(b)          # end is inclusive in input
        else:
            start, end = int(part) - 1, int(part)
        start = max(0, start)
        end = min(total, end)
        w = PdfWriter()
        for i in range(start, end):
            w.add_page(reader.pages[i])
        out_path = out / f"pages_{start+1}-{end}.pdf"
        with out_path.open("wb") as f:
            w.write(f)

# merge_pdfs(["a.pdf", "b.pdf"], "/tmp/merged.pdf")
# split_pdf("input.pdf", "1-5,10-15", "/tmp/split_output")
```

## PDF — pdfplumber (extract tables/text)

```python
import pdfplumber
with pdfplumber.open("invoice.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        tables = page.extract_tables()
        # Crop region
        cropped = page.within_bbox((0, 0, page.width/2, page.height/2))
```

## Conversions Not Covered Above

```bash
# Word → PDF
pandoc input.docx -o output.pdf

# Markdown → Word / PDF / PPT
pandoc input.md -o output.docx
pandoc input.md -o output.pdf --toc
pandoc input.md -o output.pptx
```

See [media-kit.md](media-kit.md) for Pandoc and [pipelines.md](pipelines.md) for full conversion flows.
