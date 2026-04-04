# PDF Workflows — Working Examples

Complete, runnable code blocks for PDF generation, editing, extraction, and manipulation.

---

## reportlab — Generate PDFs from Scratch

### Simple PDF (Canvas)

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

output = "/tmp/simple_canvas.pdf"
c = canvas.Canvas(output, pagesize=A4)
w, h = A4

# Title
c.setFont("Helvetica-Bold", 24)
c.setFillColor(HexColor("#1a1a2e"))
c.drawString(2 * cm, h - 3 * cm, "Monthly Status Report")

# Subtitle
c.setFont("Helvetica", 12)
c.setFillColor(HexColor("#555555"))
c.drawString(2 * cm, h - 4 * cm, "Generated on 2026-04-04")

# Horizontal rule
c.setStrokeColor(HexColor("#0066cc"))
c.setLineWidth(2)
c.line(2 * cm, h - 4.5 * cm, w - 2 * cm, h - 4.5 * cm)

# Body text
c.setFont("Helvetica", 11)
c.setFillColor(HexColor("#333333"))
text_y = h - 6 * cm
for line in [
    "1. Project Alpha completed ahead of schedule.",
    "2. Budget utilization at 87% of forecast.",
    "3. Three new team members onboarded this quarter.",
    "4. Client satisfaction score: 4.7 / 5.0.",
]:
    c.drawString(2.5 * cm, text_y, line)
    text_y -= 0.7 * cm

# Filled rectangle
c.setFillColor(HexColor("#e8f4f8"))
c.setStrokeColor(HexColor("#0066cc"))
c.rect(2 * cm, text_y - 2 * cm, 10 * cm, 1.5 * cm, fill=True, stroke=True)
c.setFillColor(HexColor("#0066cc"))
c.setFont("Helvetica-Bold", 11)
c.drawString(2.3 * cm, text_y - 1.4 * cm, "Next review: May 15, 2026")

# --- Page 2 ---
c.showPage()
c.setFont("Helvetica-Bold", 18)
c.drawString(2 * cm, h - 3 * cm, "Appendix A — Detailed Metrics")
c.setFont("Helvetica", 11)
c.drawString(2 * cm, h - 4.5 * cm, "See attached data tables for full breakdown.")

c.save()
print(f"Saved: {output}")
```

### Styled Report (PLATYPUS)

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak,
)

output = "/tmp/styled_report.pdf"
doc = SimpleDocTemplate(output, pagesize=A4,
                        leftMargin=2*cm, rightMargin=2*cm,
                        topMargin=2.5*cm, bottomMargin=2.5*cm)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("CustomTitle", parent=styles["Title"],
                          fontSize=22, textColor=HexColor("#1a1a2e"),
                          spaceAfter=20))
styles.add(ParagraphStyle("SectionHead", parent=styles["Heading2"],
                          fontSize=14, textColor=HexColor("#0066cc"),
                          spaceBefore=16, spaceAfter=8))

story = []

# Title
story.append(Paragraph("Q1 2026 Sales Report", styles["CustomTitle"]))
story.append(Paragraph("Prepared by the Analytics Team", styles["Normal"]))
story.append(Spacer(1, 1 * cm))

# Section
story.append(Paragraph("Revenue by Region", styles["SectionHead"]))
story.append(Paragraph(
    "The following table summarizes revenue across all operating regions "
    "for the first quarter of 2026.", styles["Normal"]))
story.append(Spacer(1, 0.5 * cm))

# Table with styled headers, borders, alternating rows
data = [
    ["Region", "Q1 Revenue", "Growth", "Target Met"],
    ["North America", "$4.2M", "+12%", "Yes"],
    ["Europe", "$3.1M", "+8%", "Yes"],
    ["Asia Pacific", "$2.7M", "+22%", "Yes"],
    ["Latin America", "$1.1M", "-3%", "No"],
    ["Middle East", "$0.8M", "+5%", "Partial"],
]

table = Table(data, colWidths=[4.5*cm, 3.5*cm, 2.5*cm, 3*cm])
table.setStyle(TableStyle([
    # Header row
    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0066cc")),
    ("TEXTCOLOR", (0, 0), (-1, 0), white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 11),
    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ("TOPPADDING", (0, 0), (-1, 0), 8),
    # Data rows
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 1), (-1, -1), 10),
    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
    ("TOPPADDING", (0, 1), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
    # Alternating row colors
    *[("BACKGROUND", (0, i), (-1, i), HexColor("#f0f7ff"))
      for i in range(2, len(data), 2)],
    # Grid
    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
    ("BOX", (0, 0), (-1, -1), 1, HexColor("#0066cc")),
]))
story.append(table)
story.append(Spacer(1, 1 * cm))

# Optional image (uncomment if you have one)
# story.append(Image("/tmp/chart.png", width=14*cm, height=8*cm))

story.append(Paragraph("Key Insights", styles["SectionHead"]))
story.append(Paragraph(
    "Asia Pacific showed the strongest growth at 22%, driven by expansion "
    "into new markets. Latin America requires attention with a 3% decline.",
    styles["Normal"]))

# Page break to second page
story.append(PageBreak())
story.append(Paragraph("Appendix", styles["CustomTitle"]))
story.append(Paragraph("Detailed breakdowns available upon request.", styles["Normal"]))

doc.build(story)
print(f"Saved: {output}")
```

### PDF with Custom Fonts

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import ParagraphStyle

# Register custom font family (provide paths to your .ttf files)
pdfmetrics.registerFont(TTFont("MyFont", "/path/to/font-regular.ttf"))
pdfmetrics.registerFont(TTFont("MyFont-Bold", "/path/to/font-bold.ttf"))
pdfmetrics.registerFont(TTFont("MyFont-Italic", "/path/to/font-italic.ttf"))
pdfmetrics.registerFont(TTFont("MyFont-BoldItalic", "/path/to/font-bolditalic.ttf"))

# Register family so <b> and <i> tags in Paragraphs auto-switch
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("MyFont",
                   normal="MyFont",
                   bold="MyFont-Bold",
                   italic="MyFont-Italic",
                   boldItalic="MyFont-BoldItalic")

output = "/tmp/custom_fonts.pdf"
doc = SimpleDocTemplate(output, pagesize=A4)

style = ParagraphStyle("Custom", fontName="MyFont", fontSize=12, leading=16)

story = [
    Paragraph("Regular text in custom font.", style),
    Paragraph("<b>Bold text</b> switches automatically.", style),
    Paragraph("<i>Italic text</i> also switches.", style),
    Paragraph("<b><i>Bold italic</i></b> combination.", style),
]

doc.build(story)
print(f"Saved: {output}")
```

### PDF with Charts

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart

output = "/tmp/charts_report.pdf"
doc = SimpleDocTemplate(output, pagesize=A4)
styles = getSampleStyleSheet()
story = []

# --- Bar Chart ---
story.append(Paragraph("Revenue by Quarter", styles["Heading2"]))
d = Drawing(400, 200)
bc = VerticalBarChart()
bc.x, bc.y, bc.width, bc.height = 50, 30, 300, 150
bc.data = [
    (420, 510, 380, 590),   # Product A
    (310, 280, 450, 520),   # Product B
]
bc.categoryAxis.categoryNames = ["Q1", "Q2", "Q3", "Q4"]
bc.bars[0].fillColor = HexColor("#0066cc")
bc.bars[1].fillColor = HexColor("#ff6b35")
bc.valueAxis.valueMin = 0
bc.valueAxis.valueMax = 700
bc.valueAxis.valueStep = 100
d.add(bc)
story.append(d)
story.append(Spacer(1, 1 * cm))

# --- Pie Chart ---
story.append(Paragraph("Market Share", styles["Heading2"]))
d2 = Drawing(300, 200)
pie = Pie()
pie.x, pie.y, pie.width, pie.height = 75, 10, 150, 150
pie.data = [35, 25, 20, 12, 8]
pie.labels = ["Us 35%", "Comp A 25%", "Comp B 20%", "Comp C 12%", "Other 8%"]
pie.slices[0].fillColor = HexColor("#0066cc")
pie.slices[1].fillColor = HexColor("#ff6b35")
pie.slices[2].fillColor = HexColor("#2ec4b6")
pie.slices[3].fillColor = HexColor("#e71d36")
pie.slices[4].fillColor = HexColor("#999999")
pie.slices[0].popout = 5
d2.add(pie)
story.append(d2)
story.append(Spacer(1, 1 * cm))

# --- Line Chart ---
story.append(Paragraph("Monthly Trend", styles["Heading2"]))
d3 = Drawing(400, 200)
lc = HorizontalLineChart()
lc.x, lc.y, lc.width, lc.height = 50, 30, 300, 150
lc.data = [
    (10, 22, 35, 42, 55, 68, 72, 80, 91, 98, 105, 120),
    (5, 12, 18, 30, 38, 45, 50, 62, 70, 78, 85, 95),
]
lc.categoryAxis.categoryNames = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
lc.categoryAxis.labels.angle = 45
lc.categoryAxis.labels.dx = -10
lc.lines[0].strokeColor = HexColor("#0066cc")
lc.lines[0].strokeWidth = 2
lc.lines[1].strokeColor = HexColor("#ff6b35")
lc.lines[1].strokeWidth = 2
d3.add(lc)
story.append(d3)

doc.build(story)
print(f"Saved: {output}")
```

### PDF with Barcodes

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import code128
from reportlab.graphics.barcode.qr import QrCodeWidget

output = "/tmp/barcodes.pdf"
doc = SimpleDocTemplate(output, pagesize=A4)
styles = getSampleStyleSheet()
story = []

# Code128 Barcode
story.append(Paragraph("Code128 Barcode", styles["Heading2"]))
d = Drawing(300, 80)
barcode = code128.Code128("INV-2026-04-0042", barWidth=1.2, barHeight=50)
barcode.x, barcode.y = 10, 10
d.add(barcode)
story.append(d)
story.append(Spacer(1, 1 * cm))

# QR Code
story.append(Paragraph("QR Code", styles["Heading2"]))
d2 = Drawing(200, 200)
qr = QrCodeWidget("https://example.com/invoice/0042")
qr.barWidth = 150
qr.barHeight = 150
qr.x, qr.y = 10, 10
d2.add(qr)
story.append(d2)

doc.build(story)
print(f"Saved: {output}")
```

### PDF with Headers/Footers/Page Numbers

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

output = "/tmp/headers_footers.pdf"
w, h = A4

def header_footer(canvas, doc):
    canvas.saveState()
    # Header
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(HexColor("#0066cc"))
    canvas.drawString(2 * cm, h - 1.5 * cm, "Acme Corp -- Confidential")
    canvas.setStrokeColor(HexColor("#0066cc"))
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, h - 1.7 * cm, w - 2 * cm, h - 1.7 * cm)

    # Footer with "Page X of Y"
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#888888"))
    canvas.line(2 * cm, 1.5 * cm, w - 2 * cm, 1.5 * cm)
    page_text = f"Page {doc.page}"
    canvas.drawString(2 * cm, 1 * cm, "Generated 2026-04-04")
    canvas.drawRightString(w - 2 * cm, 1 * cm, page_text)
    canvas.restoreState()

# For "Page X of Y", use canvasmaker trick:
from reportlab.pdfgen.canvas import Canvas

class NumberedCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_pages = []

    def showPage(self):
        self._saved_pages.append(dict(self.__dict__))
        super().showPage()

    def save(self):
        total = len(self._saved_pages)
        for i, state in enumerate(self._saved_pages):
            self.__dict__.update(state)
            self.setFont("Helvetica", 8)
            self.setFillColor(HexColor("#888888"))
            self.drawRightString(w - 2 * cm, 1 * cm,
                                 f"Page {i + 1} of {total}")
        super().save()

doc = SimpleDocTemplate(output, pagesize=A4,
                        topMargin=3*cm, bottomMargin=2.5*cm)
styles = getSampleStyleSheet()

story = []
for i in range(1, 6):
    story.append(Paragraph(f"Section {i}", styles["Heading1"]))
    story.append(Paragraph("Lorem ipsum dolor sit amet. " * 30, styles["Normal"]))
    if i < 5:
        story.append(PageBreak())

doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer,
          canvasmaker=NumberedCanvas)
print(f"Saved: {output}")
```

### PDF with Table of Contents

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, TableOfContents,
)

output = "/tmp/toc_report.pdf"
styles = getSampleStyleSheet()

# TOC entry styles
styles.add(ParagraphStyle("TOCHeading1", parent=styles["Normal"],
                          fontSize=12, leading=16, leftIndent=0))
styles.add(ParagraphStyle("TOCHeading2", parent=styles["Normal"],
                          fontSize=10, leading=14, leftIndent=20))

class TOCDocTemplate(SimpleDocTemplate):
    """Subclass that notifies TOC of heading flowables."""
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style = flowable.style.name
            if style == "Heading1":
                level = 0
                text = flowable.getPlainText()
                self.notify("TOCEntry", (level, text, self.page))
            elif style == "Heading2":
                level = 1
                text = flowable.getPlainText()
                self.notify("TOCEntry", (level, text, self.page))

doc = TOCDocTemplate(output, pagesize=A4)

toc = TableOfContents()
toc.levelStyles = [styles["TOCHeading1"], styles["TOCHeading2"]]

story = []
story.append(Paragraph("Table of Contents", styles["Title"]))
story.append(Spacer(1, 0.5 * cm))
story.append(toc)
story.append(PageBreak())

chapters = [
    ("Introduction", ["Background", "Objectives"]),
    ("Methodology", ["Data Collection", "Analysis Framework"]),
    ("Results", ["Primary Findings", "Secondary Findings"]),
    ("Conclusion", ["Summary", "Recommendations"]),
]

for chapter, sections in chapters:
    story.append(Paragraph(chapter, styles["Heading1"]))
    for section in sections:
        story.append(Paragraph(section, styles["Heading2"]))
        story.append(Paragraph("Lorem ipsum dolor sit amet. " * 20, styles["Normal"]))
        story.append(Spacer(1, 0.5 * cm))
    story.append(PageBreak())

# Build twice: first pass populates TOC, second pass renders it
doc.multiBuild(story)
print(f"Saved: {output}")
```

### Multi-Column Layout

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

output = "/tmp/multi_column.pdf"
w, h = A4
margin = 2 * cm
gutter = 0.8 * cm
col_width = (w - 2 * margin - gutter) / 2

# Two-column frame layout
frame_left = Frame(margin, margin, col_width, h - 2 * margin, id="left")
frame_right = Frame(margin + col_width + gutter, margin,
                    col_width, h - 2 * margin, id="right")

doc = BaseDocTemplate(output, pagesize=A4)
doc.addPageTemplates([
    PageTemplate(id="TwoCol", frames=[frame_left, frame_right]),
])

styles = getSampleStyleSheet()
story = []

story.append(Paragraph("Two-Column Newsletter", styles["Title"]))
story.append(Spacer(1, 0.5 * cm))

for i in range(1, 7):
    story.append(Paragraph(f"Article {i}", styles["Heading2"]))
    story.append(Paragraph(
        "Sed ut perspiciatis unde omnis iste natus error sit voluptatem "
        "accusantium doloremque laudantium. " * 8, styles["Normal"]))
    story.append(Spacer(1, 0.3 * cm))

doc.build(story)
print(f"Saved: {output}")
```

### Interactive Form (AcroForm)

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

output = "/tmp/interactive_form.pdf"
c = canvas.Canvas(output, pagesize=A4)
w, h = A4
form = c.acroForm

c.setFont("Helvetica-Bold", 16)
c.drawString(2 * cm, h - 3 * cm, "Application Form")

y = h - 5 * cm

# Text field
c.setFont("Helvetica", 11)
c.drawString(2 * cm, y + 0.2 * cm, "Full Name:")
form.textfield(name="fullname", x=6*cm, y=y - 0.2*cm,
               width=10*cm, height=0.8*cm,
               borderColor=HexColor("#0066cc"),
               fillColor=HexColor("#f5f5f5"),
               fontSize=11, maxlen=100)
y -= 1.5 * cm

# Email field
c.drawString(2 * cm, y + 0.2 * cm, "Email:")
form.textfield(name="email", x=6*cm, y=y - 0.2*cm,
               width=10*cm, height=0.8*cm,
               borderColor=HexColor("#0066cc"),
               fillColor=HexColor("#f5f5f5"),
               fontSize=11)
y -= 1.5 * cm

# Checkbox
c.drawString(2 * cm, y + 0.2 * cm, "Agree to Terms:")
form.checkbox(name="agree", x=6*cm, y=y,
              size=0.5*cm,
              borderColor=HexColor("#0066cc"),
              fillColor=HexColor("#f5f5f5"),
              checked=False)
y -= 1.5 * cm

# Dropdown
c.drawString(2 * cm, y + 0.2 * cm, "Department:")
form.choice(name="department", x=6*cm, y=y - 0.2*cm,
            width=10*cm, height=0.8*cm,
            options=["Engineering", "Marketing", "Sales", "HR", "Finance"],
            value="Engineering",
            borderColor=HexColor("#0066cc"),
            fillColor=HexColor("#f5f5f5"),
            fontSize=11)

c.save()
print(f"Saved: {output}")
```

### Encrypted PDF

```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

output = "/tmp/encrypted_report.pdf"
doc = SimpleDocTemplate(output, pagesize=A4,
                        encrypt="my-secret-password")

# For fine-grained control:
from reportlab.lib.pdfencrypt import StandardEncryption
enc = StandardEncryption(
    userPassword="user-pass",       # password to open
    ownerPassword="owner-pass",     # password for full access
    canPrint=True,
    canModify=False,
    canCopy=False,
    canAnnotate=False,
    strength=128,                   # 40 or 128 bit
)
doc2 = SimpleDocTemplate("/tmp/encrypted_fine.pdf", pagesize=A4, encrypt=enc)

styles = getSampleStyleSheet()
story = [Paragraph("This document is password-protected.", styles["Normal"])]

doc.build(story)
doc2.build(list(story))  # copy the story for second build
print("Saved encrypted PDFs to /tmp/")
```

---

## PyMuPDF (fitz) — Read/Edit/Manipulate

### Render Page to Image (Screenshot)

```python
import fitz  # PyMuPDF

doc = fitz.open("/tmp/input.pdf")
page = doc[0]  # first page

# High-DPI render (300 DPI)
mat = fitz.Matrix(300 / 72, 300 / 72)
pix = page.get_pixmap(matrix=mat)
pix.save("/tmp/page_screenshot.png")

# All pages
for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 144 DPI
    pix.save(f"/tmp/page_{i+1}.png")

doc.close()
print("Saved page images to /tmp/")
```

### Extract Text (All Modes)

```python
import fitz
import json

doc = fitz.open("/tmp/input.pdf")
page = doc[0]

# Plain text
plain = page.get_text("text")
print("=== Plain text ===")
print(plain[:500])

# Structured dict with font info
blocks = page.get_text("dict")
for block in blocks["blocks"]:
    if block["type"] == 0:  # text block
        for line in block["lines"]:
            for span in line["spans"]:
                print(f"  Font: {span['font']}, Size: {span['size']:.1f}, "
                      f"Text: {span['text'][:60]}")

# HTML output
html = page.get_text("html")
with open("/tmp/page_content.html", "w", encoding="utf-8") as f:
    f.write(html)

doc.close()
```

### Search Text in PDF

```python
import fitz

doc = fitz.open("/tmp/input.pdf")
search_term = "invoice"

for page_num, page in enumerate(doc):
    matches = page.search_for(search_term, quads=False)
    for rect in matches:
        # Add yellow highlight annotation on each match
        highlight = page.add_highlight_annot(rect)
        highlight.set_colors(stroke=(1, 1, 0))
        highlight.update()
        print(f"Found '{search_term}' on page {page_num + 1} at {rect}")

doc.save("/tmp/highlighted.pdf")
doc.close()
```

### Extract Tables

```python
import fitz

doc = fitz.open("/tmp/input.pdf")
page = doc[0]

tables = page.find_tables()
print(f"Found {len(tables.tables)} table(s)")

for i, table in enumerate(tables.tables):
    data = table.extract()
    print(f"\nTable {i + 1}: {len(data)} rows x {len(data[0])} cols")
    for row in data[:5]:  # print first 5 rows
        print(row)

doc.close()
```

### Extract Images

```python
import fitz
import os

doc = fitz.open("/tmp/input.pdf")
os.makedirs("/tmp/extracted_images", exist_ok=True)

for page_num, page in enumerate(doc):
    images = page.get_images(full=True)
    for img_idx, img_info in enumerate(images):
        xref = img_info[0]
        img = doc.extract_image(xref)
        ext = img["ext"]
        img_bytes = img["image"]
        path = f"/tmp/extracted_images/page{page_num+1}_img{img_idx+1}.{ext}"
        with open(path, "wb") as f:
            f.write(img_bytes)
        print(f"Saved: {path} ({len(img_bytes)} bytes)")

doc.close()
```

### Add Annotations

```python
import fitz

doc = fitz.open("/tmp/input.pdf")
page = doc[0]

# Highlight text occurrence
matches = page.search_for("important")
for rect in matches:
    page.add_highlight_annot(rect)

# Sticky note
page.add_text_annot(fitz.Point(100, 200),
                    "Please review this section.",
                    icon="Note")

# Freetext annotation (visible text box)
page.add_freetext_annot(
    fitz.Rect(100, 300, 350, 340),
    "DRAFT - Not for distribution",
    fontsize=14,
    fontname="helv",
    text_color=fitz.pdfcolor["red"],
    fill_color=fitz.pdfcolor["yellow"],
    border_color=fitz.pdfcolor["red"],
)

# Stamp annotation
page.add_stamp_annot(
    fitz.Rect(400, 50, 550, 100),
    stamp=fitz.PDF_ANNOT_STAMP_APPROVED,  # 0 = Approved
)

doc.save("/tmp/annotated.pdf")
doc.close()
```

### Redact Content

```python
import fitz

doc = fitz.open("/tmp/input.pdf")
page = doc[0]

# Redact specific text
sensitive_terms = ["SSN", "123-45-6789", "confidential"]
for term in sensitive_terms:
    matches = page.search_for(term)
    for rect in matches:
        page.add_redact_annot(rect, fill=(0, 0, 0))  # black box

# Redact a specific rectangular area
page.add_redact_annot(fitz.Rect(50, 400, 300, 450), fill=(0, 0, 0))

# Apply all redactions (permanently removes content)
page.apply_redactions()

doc.save("/tmp/redacted.pdf")
doc.close()
print("Redacted content permanently removed.")
```

### Merge PDFs

```python
import fitz

output = fitz.open()  # new empty document

files = ["/tmp/doc1.pdf", "/tmp/doc2.pdf", "/tmp/doc3.pdf"]
for f in files:
    src = fitz.open(f)
    output.insert_pdf(src)  # append all pages
    src.close()

# Insert specific pages from another PDF
extra = fitz.open("/tmp/extra.pdf")
output.insert_pdf(extra, from_page=0, to_page=2)  # pages 1-3 only
extra.close()

output.save("/tmp/merged.pdf")
output.close()
print("Saved: /tmp/merged.pdf")
```

### Split PDF

```python
import fitz

doc = fitz.open("/tmp/input.pdf")
total = len(doc)

# Extract pages 1-5 into one file
part1 = fitz.open()
part1.insert_pdf(doc, from_page=0, to_page=4)
part1.save("/tmp/pages_1_to_5.pdf")
part1.close()

# Extract pages 6 to end
part2 = fitz.open()
part2.insert_pdf(doc, from_page=5, to_page=total - 1)
part2.save("/tmp/pages_6_to_end.pdf")
part2.close()

# Each page as separate file
for i in range(total):
    single = fitz.open()
    single.insert_pdf(doc, from_page=i, to_page=i)
    single.save(f"/tmp/page_{i+1}.pdf")
    single.close()

doc.close()
print(f"Split {total} pages into individual files.")
```

### Add Watermark

```python
import fitz

doc = fitz.open("/tmp/input.pdf")

for page in doc:
    # Text watermark
    tw = fitz.TextWriter(page.rect)
    font = fitz.Font("helv")
    fontsize = 60

    # Center the text and rotate
    text = "CONFIDENTIAL"
    text_width = font.text_length(text, fontsize=fontsize)
    rect = page.rect
    x = (rect.width - text_width) / 2
    y = rect.height / 2

    # Insert with rotation via a Shape
    shape = page.new_shape()
    shape.insert_text(
        fitz.Point(x, y),
        text,
        fontname="helv",
        fontsize=fontsize,
        color=(1, 0, 0),        # red
        rotate=45,
    )
    shape.finish(color=(1, 0, 0), fill_opacity=0.15)
    shape.commit(overlay=True)

doc.save("/tmp/watermarked.pdf")
doc.close()

# --- Overlay an existing PDF as watermark ---
doc = fitz.open("/tmp/input.pdf")
watermark = fitz.open("/tmp/watermark_template.pdf")
wm_page = watermark[0]

for page in doc:
    page.show_pdf_page(page.rect, watermark, 0, overlay=True)

doc.save("/tmp/watermarked_overlay.pdf")
doc.close()
watermark.close()
```

### Rotate and Crop Pages

```python
import fitz

doc = fitz.open("/tmp/input.pdf")

# Rotate page 1 by 90 degrees
doc[0].set_rotation(90)

# Rotate all pages
for page in doc:
    page.set_rotation(180)  # 0, 90, 180, 270

# Crop page to specific area (in points: 72 pts = 1 inch)
page = doc[0]
page.set_rotation(0)  # reset first
# Crop to upper-left quadrant
crop = fitz.Rect(0, 0, page.rect.width / 2, page.rect.height / 2)
page.set_cropbox(crop)

doc.save("/tmp/rotated_cropped.pdf")
doc.close()
```

### Fill Form Fields

```python
import fitz

doc = fitz.open("/tmp/fillable_form.pdf")

# List all form fields
for page in doc:
    for widget in page.widgets():
        print(f"Field: {widget.field_name!r}, Type: {widget.field_type}, "
              f"Value: {widget.field_value!r}")

# Fill fields by name
field_values = {
    "name": "Jane Smith",
    "email": "jane@example.com",
    "date": "2026-04-04",
    "amount": "1250.00",
}

for page in doc:
    for widget in page.widgets():
        if widget.field_name in field_values:
            widget.field_value = field_values[widget.field_name]
            widget.update()

doc.save("/tmp/filled_form.pdf")
doc.close()
print("Saved: /tmp/filled_form.pdf")
```

### Insert Text and Drawings

```python
import fitz

doc = fitz.open("/tmp/input.pdf")
page = doc[0]

shape = page.new_shape()

# Draw a rectangle
shape.draw_rect(fitz.Rect(50, 50, 250, 120))
shape.finish(color=(0, 0.4, 0.8), fill=(0.9, 0.95, 1), width=1.5)

# Draw a line
shape.draw_line(fitz.Point(50, 130), fitz.Point(250, 130))
shape.finish(color=(0.8, 0, 0), width=2)

# Insert text
shape.insert_text(
    fitz.Point(60, 90),
    "Stamped by automated process",
    fontname="helv",
    fontsize=12,
    color=(0, 0.3, 0.6),
)

# Insert multi-line text in a box
shape.insert_textbox(
    fitz.Rect(300, 50, 550, 150),
    "This is a multi-line text box that will wrap automatically "
    "within the defined rectangle area.",
    fontname="helv",
    fontsize=10,
    color=(0, 0, 0),
    align=fitz.TEXT_ALIGN_LEFT,
)

shape.commit()
doc.save("/tmp/drawings.pdf")
doc.close()
```

### TOC/Bookmarks

```python
import fitz

doc = fitz.open("/tmp/input.pdf")

# Read existing TOC
toc = doc.get_toc()
print("Current TOC:")
for level, title, page in toc:
    indent = "  " * (level - 1)
    print(f"{indent}{title} -> page {page}")

# Set new TOC (list of [level, title, page_number])
new_toc = [
    [1, "Introduction", 1],
    [2, "Background", 1],
    [2, "Scope", 2],
    [1, "Methodology", 3],
    [2, "Data Sources", 3],
    [2, "Analysis", 4],
    [1, "Results", 5],
    [1, "Conclusion", 8],
]
doc.set_toc(new_toc)

doc.save("/tmp/with_bookmarks.pdf")
doc.close()
print("Saved: /tmp/with_bookmarks.pdf")
```

### HTML to PDF (Story)

```python
import fitz

html_content = """
<html>
<head>
<style>
body { font-family: sans-serif; font-size: 11pt; color: #333; }
h1 { color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 5px; }
h2 { color: #1a1a2e; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; }
th { background-color: #0066cc; color: white; padding: 8px; text-align: left; }
td { border: 1px solid #ddd; padding: 8px; }
tr:nth-child(even) { background-color: #f2f2f2; }
.highlight { background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; }
</style>
</head>
<body>
<h1>Quarterly Report</h1>
<p>This report covers Q1 2026 performance metrics.</p>

<h2>Revenue Summary</h2>
<table>
<tr><th>Region</th><th>Revenue</th><th>Growth</th></tr>
<tr><td>North America</td><td>$4.2M</td><td>+12%</td></tr>
<tr><td>Europe</td><td>$3.1M</td><td>+8%</td></tr>
<tr><td>Asia Pacific</td><td>$2.7M</td><td>+22%</td></tr>
</table>

<div class="highlight">
<strong>Key Insight:</strong> Asia Pacific showed the strongest growth,
driven by expansion into new markets.
</div>

<h2>Next Steps</h2>
<ul>
<li>Expand APAC sales team by 20%</li>
<li>Launch European marketing campaign</li>
<li>Review LATAM pricing strategy</li>
</ul>
</body>
</html>
"""

output = "/tmp/html_to_pdf.pdf"
story = fitz.Story(html=html_content)

# A4 page with margins
MEDIABOX = fitz.paper_rect("a4")
WHERE = MEDIABOX + (36, 36, -36, -36)  # 0.5-inch margins

writer = fitz.DocumentWriter(output)

more = True
while more:
    device = writer.begin_page(MEDIABOX)
    more, _ = story.place(WHERE)
    story.draw(device)
    writer.end_page()

writer.close()
print(f"Saved: {output}")
```

### Metadata and Encryption

```python
import fitz

doc = fitz.open("/tmp/input.pdf")

# Read metadata
meta = doc.metadata
print("Current metadata:")
for key, val in meta.items():
    if val:
        print(f"  {key}: {val}")

# Set metadata
doc.set_metadata({
    "title": "Q1 2026 Report",
    "author": "Analytics Team",
    "subject": "Quarterly financial review",
    "keywords": "finance, quarterly, 2026",
    "creator": "Python / PyMuPDF",
    "producer": "Cortex PDF Pipeline",
})

doc.save("/tmp/with_metadata.pdf")
doc.close()

# Encrypt with password
doc = fitz.open("/tmp/with_metadata.pdf")
perm = (
    fitz.PDF_PERM_ACCESSIBILITY  # allow accessibility
    | fitz.PDF_PERM_PRINT         # allow printing
    # Omit fitz.PDF_PERM_MODIFY to prevent editing
    # Omit fitz.PDF_PERM_COPY to prevent copying
)
doc.save(
    "/tmp/encrypted.pdf",
    encryption=fitz.PDF_ENCRYPT_AES_256,
    user_pw="reader-pass",       # password to open
    owner_pw="admin-pass",       # password for full access
    permissions=perm,
)
doc.close()
print("Saved: /tmp/encrypted.pdf")
```

---

## PyPDF2/pypdf -- Merge/Split/Transform

### Merge Multiple PDFs

```python
from pypdf import PdfMerger

merger = PdfMerger()

# Append entire documents
merger.append("/tmp/doc1.pdf")
merger.append("/tmp/doc2.pdf")

# Append specific page range (0-indexed)
merger.append("/tmp/doc3.pdf", pages=(0, 5))   # pages 1-5
merger.append("/tmp/doc4.pdf", pages=(2, 4))   # pages 3-4

merger.write("/tmp/merged.pdf")
merger.close()
print("Saved: /tmp/merged.pdf")
```

### Add Watermark

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("/tmp/input.pdf")
watermark_reader = PdfReader("/tmp/watermark.pdf")
watermark_page = watermark_reader.pages[0]

writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark_page)
    writer.add_page(page)

with open("/tmp/watermarked.pdf", "wb") as f:
    writer.write(f)

print("Saved: /tmp/watermarked.pdf")
```

### Encrypt/Decrypt

```python
from pypdf import PdfReader, PdfWriter

# Decrypt a protected PDF
reader = PdfReader("/tmp/protected.pdf")
if reader.is_encrypted:
    reader.decrypt("the-password")

# Re-encrypt with new passwords
writer = PdfWriter()
for page in reader.pages:
    writer.add_page(page)

writer.encrypt(
    user_password="reader123",    # to open
    owner_password="admin456",    # for full access
    permissions_flag=0b0100,      # print-only
)

with open("/tmp/re_encrypted.pdf", "wb") as f:
    writer.write(f)

print("Saved: /tmp/re_encrypted.pdf")
```

### Extract Text

```python
from pypdf import PdfReader

reader = PdfReader("/tmp/input.pdf")

# Simple extraction
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    print(f"--- Page {i + 1} ---")
    print(text[:500])

# With visitor functions for structured extraction
parts = []

def visitor_text(text, cm, tm, font_dict, font_size):
    if text.strip():
        parts.append({
            "text": text.strip(),
            "font_size": font_size,
            "x": tm[4],
            "y": tm[5],
        })

page = reader.pages[0]
page.extract_text(visitor_text=visitor_text)

for p in parts[:20]:
    print(f"  [{p['font_size']:.1f}pt @ ({p['x']:.0f},{p['y']:.0f})] {p['text'][:60]}")
```

### Add Bookmarks

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("/tmp/input.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

# Top-level bookmarks
intro = writer.add_outline_item("Introduction", 0)         # page 1
methods = writer.add_outline_item("Methodology", 2)        # page 3
results = writer.add_outline_item("Results", 5)            # page 6
conclusion = writer.add_outline_item("Conclusion", 9)      # page 10

# Nested bookmarks (children of "Results")
writer.add_outline_item("Primary Findings", 5, parent=results)
writer.add_outline_item("Secondary Findings", 7, parent=results)

with open("/tmp/bookmarked.pdf", "wb") as f:
    writer.write(f)

print("Saved: /tmp/bookmarked.pdf")
```

### Fill Form Fields

```python
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

reader = PdfReader("/tmp/fillable_form.pdf")
writer = PdfWriter()
writer.append(reader)

# List available fields
fields = reader.get_fields()
for name, field in fields.items():
    print(f"Field: {name!r} = {field.get('/V', 'empty')}")

# Fill fields
writer.update_page_form_field_values(
    writer.pages[0],
    {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "date": "2026-04-04",
        "amount": "1250.00",
    },
    auto_regenerate=False,
)

with open("/tmp/filled_form.pdf", "wb") as f:
    writer.write(f)

print("Saved: /tmp/filled_form.pdf")
```

---

## pdfplumber -- Extract Data

### Extract Text with Layout

```python
import pdfplumber

with pdfplumber.open("/tmp/input.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        # Layout mode preserves spatial positioning
        text = page.extract_text(layout=True)
        print(f"=== Page {i + 1} ===")
        print(text[:1000])
        print()
```

### Extract Tables

```python
import pdfplumber

with pdfplumber.open("/tmp/input.pdf") as pdf:
    page = pdf.pages[0]

    # Default table extraction
    tables = page.extract_tables()
    for i, table in enumerate(tables):
        print(f"Table {i + 1}: {len(table)} rows")
        for row in table[:5]:
            print(row)

    # Custom settings for tricky tables
    custom_settings = {
        "vertical_strategy": "text",        # "lines", "text", "explicit"
        "horizontal_strategy": "text",
        "snap_tolerance": 5,
        "join_tolerance": 5,
        "min_words_vertical": 3,
        "min_words_horizontal": 1,
    }

    tables2 = page.extract_tables(table_settings=custom_settings)
    print(f"\nWith custom settings: {len(tables2)} table(s) found")

    # Find tables (returns Table objects with metadata)
    found = page.find_tables(table_settings=custom_settings)
    for t in found:
        print(f"  Table at bbox={t.bbox}, {len(t.rows)} rows")
        data = t.extract()
        print(f"  Header: {data[0]}")
```

### Visual Debugging

```python
import pdfplumber

with pdfplumber.open("/tmp/input.pdf") as pdf:
    page = pdf.pages[0]

    # Convert page to image
    im = page.to_image(resolution=150)

    # Draw detected tables
    tables = page.find_tables()
    for table in tables:
        im.draw_rect(table.bbox, stroke="red", stroke_width=2)
        for row in table.rows:
            im.draw_rect(row.bbox, stroke="blue", stroke_width=1)
        for cell in table.cells:
            im.draw_rect(cell, stroke="green", stroke_width=0.5)

    # Draw detected lines
    im.draw_lines(page.lines, stroke="orange", stroke_width=1)

    # Draw character bounding boxes
    # im.draw_rects([c["top"] for c in page.chars])  # can be slow

    im.save("/tmp/debug_tables.png", format="PNG")
    print("Saved: /tmp/debug_tables.png")
```

### Extract from Specific Region

```python
import pdfplumber

with pdfplumber.open("/tmp/input.pdf") as pdf:
    page = pdf.pages[0]

    # Crop to a specific bounding box (x0, top, x1, bottom) in points
    # Top-left quadrant
    bbox = (0, 0, page.width / 2, page.height / 2)
    cropped = page.crop(bbox)

    text = cropped.extract_text()
    print("Text from top-left quadrant:")
    print(text[:500])

    # Extract table from a specific region
    table_region = (50, 200, 550, 500)  # adjust to your PDF
    cropped2 = page.crop(table_region)
    tables = cropped2.extract_tables()
    for t in tables:
        for row in t:
            print(row)

    # Visual verification of crop region
    im = page.to_image(resolution=150)
    im.draw_rect(table_region, stroke="red", stroke_width=2)
    im.save("/tmp/crop_debug.png")
```

### Search Text with Position

```python
import pdfplumber
import re

with pdfplumber.open("/tmp/input.pdf") as pdf:
    for page_num, page in enumerate(pdf.pages):
        # Search with regex
        results = page.search(r"invoice\s*#?\s*\d+", regex=True, case=False)

        for match in results:
            print(f"Page {page_num + 1}: Found '{match['text']}' at "
                  f"bbox=({match['x0']:.0f}, {match['top']:.0f}, "
                  f"{match['x1']:.0f}, {match['bottom']:.0f})")

        # Search for exact string
        exact = page.search("Total Amount", case=False)
        for m in exact:
            # Extract text to the right of the match (same line)
            right_region = (m["x1"], m["top"] - 2, page.width, m["bottom"] + 2)
            cropped = page.crop(right_region)
            value = cropped.extract_text()
            if value:
                print(f"  -> Value: {value.strip()}")
```
