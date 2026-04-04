# Document Creation Libraries Reference

Comprehensive API reference for `openpyxl`, `python-docx`, and `python-pptx`.

---

# 1. openpyxl (Excel .xlsx)

```python
from openpyxl import Workbook, load_workbook
```

## 1.1 Workbook & Worksheet Operations

### Create & Open

```python
wb = Workbook()                              # Create new workbook
wb = load_workbook("file.xlsx")              # Open existing
wb = load_workbook("file.xlsx", read_only=True)   # Read-only mode (large files)
wb = load_workbook("file.xlsx", data_only=True)   # Read cached formula values
wb = load_workbook("file.xlsx", keep_vba=True)    # Preserve VBA macros
wb = load_workbook("file.xlsx", keep_links=True)  # Preserve external links
```

### Save

```python
wb.save("output.xlsx")
wb.template = True                           # Save as template
wb.save("output.xltx")
```

### Sheet Operations

```python
ws = wb.active                               # Get active sheet
ws = wb["SheetName"]                         # Get sheet by name
ws = wb.create_sheet("Name")                 # Append new sheet
ws = wb.create_sheet("Name", 0)              # Insert at position
wb.sheetnames                                # List all sheet names -> list[str]
wb.worksheets                                # List all worksheet objects

wb.copy_worksheet(ws)                        # Copy worksheet (within same workbook)
wb.move_sheet("Name", offset=2)              # Move sheet right by 2
wb.move_sheet("Name", offset=-1)             # Move sheet left by 1
wb.remove(ws)                                # Delete sheet
del wb["SheetName"]                          # Delete sheet by name

ws.title = "NewName"                         # Rename sheet
ws.sheet_properties.tabColor = "FF0000"      # Tab color (hex RGB, no #)
ws.sheet_state = "visible"                   # "visible" | "hidden" | "veryHidden"
```

### Write-Only Mode (Streaming Large Files)

```python
wb = Workbook(write_only=True)
ws = wb.create_sheet()
ws.append([1, 2, 3])                        # Only append() is available
wb.save("large.xlsx")
```

## 1.2 Cell Operations

### Read & Write

```python
ws["A1"] = "Hello"                           # Write by coordinate
ws["A1"].value                               # Read value
ws.cell(row=1, column=1, value="Hello")      # Write by row/col index (1-based)
cell = ws.cell(row=1, column=1)              # Get cell object
cell.value                                   # Read value
cell.data_type                               # "s"=string, "n"=number, "d"=date, "b"=bool, "f"=formula, "e"=error
cell.coordinate                              # "A1"
cell.row                                     # 1
cell.column                                  # 1
cell.column_letter                           # "A"
```

### Ranges

```python
ws["A1":"C3"]                                # Tuple of row tuples
ws["A"]                                      # Entire column A
ws["A:C"]                                    # Columns A through C
ws[1]                                        # Entire row 1
ws[1:3]                                      # Rows 1 through 3

# Iterate rows (returns tuples of cells)
for row in ws.iter_rows(min_row=1, max_row=10, min_col=1, max_col=5, values_only=False):
    for cell in row:
        pass

# Iterate columns
for col in ws.iter_cols(min_row=1, max_row=10, min_col=1, max_col=5, values_only=True):
    pass

# values_only=True returns raw values instead of cell objects
```

### Append Rows

```python
ws.append([1, 2, 3])                         # Append list as row
ws.append({"A": 1, "C": 3})                  # Append dict (column letter keys)
```

### Formulas

```python
ws["A1"] = "=SUM(B1:B10)"                   # Write formula
# load_workbook("f.xlsx", data_only=True) to read cached formula results
```

### Merged Cells

```python
ws.merge_cells("A1:D1")                      # Merge range
ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=4)
ws.unmerge_cells("A1:D1")                    # Unmerge
ws.merged_cells.ranges                        # List merged ranges
```

### Hyperlinks

```python
ws["A1"].hyperlink = "https://example.com"
ws["A1"].value = "Click here"
ws["A1"].style = "Hyperlink"

# Internal link
from openpyxl.worksheet.hyperlink import Hyperlink
ws["A1"].hyperlink = Hyperlink(ref="A1", location="'Sheet2'!A1", display="Go to Sheet2")
```

### Comments

```python
from openpyxl.comments import Comment
ws["A1"].comment = Comment("Comment text", "Author Name")
ws["A1"].comment.width = 300                 # Comment box width (pixels)
ws["A1"].comment.height = 150                # Comment box height (pixels)
```

## 1.3 Styling & Formatting

```python
from openpyxl.styles import (
    Font, PatternFill, GradientFill, Border, Side,
    Alignment, Protection, NamedStyle, numbers
)
from openpyxl.styles.colors import Color
```

### Font

```python
Font(
    name="Calibri",              # Font family name
    size=11,                     # Point size (float)
    bold=False,                  # bool
    italic=False,                # bool
    underline="none",            # "none" | "single" | "double" | "singleAccounting" | "doubleAccounting"
    strike=False,                # Strikethrough (bool)
    vertAlign=None,              # "superscript" | "subscript" | "baseline" | None
    color="000000",              # Hex RGB string (6 chars, no #)
    # Or use Color object:
    color=Color(rgb="FF0000"),       # RGB
    color=Color(theme=1),            # Theme color index (0-11)
    color=Color(indexed=8),          # Indexed color (0-63)
    color=Color(tint=-0.5),          # Tint modifier (-1.0 to 1.0)
    charset=None,                # Character set (int)
    family=None,                 # Font family (1=Roman, 2=Swiss, 3=Modern, etc.)
    scheme=None,                 # "major" | "minor" | None (theme font scheme)
)
```

### Fill

#### PatternFill

```python
PatternFill(
    patternType="solid",         # Fill pattern (see below)
    fgColor="FFFF00",           # Foreground color (hex RGB)
    bgColor="000000",           # Background color (for patterns)
)
# patternType values (18 patterns):
# "none", "solid", "darkDown", "darkGray", "darkGrid", "darkHorizontal",
# "darkTrellis", "darkUp", "darkVertical", "gray0625", "gray125",
# "lightDown", "lightGray", "lightGrid", "lightHorizontal", "lightTrellis",
# "lightUp", "lightVertical", "mediumGray"
```

#### GradientFill

```python
GradientFill(
    type="linear",               # "linear" | "path"
    degree=0,                    # Angle for linear (0=left-to-right, 90=top-to-bottom)
    left=0, right=0,             # For "path" type: focal point (0.0-1.0)
    top=0, bottom=0,             # For "path" type: focal point (0.0-1.0)
    stop=[                       # Color stops (list of Color or hex strings)
        Color(rgb="FF0000"),
        Color(rgb="0000FF"),
    ]
)
```

### Border

```python
Border(
    left=Side(border_style="thin", color="000000"),
    right=Side(border_style="thin", color="000000"),
    top=Side(border_style="thin", color="000000"),
    bottom=Side(border_style="thin", color="000000"),
    diagonal=Side(border_style="thin", color="000000"),
    diagonalDown=False,          # bool - diagonal line top-left to bottom-right
    diagonalUp=False,            # bool - diagonal line bottom-left to top-right
)

# Side border_style values (14 styles):
# None, "thin", "medium", "thick", "double",
# "hair", "dotted", "dashed", "mediumDashed",
# "dashDot", "mediumDashDot", "dashDotDot", "mediumDashDotDot",
# "slantDashDot"
```

### Alignment

```python
Alignment(
    horizontal="general",        # "general" | "left" | "center" | "right" | "fill"
                                 #   | "justify" | "centerContinuous" | "distributed"
    vertical="bottom",           # "top" | "center" | "bottom" | "justify" | "distributed"
    textRotation=0,              # 0-180 (degrees); 255 = vertical stacked text
    wrapText=False,              # bool - wrap text in cell
    shrinkToFit=False,           # bool - shrink font to fit cell
    indent=0,                    # int - indent level (0+)
    relativeIndent=0,            # int - relative indent change
    justifyLastLine=None,        # bool
    readingOrder=0,              # 0=context, 1=LTR, 2=RTL
)
```

### Number Formats

```python
cell.number_format = "0.00"                  # Two decimals
cell.number_format = "#,##0"                 # Thousands separator
cell.number_format = "#,##0.00"              # Thousands + decimals
cell.number_format = "0%"                    # Percentage
cell.number_format = "0.00%"                 # Percentage with decimals
cell.number_format = "$#,##0.00"             # Currency
cell.number_format = "yyyy-mm-dd"            # Date
cell.number_format = "dd/mm/yyyy"            # Date
cell.number_format = "hh:mm:ss"              # Time
cell.number_format = "yyyy-mm-dd hh:mm:ss"  # Datetime
cell.number_format = '0.00E+00'              # Scientific
cell.number_format = '@'                     # Text (force text)
cell.number_format = '[Red]0.00;[Blue]-0.00' # Conditional colors

# Built-in format constants
from openpyxl.styles.numbers import FORMAT_PERCENTAGE, FORMAT_DATE_DATETIME, \
    FORMAT_NUMBER_COMMA_SEPARATED1, FORMAT_CURRENCY_USD_SIMPLE
```

### Applying Styles

```python
cell.font = Font(bold=True, size=14)
cell.fill = PatternFill(patternType="solid", fgColor="FFFF00")
cell.border = Border(bottom=Side(border_style="thick", color="000000"))
cell.alignment = Alignment(horizontal="center", vertical="center", wrapText=True)
cell.number_format = "#,##0.00"
cell.protection = Protection(locked=True, hidden=False)
```

### Named Styles

```python
style = NamedStyle(name="highlight")
style.font = Font(bold=True, size=14, color="FFFFFF")
style.fill = PatternFill(patternType="solid", fgColor="4472C4")
style.alignment = Alignment(horizontal="center")
style.border = Border(
    bottom=Side(border_style="thin", color="000000")
)
style.number_format = "#,##0.00"

wb.add_named_style(style)                   # Register once per workbook
cell.style = "highlight"                     # Apply by name (string)
```

### Rich Text (Mixed Formatting in One Cell)

```python
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont

rich = CellRichText(
    "Normal text, ",
    TextBlock(InlineFont(b=True, sz=14), "bold large, "),
    TextBlock(InlineFont(i=True, color="FF0000"), "italic red"),
)
ws["A1"].value = rich
# InlineFont params: rFont (name), charset, family, b, i, strike, outline,
#   shadow, condense, extend, color, sz, u, vertAlign, scheme
```

## 1.4 Conditional Formatting

```python
from openpyxl.formatting.rule import (
    CellIsRule, FormulaRule, ColorScaleRule, DataBarRule, IconSetRule
)
```

### CellIsRule

```python
ws.conditional_formatting.add(
    "A1:A100",
    CellIsRule(
        operator="greaterThan",       # "between" | "notBetween" | "equal" | "notEqual"
                                      # "greaterThan" | "lessThan" | "greaterThanOrEqual"
                                      # "lessThanOrEqual"
        formula=["50"],               # List of values (2 for between/notBetween)
        fill=PatternFill(bgColor="FFC7CE"),
        font=Font(color="9C0006"),
        border=Border(...),
        stopIfTrue=True,
    )
)
```

### FormulaRule

```python
ws.conditional_formatting.add(
    "A1:A100",
    FormulaRule(
        formula=["ISBLANK(A1)"],      # Formula (must return TRUE/FALSE)
        fill=PatternFill(bgColor="FFFF00"),
        font=Font(bold=True),
        stopIfTrue=False,
    )
)
```

### ColorScaleRule

```python
# 2-color scale
ws.conditional_formatting.add(
    "A1:A100",
    ColorScaleRule(
        start_type="min",            # "min" | "max" | "num" | "percent" | "percentile" | "formula"
        start_value=None,            # Value (required if type is num/percent/percentile/formula)
        start_color="F8696B",        # Hex RGB
        end_type="max",
        end_value=None,
        end_color="63BE7B",
    )
)

# 3-color scale
ColorScaleRule(
    start_type="min", start_color="F8696B",
    mid_type="percentile", mid_value=50, mid_color="FFEB84",
    end_type="max", end_color="63BE7B",
)
```

### DataBarRule

```python
ws.conditional_formatting.add(
    "A1:A100",
    DataBarRule(
        start_type="min",
        start_value=None,
        end_type="max",
        end_value=None,
        color="638EC6",              # Bar color
        showValue=True,              # Show cell value alongside bar
        minLength=None,              # Min bar length (percent)
        maxLength=None,              # Max bar length (percent)
    )
)
```

### IconSetRule

```python
ws.conditional_formatting.add(
    "A1:A100",
    IconSetRule(
        icon_style="3TrafficLights1",  # Icon set name (see below)
        type="percent",                # "percent" | "num" | "percentile" | "formula"
        values=[0, 33, 67],           # Threshold values
        showValue=True,               # Show cell value alongside icon
        reverse=False,                # Reverse icon order
    )
)
# icon_style values:
# "3Arrows", "3ArrowsGray", "3Flags", "3Signs", "3Stars",
# "3Symbols", "3Symbols2", "3TrafficLights1", "3TrafficLights2", "3Triangles",
# "4Arrows", "4ArrowsGray", "4Rating", "4RedToBlack", "4TrafficLights",
# "5Arrows", "5ArrowsGray", "5Quarters", "5Rating"
```

## 1.5 Data Validation

```python
from openpyxl.worksheet.datavalidation import DataValidation
```

```python
dv = DataValidation(
    type="list",                     # "whole" | "decimal" | "list" | "date" | "time"
                                     #   | "textLength" | "custom"
    operator="between",              # "between" | "notBetween" | "equal" | "notEqual"
                                     #   | "greaterThan" | "lessThan" | "greaterThanOrEqual"
                                     #   | "lessThanOrEqual"
                                     # (not used for "list" or "custom")
    formula1='"Option1,Option2,Option3"',   # First value / formula / list
    formula2=None,                   # Second value (for between/notBetween)
    allow_blank=True,                # Allow empty cells (bool)
    showDropDown=False,              # NOTE: False=SHOW dropdown for lists (counterintuitive)
    showInputMessage=True,           # Show input message on cell select
    showErrorMessage=True,           # Show error on invalid input
    errorTitle="Invalid",            # Error dialog title
    error="Please select a valid option",   # Error dialog message
    errorStyle="stop",               # "stop" | "warning" | "information"
    promptTitle="Select",            # Input prompt title
    prompt="Choose from list",       # Input prompt message
)

dv.add("A1:A100")                           # Apply to range
ws.add_data_validation(dv)                   # Register on worksheet

# List from cell range
dv = DataValidation(type="list", formula1="=Sheet2!$A$1:$A$10")

# Whole number between 1 and 100
dv = DataValidation(type="whole", operator="between", formula1=1, formula2=100)

# Text length
dv = DataValidation(type="textLength", operator="lessThanOrEqual", formula1=50)

# Custom formula
dv = DataValidation(type="custom", formula1="=AND(A1>0,A1<100)")
```

## 1.6 Charts

```python
from openpyxl.chart import (
    AreaChart, AreaChart3D, BarChart, BarChart3D,
    LineChart, LineChart3D, PieChart, PieChart3D,
    DoughnutChart, ScatterChart, BubbleChart,
    RadarChart, StockChart, SurfaceChart, SurfaceChart3D,
    Reference, Series
)
```

### Create a Chart (General Pattern)

```python
chart = BarChart()                           # Instantiate chart type
chart.type = "col"                           # "col" (vertical) | "bar" (horizontal)
chart.grouping = "clustered"                 # "clustered" | "stacked" | "percentStacked" | "standard"
chart.style = 10                             # Built-in style number (1-48)
chart.title = "Sales Report"                 # Chart title (str or None)
chart.y_axis.title = "Amount"               # Y-axis title
chart.x_axis.title = "Month"                # X-axis title
chart.width = 20                             # Chart width (cm)
chart.height = 15                            # Chart height (cm)

# Data references
data = Reference(ws, min_col=2, max_col=4, min_row=1, max_row=10)   # Data series
cats = Reference(ws, min_col=1, min_row=2, max_row=10)              # Category labels

chart.add_data(data, titles_from_data=True)  # Add data (first row = series names)
chart.set_categories(cats)                   # Set category axis labels
chart.shape = 4                              # Bar shape (0-7 for 3D)

ws.add_chart(chart, "E1")                    # Place chart at anchor cell
```

### Chart Types & Specific Properties

```python
# ---- Area ----
AreaChart()                  # type not needed; grouping: "standard" | "stacked" | "percentStacked"
AreaChart3D()

# ---- Bar / Column ----
BarChart()                   # type="col" (columns) | type="bar" (horizontal bars)
BarChart3D()                 # grouping: "clustered" | "stacked" | "percentStacked"
chart.overlap = 50           # Bar overlap percentage (-100 to 100, bar/col only)
chart.gapWidth = 150         # Gap between bars (percent, 0-500)

# ---- Line ----
LineChart()                  # grouping: "standard" | "stacked" | "percentStacked"
LineChart3D()

# ---- Pie / Doughnut ----
PieChart()                   # No axis; single data series only
PieChart3D()
DoughnutChart()              # hole_size attribute (10-90, default 50)

# ---- Scatter / Bubble ----
ScatterChart()               # style: "line" | "lineMarker" | "marker" | "smooth" | "smoothMarker"
BubbleChart()                # Each series needs x, y, size references

# ---- Radar ----
RadarChart()                 # type: "standard" | "filled" | "marker"

# ---- Stock ----
StockChart()                 # Requires 3-5 series (High-Low-Close, Open-High-Low-Close, Volume-...)

# ---- Surface ----
SurfaceChart()
SurfaceChart3D()
```

### Axes

```python
from openpyxl.chart.axis import TextAxis, NumericAxis, DateAxis, SeriesAxis

chart.x_axis                                 # Category axis (TextAxis or DateAxis)
chart.y_axis                                 # Value axis (NumericAxis)

# Numeric axis properties
chart.y_axis.scaling.min = 0                 # Minimum value
chart.y_axis.scaling.max = 100               # Maximum value
chart.y_axis.scaling.logBase = 10            # Logarithmic scale base
chart.y_axis.majorUnit = 10                  # Major gridline interval
chart.y_axis.minorUnit = 5                   # Minor gridline interval
chart.y_axis.majorGridlines = None           # Remove major gridlines (set to object to show)
chart.y_axis.minorGridlines = None           # Remove minor gridlines
chart.y_axis.tickLblPos = "low"              # "high" | "low" | "nextTo" | None
chart.y_axis.numFmt = "#,##0.00"             # Number format for labels
chart.y_axis.delete = False                  # True to hide axis entirely
chart.y_axis.crosses = "min"                 # "min" | "max" | "autoZero"
chart.y_axis.crossesAt = 0                   # Custom cross value

# Text axis (category)
chart.x_axis.tickLblPos = "low"
chart.x_axis.lblOffset = 100                 # Label offset (percent)
chart.x_axis.tickLblSkip = 1                 # Show every Nth label
chart.x_axis.tickMarkSkip = 1                # Show every Nth tick

# Date axis
from openpyxl.chart.axis import DateAxis
chart.x_axis = DateAxis()
chart.x_axis.baseTimeUnit = "months"         # "days" | "months" | "years"
chart.x_axis.majorUnit = 1
chart.x_axis.majorTimeUnit = "months"
```

### Combination / Dual-Axis Charts

```python
from copy import deepcopy

c1 = BarChart()
c1.add_data(data1, titles_from_data=True)
c1.y_axis.title = "Bars"

c2 = LineChart()
c2.add_data(data2, titles_from_data=True)
c2.y_axis.title = "Lines"
c2.y_axis.axId = 200                         # Unique axis ID for secondary axis
c2.y_axis.crosses = "max"                    # Position secondary axis on right

c1 += c2                                     # Combine charts
ws.add_chart(c1, "E1")
```

### Legend

```python
from openpyxl.chart.legend import Legend
chart.legend = Legend()
chart.legend.position = "b"                  # "b" (bottom) | "t" | "l" | "r" | "tr"
chart.legend = None                          # Remove legend
```

### Data Labels

```python
from openpyxl.chart.label import DataLabelList
chart.dataLabels = DataLabelList()
chart.dataLabels.showVal = True              # Show value
chart.dataLabels.showCatName = True          # Show category name
chart.dataLabels.showSerName = False         # Show series name
chart.dataLabels.showPercent = True          # Show percentage (pie/doughnut)
chart.dataLabels.showLeaderLines = True      # Leader lines (pie)
chart.dataLabels.numFmt = "0.0%"             # Number format
```

### Series Formatting

```python
from openpyxl.chart.series import SeriesLabel
from openpyxl.drawing.line import LineProperties, LineEndProperties
from openpyxl.chart.marker import Marker

series = chart.series[0]
series.graphicalProperties.solidFill = "FF0000"    # Fill color
series.graphicalProperties.line.solidFill = "0000FF"  # Line/border color
series.graphicalProperties.line.width = 25000      # Line width (EMU)
series.graphicalProperties.line.dashStyle = "dash"  # "solid"|"dash"|"dot"|"dashDot"|"lgDash" etc.
series.smooth = True                                # Smooth line (line/scatter)

# Markers (line/scatter)
series.marker = Marker()
series.marker.symbol = "circle"              # "circle"|"dash"|"diamond"|"dot"|"plus"|"square"|"star"|"triangle"|"x"|"auto"
series.marker.size = 7                       # Marker size (2-72)
series.marker.graphicalProperties.solidFill = "FF0000"
```

### Trendlines

```python
from openpyxl.chart.trendline import Trendline
series.trendline = Trendline(
    trendlineType="linear",                  # "linear"|"log"|"exp"|"power"|"poly"|"movingAvg"
    order=2,                                 # Polynomial order (2-6, for "poly")
    period=3,                                # Moving average period (for "movingAvg")
    forward=2,                               # Forecast forward periods
    backward=1,                              # Forecast backward periods
    dispEq=True,                             # Display equation
    dispRSqr=True,                           # Display R-squared
    intercept=0,                             # Set intercept value
)
```

### Error Bars

```python
from openpyxl.chart.error_bar import ErrorBars
series.errBars = ErrorBars(
    errBarType="both",                       # "both" | "plus" | "minus"
    errValType="fixedVal",                   # "fixedVal"|"percentage"|"stdDev"|"stdErr"|"cust"
    val=5,                                   # Fixed value or percentage
)
```

## 1.7 Tables

```python
from openpyxl.worksheet.table import Table, TableStyleInfo
```

```python
tab = Table(
    displayName="SalesTable",                # Unique table name (no spaces)
    ref="A1:D10",                            # Table range (string)
)
style = TableStyleInfo(
    name="TableStyleMedium9",                # Built-in style name (TableStyleLight1-28, Medium1-28, Dark1-11)
    showFirstColumn=False,
    showLastColumn=False,
    showRowStripes=True,
    showColumnStripes=False,
)
tab.tableStyleInfo = style

ws.add_table(tab)

# Auto-filter (tables include auto-filter by default)
tab.autoFilter.ref = "A1:D10"

# Totals row
tab.totalsRowCount = 1                       # Enable totals row
# Configure totals per column via column objects
```

## 1.8 Defined Names / Named Ranges

```python
from openpyxl.workbook.defined_name import DefinedName

# Workbook-scoped
dn = DefinedName("MyRange", attr_text="Sheet1!$A$1:$B$10")
wb.defined_names.add(dn)

# Sheet-scoped (localSheetId = sheet index)
dn = DefinedName("LocalRange", attr_text="Sheet1!$A$1:$B$10", localSheetId=0)
wb.defined_names.add(dn)

# Read defined names
for name in wb.defined_names.definedName:
    print(name.name, name.attr_text)
```

## 1.9 Auto-Filter & Sorting

```python
ws.auto_filter.ref = "A1:D100"               # Enable auto-filter on range
ws.auto_filter.add_filter_column(0, ["Value1", "Value2"])  # Filter column index 0
ws.auto_filter.add_sort_condition("B1:B100")  # Sort by column
```

## 1.10 Images

```python
from openpyxl.drawing.image import Image

img = Image("logo.png")
img.width = 200                              # Pixels
img.height = 100                             # Pixels
ws.add_image(img, "A1")                      # Anchor at cell
```

## 1.11 Page Setup & Print

```python
ws.page_setup.orientation = "landscape"      # "portrait" | "landscape"
ws.page_setup.paperSize = ws.PAPERSIZE_A4    # PAPERSIZE_LETTER, PAPERSIZE_A4, PAPERSIZE_A3, etc.
ws.page_setup.fitToWidth = 1                 # Fit to N pages wide
ws.page_setup.fitToHeight = 0                # 0 = unlimited height (fit width only)
ws.page_setup.scale = 85                     # Print scale percentage

# Margins (inches)
ws.page_margins.left = 0.7
ws.page_margins.right = 0.7
ws.page_margins.top = 0.75
ws.page_margins.bottom = 0.75
ws.page_margins.header = 0.3
ws.page_margins.footer = 0.3

# Headers & Footers
ws.oddHeader.center.text = "Report Title"
ws.oddFooter.center.text = "Page &P of &N"  # &P=page number, &N=total pages
ws.oddHeader.left.text = "&D"                # &D=date, &T=time, &F=filename, &A=sheet name
ws.oddHeader.left.font = "Arial,Bold"
ws.oddHeader.left.size = 14
ws.oddHeader.left.color = "FF0000"
ws.evenHeader.center.text = "Even Page Header"
ws.firstHeader.center.text = "First Page Header"

# Print area & page breaks
ws.print_area = "A1:G50"                     # Print area
ws.print_title_rows = "1:2"                  # Repeat rows at top
ws.print_title_cols = "A:B"                  # Repeat columns at left
ws.page_breaks.append(Break(id=20))          # Horizontal page break after row 20

from openpyxl.worksheet.pagebreak import Break, RowBreak, ColBreak
ws.row_breaks.append(Break(id=20))           # Row break
ws.col_breaks.append(Break(id=5))            # Column break
```

## 1.12 Worksheet Protection

```python
ws.protection.sheet = True                   # Enable protection
ws.protection.password = "secret"            # Set password
ws.protection.enable()                       # Shorthand
ws.protection.disable()

# Granular permissions
ws.protection.formatCells = False            # Allow format cells
ws.protection.formatColumns = False          # Allow format columns
ws.protection.formatRows = False             # Allow format rows
ws.protection.insertColumns = False          # Allow insert columns
ws.protection.insertRows = False             # Allow insert rows
ws.protection.insertHyperlinks = False       # Allow insert hyperlinks
ws.protection.deleteColumns = False          # Allow delete columns
ws.protection.deleteRows = False             # Allow delete rows
ws.protection.sort = False                   # Allow sorting
ws.protection.autoFilter = False             # Allow auto-filter
ws.protection.pivotTables = False            # Allow pivot tables
ws.protection.objects = False                # Allow editing objects
ws.protection.scenarios = False              # Allow editing scenarios

# Cell-level protection
from openpyxl.styles import Protection
cell.protection = Protection(locked=True, hidden=False)
```

## 1.13 Freeze Panes

```python
ws.freeze_panes = "B2"                       # Freeze row 1 and column A
ws.freeze_panes = "A2"                       # Freeze row 1 only
ws.freeze_panes = "B1"                       # Freeze column A only
ws.freeze_panes = None                       # Unfreeze
```

## 1.14 Column Width & Row Height

```python
ws.column_dimensions["A"].width = 25         # Character width units
ws.column_dimensions["A"].bestFit = True     # Auto-fit flag (hint only)
ws.column_dimensions["A"].auto_size = True   # Auto-size flag (hint only)
ws.row_dimensions[1].height = 30             # Points

# Hide rows/columns
ws.column_dimensions["C"].hidden = True
ws.row_dimensions[5].hidden = True

# Group rows/columns (outline)
ws.column_dimensions.group("A", "D", outline_level=1, hidden=False)
ws.row_dimensions.group(1, 10, outline_level=1, hidden=False)
```

---

# 2. python-docx (Word .docx)

```python
from docx import Document
from docx.shared import Inches, Cm, Mm, Pt, Emu, Twips, RGBColor
from docx.enum.text import (
    WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT,
    WD_TAB_LEADER, WD_UNDERLINE
)
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL, WD_ROW_HEIGHT_RULE
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
```

## 2.1 Document Operations

```python
doc = Document()                             # Create new (default template)
doc = Document("template.docx")              # Open existing / use as template
doc.save("output.docx")                      # Save to file

# Save to stream (BytesIO)
from io import BytesIO
stream = BytesIO()
doc.save(stream)
stream.seek(0)
```

## 2.2 Paragraphs & Runs

### Add Paragraphs

```python
p = doc.add_paragraph("Text content")        # Add paragraph
p = doc.add_paragraph("Text", style="BodyText")  # With named style
p = doc.add_paragraph()                       # Empty paragraph

# Append text as run within paragraph
run = p.add_run("additional text")
run = p.add_run("bold text")
run.bold = True
```

### Paragraph Format

```python
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

pf = p.paragraph_format

pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
# WD_ALIGN_PARAGRAPH: LEFT, CENTER, RIGHT, JUSTIFY, DISTRIBUTE

pf.left_indent = Inches(0.5)                # Left indent
pf.right_indent = Inches(0.5)               # Right indent
pf.first_line_indent = Inches(0.25)         # First-line indent (positive)
pf.first_line_indent = Inches(-0.25)        # Hanging indent (negative)

pf.space_before = Pt(12)                    # Space before paragraph
pf.space_after = Pt(12)                     # Space after paragraph
pf.line_spacing = Pt(14)                    # Exact line spacing
pf.line_spacing = 1.5                       # Multiple (1.0, 1.5, 2.0, etc.)
pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY       # EXACTLY | AT_LEAST | MULTIPLE
                                             # | SINGLE | DOUBLE | ONE_POINT_FIVE

pf.keep_together = True                      # Keep paragraph on one page
pf.keep_with_next = True                     # Keep with next paragraph
pf.page_break_before = True                  # Page break before paragraph
pf.widow_control = True                      # Prevent widows/orphans

# Tab stops
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
tab_stops = pf.tab_stops
tab_stops.add_tab_stop(Inches(2.0))                                     # Left tab
tab_stops.add_tab_stop(Inches(4.0), WD_TAB_ALIGNMENT.CENTER)            # Center tab
tab_stops.add_tab_stop(Inches(6.0), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)  # Right tab with dots
# WD_TAB_ALIGNMENT: LEFT, CENTER, RIGHT, DECIMAL, BAR, CLEAR, END, NUM
# WD_TAB_LEADER: SPACES, DOTS, DASHES, LINES, HEAVY, MIDDLE_DOT
```

### Run / Font Formatting

```python
run = p.add_run("Formatted text")
font = run.font

font.name = "Arial"                          # Font family
font.size = Pt(12)                           # Point size
font.bold = True                             # bool or None (inherit)
font.italic = True
font.underline = True                        # True for single underline
font.underline = WD_UNDERLINE.DOUBLE         # Specific underline type
# WD_UNDERLINE: NONE, SINGLE, WORDS, DOUBLE, DOTTED, THICK, DASH,
#   DOT_DASH, DOT_DOT_DASH, WAVY, DOTTED_HEAVY, DASH_HEAVY,
#   DOT_DASH_HEAVY, DOT_DOT_DASH_HEAVY, WAVY_HEAVY (14 types)

font.strike = True                           # Strikethrough
font.double_strike = True                    # Double strikethrough
font.subscript = True
font.superscript = True
font.all_caps = True
font.small_caps = True
font.shadow = True
font.outline = True
font.emboss = True
font.imprint = True                          # Engrave
font.hidden = True                           # Hidden text
font.no_proof = True                         # Skip spell check
font.math = True                             # Math mode

font.color.rgb = RGBColor(0xFF, 0x00, 0x00) # RGB color
font.color.theme_color = MSO_THEME_COLOR.ACCENT_1  # Theme color
# MSO_THEME_COLOR: ACCENT_1-6, BACKGROUND_1-2, DARK_1-2, LIGHT_1-2,
#   FOLLOWED_HYPERLINK, HYPERLINK, TEXT_1-2, MIXED

font.highlight_color = WD_COLOR_INDEX.YELLOW
# WD_COLOR_INDEX: AUTO, BLACK, BLUE, BRIGHT_GREEN, DARK_BLUE, DARK_RED,
#   DARK_YELLOW, GRAY_25, GRAY_50, GREEN, PINK, RED, TEAL, TURQUOISE,
#   VIOLET, WHITE, YELLOW
```

## 2.3 Headings & Lists

```python
doc.add_heading("Title", level=0)            # Title (level 0)
doc.add_heading("Heading 1", level=1)        # Heading levels 1-9
doc.add_heading("Heading 2", level=2)

# Bullet lists (use style names)
doc.add_paragraph("Item 1", style="List Bullet")
doc.add_paragraph("Item 1a", style="List Bullet 2")    # Indented
doc.add_paragraph("Item 1ai", style="List Bullet 3")   # Further indented

# Numbered lists
doc.add_paragraph("Step 1", style="List Number")
doc.add_paragraph("Step 1a", style="List Number 2")
doc.add_paragraph("Step 1ai", style="List Number 3")
```

## 2.4 Tables

```python
table = doc.add_table(rows=3, cols=4)        # Create table
table = doc.add_table(rows=3, cols=4, style="Table Grid")  # With style

# Built-in styles: "Table Grid", "Light List", "Light Grid", "Medium Shading 1",
#   "Light Shading - Accent 1", "Colorful Grid - Accent 2", etc.
table.style = "Light Shading - Accent 1"

# Table alignment
table.alignment = WD_TABLE_ALIGNMENT.CENTER  # LEFT | CENTER | RIGHT

# Autofit
table.autofit = True                         # Allow autofit
table.allow_autofit = True                   # Same
```

### Cell Access & Content

```python
cell = table.cell(0, 0)                      # Access cell (row, col) 0-based
cell.text = "Hello"                           # Set text (replaces all content)
cell.text                                     # Read text

# Rich content in cell
p = cell.paragraphs[0]                        # First paragraph in cell
p.text = "Text"
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

cell.add_paragraph("Another paragraph")       # Add paragraph to cell
cell.add_table(2, 2)                          # Nested table in cell
```

### Row & Column Operations

```python
row = table.rows[0]                           # Access row
row.cells                                     # Cells in row
row.height = Inches(0.5)                      # Row height
row.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY  # EXACTLY | AT_LEAST | AUTO

table.add_row()                               # Add row at end
table.add_column(Inches(1.5))                 # Add column with width

col = table.columns[0]                        # Access column
col.width = Inches(2.0)                       # Column width
```

### Merge Cells

```python
cell_a = table.cell(0, 0)
cell_b = table.cell(0, 3)
cell_a.merge(cell_b)                          # Merge from cell_a to cell_b

# Vertical merge
table.cell(0, 0).merge(table.cell(2, 0))     # Merge rows 0-2 in column 0
```

### Cell Formatting

```python
cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER  # TOP | CENTER | BOTTOM

# Borders and shading via direct XML manipulation
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

# Shading
shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="4472C4"/>')
cell._tc.get_or_add_tcPr().append(shading)

# Borders (per-cell via XML)
tc_pr = cell._tc.get_or_add_tcPr()
borders = parse_xml(
    f'<w:tcBorders {nsdecls("w")}>'
    '  <w:top w:val="single" w:sz="12" w:color="000000"/>'
    '  <w:bottom w:val="single" w:sz="12" w:color="000000"/>'
    '  <w:left w:val="single" w:sz="12" w:color="000000"/>'
    '  <w:right w:val="single" w:sz="12" w:color="000000"/>'
    '</w:tcBorders>'
)
tc_pr.append(borders)
# w:val border types: "single","double","dotted","dashed","thick","thinThickSmallGap", etc.
# w:sz = border width in 1/8 pt (e.g., 12 = 1.5pt)
```

## 2.5 Images

```python
doc.add_picture("image.png")                          # Full width
doc.add_picture("image.png", width=Inches(4.0))       # Specify width (auto height)
doc.add_picture("image.png", height=Inches(3.0))      # Specify height (auto width)
doc.add_picture("image.png", width=Inches(4), height=Inches(3))  # Both (may distort)

# From stream
from io import BytesIO
doc.add_picture(BytesIO(image_bytes), width=Inches(4))

# Inline shapes collection
for shape in doc.inline_shapes:
    shape.width = Inches(3)
    shape.height = Inches(2)
```

## 2.6 Sections & Page Layout

```python
section = doc.sections[0]                     # First section (always exists)
section = doc.add_section(WD_SECTION.NEW_PAGE)  # Add new section

# WD_SECTION: NEW_PAGE, CONTINUOUS, EVEN_PAGE, ODD_PAGE, NEW_COLUMN

# Page size
section.page_width = Inches(8.5)             # Letter width
section.page_height = Inches(11)             # Letter height

# Orientation
section.orientation = WD_ORIENT.LANDSCAPE    # PORTRAIT | LANDSCAPE
# When switching orientation, also swap width/height:
section.page_width, section.page_height = section.page_height, section.page_width

# Margins
section.top_margin = Inches(1.0)
section.bottom_margin = Inches(1.0)
section.left_margin = Inches(1.0)
section.right_margin = Inches(1.0)
section.gutter = Inches(0)                   # Gutter margin (binding edge)

# Header/footer distance from edge
section.header_distance = Inches(0.5)
section.footer_distance = Inches(0.5)
```

## 2.7 Headers & Footers

```python
section = doc.sections[0]

# Default header/footer
header = section.header                       # _Header object
footer = section.footer                       # _Footer object

header.is_linked_to_previous                  # bool - linked to previous section
header.is_linked_to_previous = False          # Unlink

# Write to header
p = header.paragraphs[0]                      # First paragraph (always exists)
p.text = "Document Title"
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Multiple paragraphs
header.add_paragraph("Second line")

# Tables in header
header.add_table(1, 3, width=Inches(6))

# Images in header
run = header.paragraphs[0].add_run()
run.add_picture("logo.png", width=Inches(1))

# Different first page
section.different_first_page_header_footer = True
first_header = section.first_page_header      # First page header
first_footer = section.first_page_footer

# Even/odd pages
doc.settings.odd_and_even_pages_header_footer = True
even_header = section.even_page_header
even_footer = section.even_page_footer
```

## 2.8 Breaks

```python
# Page break (within text flow)
doc.add_page_break()

# Or via run
run = p.add_run()
run.add_break(WD_BREAK.PAGE)

from docx.enum.text import WD_BREAK
# WD_BREAK: LINE, PAGE, COLUMN, LINE_CLEAR_LEFT, LINE_CLEAR_RIGHT, LINE_CLEAR_ALL

# Section break (creates new section)
doc.add_section(WD_SECTION.NEW_PAGE)
doc.add_section(WD_SECTION.CONTINUOUS)        # No page break, just new section
doc.add_section(WD_SECTION.EVEN_PAGE)
doc.add_section(WD_SECTION.ODD_PAGE)
```

## 2.9 Hyperlinks

```python
# python-docx has no built-in hyperlink API; use helper via XML:
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import docx.opc.constants

def add_hyperlink(paragraph, url, text, color="0563C1", underline=True):
    """Add a hyperlink to a paragraph."""
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    if color:
        c = OxmlElement("w:color")
        c.set(qn("w:val"), color)
        rPr.append(c)
    if underline:
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rPr.append(u)
    new_run.append(rPr)
    new_run.text = text
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return hyperlink
```

## 2.10 Styles

```python
# Access styles
styles = doc.styles

# Paragraph style
style = styles["Normal"]
style.font.name = "Arial"
style.font.size = Pt(11)
style.paragraph_format.space_after = Pt(6)

# Add new style
from docx.enum.style import WD_STYLE_TYPE
new_style = styles.add_style("CustomHeading", WD_STYLE_TYPE.PARAGRAPH)
new_style.base_style = styles["Heading 1"]
new_style.font.color.rgb = RGBColor(0x00, 0x00, 0x80)
new_style.font.size = Pt(18)

# WD_STYLE_TYPE: PARAGRAPH, CHARACTER, TABLE, LIST

# Character style
char_style = styles.add_style("Emphasis2", WD_STYLE_TYPE.CHARACTER)
char_style.font.italic = True
char_style.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
run = p.add_run("emphasized", style="Emphasis2")

# Table style
table.style = doc.styles["Table Grid"]
```

## 2.11 Core Properties

```python
props = doc.core_properties
props.author = "Author Name"
props.title = "Document Title"
props.subject = "Subject"
props.keywords = "keyword1, keyword2"
props.comments = "Description"
props.category = "Category"
props.content_status = "Draft"               # "Draft" | "Final" | etc.
props.created                                 # datetime (read-only after creation)
props.modified                                # datetime
props.last_modified_by = "Editor Name"
props.revision                                # int
props.version = "1.0"
props.language = "en-US"
props.identifier = "DOC-001"
```

## 2.12 Length Units

```python
from docx.shared import Inches, Cm, Mm, Pt, Emu, Twips

Inches(1)         # 914400 EMU
Cm(2.54)          # 914400 EMU
Mm(25.4)          # 914400 EMU
Pt(72)            # 914400 EMU
Emu(914400)       # 1 inch
Twips(1440)       # 914400 EMU (1 inch = 1440 twips)

# All return Emu-compatible Length objects usable for any dimension property
```

---

# 3. python-pptx (PowerPoint .pptx)

```python
from pptx import Presentation
from pptx.util import Inches, Cm, Mm, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
```

## 3.1 Presentation & Slides

```python
prs = Presentation()                          # Create new (default template)
prs = Presentation("template.pptx")          # Open existing

# Slide dimensions
prs.slide_width = Inches(13.333)             # Widescreen 16:9
prs.slide_height = Inches(7.5)
prs.slide_width = Inches(10)                 # Standard 4:3
prs.slide_height = Inches(7.5)

# Slide layouts
slide_layouts = prs.slide_layouts             # Collection
layout = prs.slide_layouts[0]                 # By index
layout.name                                   # Layout name (e.g., "Title Slide")
# Common layouts by index (default template):
# 0=Title Slide, 1=Title and Content, 2=Section Header,
# 3=Two Content, 4=Comparison, 5=Title Only, 6=Blank,
# 7=Content with Caption, 8=Picture with Caption

# Slide masters
prs.slide_masters                             # SlideMaster collection
prs.slide_masters[0].slide_layouts            # Layouts for this master

# Add slide
slide = prs.slides.add_slide(layout)

# Notes slide
notes_slide = slide.notes_slide
notes_tf = notes_slide.notes_text_frame
notes_tf.text = "Speaker notes here"

# Save
prs.save("output.pptx")

# Save to stream
from io import BytesIO
stream = BytesIO()
prs.save(stream)
```

## 3.2 Shapes

### Common Shape Properties

```python
shape.left = Inches(1.0)                     # X position from left edge
shape.top = Inches(1.0)                      # Y position from top edge
shape.width = Inches(5.0)                    # Width
shape.height = Inches(3.0)                   # Height
shape.rotation = 45.0                        # Rotation in degrees (clockwise)
shape.name = "MyShape"                       # Shape name (string)
shape.shape_id                                # Unique ID (int, read-only)
shape.shape_type                              # MSO_SHAPE_TYPE enum (read-only)
```

### AutoShape

```python
from pptx.enum.shapes import MSO_SHAPE

shape = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE,                     # Shape type (187 presets, see below)
    left=Inches(1), top=Inches(1),
    width=Inches(3), height=Inches(2),
)

# Common MSO_SHAPE values:
# RECTANGLE, ROUNDED_RECTANGLE, OVAL, DIAMOND, TRIANGLE,
# RIGHT_TRIANGLE, PARALLELOGRAM, TRAPEZOID, PENTAGON, HEXAGON,
# OCTAGON, CROSS, STAR_5_POINT, STAR_6_POINT, STAR_4_POINT,
# HEART, LIGHTNING_BOLT, SUN, MOON, CLOUD,
# RIGHT_ARROW, LEFT_ARROW, UP_ARROW, DOWN_ARROW,
# LEFT_RIGHT_ARROW, UP_DOWN_ARROW, CURVED_RIGHT_ARROW,
# CHEVRON, CALLOUT_1, CALLOUT_2, CALLOUT_3,
# ROUNDED_RECTANGLE_CALLOUT, OVAL_CALLOUT, CLOUD_CALLOUT,
# FLOWCHART_PROCESS, FLOWCHART_DECISION, FLOWCHART_DATA,
# FLOWCHART_TERMINATOR, FLOWCHART_DOCUMENT, etc.
# See full list: pptx.enum.shapes.MSO_SHAPE (187 members)
```

### TextBox

```python
txBox = slide.shapes.add_textbox(
    left=Inches(1), top=Inches(1),
    width=Inches(5), height=Inches(1),
)
tf = txBox.text_frame
tf.text = "Hello"                             # Set text (first paragraph)
```

### Picture

```python
pic = slide.shapes.add_picture(
    "image.png",                              # File path or stream
    left=Inches(1), top=Inches(1),
    width=Inches(4),                          # Optional (preserves aspect if only one)
    height=Inches(3),                         # Optional
)

# Crop (proportional values 0.0-1.0)
pic.crop_left = 0.1
pic.crop_right = 0.1
pic.crop_top = 0.05
pic.crop_bottom = 0.05

# Insert into placeholder
placeholder = slide.placeholders[1]           # Content placeholder
placeholder.insert_picture("image.png")
```

### Table

```python
table_shape = slide.shapes.add_table(
    rows=4, cols=3,
    left=Inches(1), top=Inches(2),
    width=Inches(8), height=Inches(3),
)
table = table_shape.table

# Cell access
cell = table.cell(0, 0)                      # (row, col) 0-based
cell.text = "Header"                          # Set text
cell.text_frame                               # Access TextFrame for rich formatting

# Merge cells
cell.merge(table.cell(0, 2))                 # Merge cell(0,0) through cell(0,2)

# Banding
table.first_row = True                       # Special formatting for first row
table.last_row = False
table.first_col = False
table.last_col = False
table.horz_banding = True                    # Horizontal banding
table.vert_banding = False                   # Vertical banding

# Column widths / row heights
table.columns[0].width = Inches(2)
table.rows[0].height = Inches(0.5)

# Cell formatting
cell.fill.solid()
cell.fill.fore_color.rgb = RGBColor(0x44, 0x72, 0xC4)
cell.vertical_anchor = MSO_ANCHOR.MIDDLE     # TOP | MIDDLE | BOTTOM
cell.margin_left = Inches(0.05)
cell.margin_right = Inches(0.05)
cell.margin_top = Inches(0.02)
cell.margin_bottom = Inches(0.02)
```

### Group Shape

```python
from pptx.enum.shapes import MSO_SHAPE_TYPE

group = slide.shapes.add_group_shape()
group.left = Inches(1)
group.top = Inches(1)
# Shapes within the group (via XML manipulation for complex groups)
# group.shapes returns GroupShapes collection
```

### Connector

```python
connector = slide.shapes.add_connector(
    connector_type=1,                         # 1=straight, 2=elbow, 3=curved
    begin_x=Inches(1), begin_y=Inches(1),
    end_x=Inches(5), end_y=Inches(3),
)
connector.begin_connect(shape1, 0)           # Connect to shape1, connection point 0
connector.end_connect(shape2, 2)             # Connect to shape2, connection point 2
```

### Freeform

```python
builder = slide.shapes.build_freeform(
    start_x=Inches(1), start_y=Inches(1),
)
builder.add_line_segments([
    (Inches(3), Inches(1)),                  # (x, y) tuples
    (Inches(3), Inches(3)),
    (Inches(1), Inches(3)),
])
builder.close()                              # Close the shape path
freeform = builder.convert_to_shape()
```

## 3.3 Text Frames & Formatting

### TextFrame

```python
tf = shape.text_frame

tf.text = "Simple text"                       # Set all text (single paragraph)
tf.paragraphs                                 # List of Paragraph objects (always >= 1)

tf.word_wrap = True                           # Enable word wrap
tf.auto_size = MSO_AUTO_SIZE.NONE             # No auto-size
tf.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT  # Resize shape to fit text
tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE  # Shrink text to fit shape

tf.margin_left = Inches(0.1)                 # Internal margins
tf.margin_right = Inches(0.1)
tf.margin_top = Inches(0.05)
tf.margin_bottom = Inches(0.05)
```

### Paragraph

```python
p = tf.paragraphs[0]                         # First paragraph
p = tf.add_paragraph()                        # Add new paragraph

p.text = "Text"                               # Set paragraph text
p.alignment = PP_ALIGN.CENTER
# PP_ALIGN: LEFT, CENTER, RIGHT, JUSTIFY, DISTRIBUTE,
#   JUSTIFY_LOW, THAI_DISTRIBUTE (+ others)

p.level = 0                                  # Indentation level (0-8)
p.space_before = Pt(6)                       # Space before (Pt or Emu)
p.space_after = Pt(6)                        # Space after
p.line_spacing = Pt(18)                      # Exact line spacing
p.line_spacing = 1.5                         # Multiple (float)

p.font                                        # Default font for paragraph (inherited by runs)
```

### Run

```python
run = p.add_run()
run.text = "Formatted text"

# Hyperlink
run.hyperlink.address = "https://example.com"

# Font (same properties for paragraph.font and run.font)
font = run.font
font.name = "Arial"
font.size = Pt(14)
font.bold = True
font.italic = True
font.underline = True                         # True | False | None (inherit)
# Additional underline types via XML: "sng","dbl","heavy","dotted","dash","dashHeavy", etc.
font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
font.color.theme_color = MSO_THEME_COLOR.ACCENT_1
font.color.brightness = -0.25               # -1.0 (darker) to 1.0 (lighter), for theme colors
```

## 3.4 Charts

```python
from pptx.chart.data import (
    CategoryChartData, XyChartData, BubbleChartData
)
from pptx.enum.chart import (
    XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION,
    XL_TICK_MARK, XL_TICK_LABEL_POSITION
)
```

### Create a Chart

```python
chart_data = CategoryChartData()
chart_data.categories = ["Q1", "Q2", "Q3", "Q4"]
chart_data.add_series("2024", (100, 150, 130, 170))
chart_data.add_series("2025", (120, 160, 140, 190))

chart_frame = slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED,           # Chart type enum
    left=Inches(1), top=Inches(2),
    width=Inches(8), height=Inches(4.5),
    chart_data=chart_data,
)
chart = chart_frame.chart
```

### Chart Types (XL_CHART_TYPE)

```python
# Bar / Column
XL_CHART_TYPE.BAR_CLUSTERED                   # Horizontal bars
XL_CHART_TYPE.BAR_STACKED
XL_CHART_TYPE.BAR_STACKED_100
XL_CHART_TYPE.COLUMN_CLUSTERED                # Vertical columns
XL_CHART_TYPE.COLUMN_STACKED
XL_CHART_TYPE.COLUMN_STACKED_100
XL_CHART_TYPE.THREE_D_BAR_CLUSTERED
XL_CHART_TYPE.THREE_D_BAR_STACKED
XL_CHART_TYPE.THREE_D_BAR_STACKED_100
XL_CHART_TYPE.THREE_D_COLUMN
XL_CHART_TYPE.THREE_D_COLUMN_CLUSTERED
XL_CHART_TYPE.THREE_D_COLUMN_STACKED
XL_CHART_TYPE.THREE_D_COLUMN_STACKED_100

# Line
XL_CHART_TYPE.LINE
XL_CHART_TYPE.LINE_MARKERS
XL_CHART_TYPE.LINE_MARKERS_STACKED
XL_CHART_TYPE.LINE_MARKERS_STACKED_100
XL_CHART_TYPE.LINE_STACKED
XL_CHART_TYPE.LINE_STACKED_100
XL_CHART_TYPE.THREE_D_LINE

# Pie / Doughnut
XL_CHART_TYPE.PIE
XL_CHART_TYPE.PIE_EXPLODED
XL_CHART_TYPE.THREE_D_PIE
XL_CHART_TYPE.THREE_D_PIE_EXPLODED
XL_CHART_TYPE.DOUGHNUT
XL_CHART_TYPE.DOUGHNUT_EXPLODED

# Area
XL_CHART_TYPE.AREA
XL_CHART_TYPE.AREA_STACKED
XL_CHART_TYPE.AREA_STACKED_100
XL_CHART_TYPE.THREE_D_AREA
XL_CHART_TYPE.THREE_D_AREA_STACKED
XL_CHART_TYPE.THREE_D_AREA_STACKED_100

# Scatter / XY
XL_CHART_TYPE.XY_SCATTER
XL_CHART_TYPE.XY_SCATTER_LINES
XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS
XL_CHART_TYPE.XY_SCATTER_SMOOTH
XL_CHART_TYPE.XY_SCATTER_SMOOTH_NO_MARKERS

# Bubble
XL_CHART_TYPE.BUBBLE
XL_CHART_TYPE.BUBBLE_THREE_D_EFFECT

# Radar
XL_CHART_TYPE.RADAR
XL_CHART_TYPE.RADAR_FILLED
XL_CHART_TYPE.RADAR_MARKERS
```

### XY / Scatter Chart Data

```python
chart_data = XyChartData()
series = chart_data.add_series("Series 1")
series.add_data_point(1.0, 2.5)
series.add_data_point(2.0, 4.1)
series.add_data_point(3.0, 3.7)
```

### Bubble Chart Data

```python
chart_data = BubbleChartData()
series = chart_data.add_series("Series 1")
series.add_data_point(1.0, 2.5, 10)         # x, y, size
series.add_data_point(2.0, 4.1, 20)
```

### Chart Title

```python
chart.has_title = True
chart.chart_title.has_text_frame = True
chart.chart_title.text_frame.text = "Sales Report"
chart.chart_title.text_frame.paragraphs[0].font.size = Pt(18)
```

### Legend

```python
chart.has_legend = True
chart.legend.position = XL_LEGEND_POSITION.BOTTOM
# XL_LEGEND_POSITION: BOTTOM, CORNER, CUSTOM, LEFT, RIGHT, TOP
chart.legend.include_in_layout = False       # Don't overlap chart area
chart.legend.font.size = Pt(10)
```

### Axes

```python
# Value axis (y)
value_axis = chart.value_axis
value_axis.has_title = True
value_axis.axis_title.text_frame.text = "Revenue ($)"
value_axis.minimum_scale = 0
value_axis.maximum_scale = 200
value_axis.major_unit = 50
value_axis.minor_unit = 25
value_axis.has_major_gridlines = True
value_axis.has_minor_gridlines = False
value_axis.major_tick_mark = XL_TICK_MARK.OUTSIDE   # CROSS | INSIDE | OUTSIDE | NONE
value_axis.minor_tick_mark = XL_TICK_MARK.NONE
value_axis.tick_label_position = XL_TICK_LABEL_POSITION.NEXT_TO_AXIS
# XL_TICK_LABEL_POSITION: HIGH, LOW, NEXT_TO_AXIS, NONE
value_axis.visible = True
value_axis.format.line.fill.background()     # Hide axis line

# Category axis (x)
category_axis = chart.category_axis
category_axis.has_title = True
category_axis.axis_title.text_frame.text = "Quarter"
category_axis.tick_labels.font.size = Pt(10)
category_axis.tick_labels.number_format = "0%"
category_axis.tick_labels.number_format_is_linked = False
```

### Data Labels

```python
plot = chart.plots[0]
plot.has_data_labels = True
data_labels = plot.data_labels
data_labels.font.size = Pt(9)
data_labels.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
data_labels.number_format = "$#,##0"
data_labels.number_format_is_linked = False
data_labels.show_category_name = False
data_labels.show_legend_key = False
data_labels.show_percentage = False           # For pie/doughnut
data_labels.show_series_name = False
data_labels.show_value = True
data_labels.label_position = XL_LABEL_POSITION.OUTSIDE_END
# XL_LABEL_POSITION: ABOVE, BELOW, BEST_FIT, CENTER, INSIDE_BASE,
#   INSIDE_END, LEFT, MIXED, OUTSIDE_END, RIGHT
```

### Series Formatting

```python
series = chart.series[0]
series.format.fill.solid()
series.format.fill.fore_color.rgb = RGBColor(0x44, 0x72, 0xC4)

series.format.line.color.rgb = RGBColor(0x00, 0x00, 0x00)
series.format.line.width = Pt(1.5)

series.smooth = True                          # Smooth line (line charts)

# Individual point formatting
point = series.points[0]
point.format.fill.solid()
point.format.fill.fore_color.rgb = RGBColor(0xFF, 0x00, 0x00)

# Gap & overlap (bar/column only)
plot = chart.plots[0]
plot.gap_width = 150                          # Gap width (percent, 0-500)
plot.overlap = 0                              # Overlap (-100 to 100)
```

## 3.5 Fill & Line Formatting

### FillFormat

```python
# Solid fill
shape.fill.solid()
shape.fill.fore_color.rgb = RGBColor(0x44, 0x72, 0xC4)
shape.fill.fore_color.theme_color = MSO_THEME_COLOR.ACCENT_1
shape.fill.fore_color.brightness = 0.4       # Lighter tint

# Gradient fill
shape.fill.gradient()
shape.fill.gradient_angle = 45               # Degrees
shape.fill.gradient_stops[0].color.rgb = RGBColor(0xFF, 0x00, 0x00)
shape.fill.gradient_stops[0].position = 0.0  # 0.0 to 1.0
shape.fill.gradient_stops[1].color.rgb = RGBColor(0x00, 0x00, 0xFF)
shape.fill.gradient_stops[1].position = 1.0

# Pattern fill
shape.fill.patterned()
shape.fill.pattern = MSO_PATTERN.CROSS        # See MSO_PATTERN enum
shape.fill.fore_color.rgb = RGBColor(0x00, 0x00, 0x00)
shape.fill.back_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

# Picture fill (from image file)
shape.fill.picture()
# (requires XML-level manipulation to set the image)

# No fill (transparent)
shape.fill.background()

# Transparent
shape.fill.solid()
shape.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
# Alpha via XML: shape.fill._fill element
```

### LineFormat

```python
shape.line.color.rgb = RGBColor(0x00, 0x00, 0x00)
shape.line.color.theme_color = MSO_THEME_COLOR.ACCENT_1
shape.line.width = Pt(2.0)                   # Line width
shape.line.fill.background()                 # No line (transparent)
shape.line.fill.solid()                      # Solid line

shape.line.dash_style = MSO_LINE_DASH_STYLE.DASH
# MSO_LINE_DASH_STYLE: SOLID, ROUND_DOT, SQUARE_DOT, DASH, DASH_DOT,
#   LONG_DASH, LONG_DASH_DOT, LONG_DASH_DOT_DOT, DASH_STYLE_MIXED,
#   SYSTEM_DASH, SYSTEM_DOT, SYSTEM_DASH_DOT
```

## 3.6 Placeholders

```python
# Access placeholders on slide
for ph in slide.placeholders:
    print(ph.placeholder_format.idx, ph.name, ph.placeholder_format.type)

# Common placeholder types (MSO_PLACEHOLDER):
# TITLE (0), BODY (1/13), CENTER_TITLE (3), SUBTITLE (4),
# DATE (10), SLIDE_NUMBER (12), FOOTER (11),
# OBJECT (7), TABLE (12), CHART (13), ORG_CHART (14),
# MEDIA_CLIP (16), PICTURE (18), BITMAP (9),
# VERTICAL_BODY (14), VERTICAL_OBJECT (15), VERTICAL_TITLE (16)

# Access by index
title = slide.placeholders[0]
title.text = "Slide Title"

body = slide.placeholders[1]
tf = body.text_frame
tf.text = "First bullet"
tf.add_paragraph().text = "Second bullet"

# Insert picture into picture placeholder
pic_ph = slide.placeholders[1]               # Must be a picture placeholder
pic_ph.insert_picture("image.png")
```

## 3.7 Slide Background

```python
background = slide.background
fill = background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0xF0, 0xF0, 0xF0)

# Gradient background
fill.gradient()
fill.gradient_stops[0].color.rgb = RGBColor(0x00, 0x00, 0x80)
fill.gradient_stops[1].color.rgb = RGBColor(0x00, 0x00, 0x00)
```

## 3.8 Hyperlinks & Click Actions

```python
# Hyperlink on a run
run.hyperlink.address = "https://example.com"

# Click action on shape
shape.click_action.hyperlink.address = "https://example.com"
shape.click_action.target_slide = prs.slides[2]  # Link to specific slide
```

## 3.9 OLE Embedding & Media

```python
# Embed video (via XML-level manipulation)
# python-pptx has limited native support for media;
# use slide.shapes._spTree to add media elements via lxml

# For basic movie placeholder usage:
# Requires manipulating the XML directly — use pptx.oxml helpers
```

## 3.10 Core Properties

```python
props = prs.core_properties
props.author = "Author Name"
props.title = "Presentation Title"
props.subject = "Subject"
props.keywords = "keyword1, keyword2"
props.comments = "Description"
props.category = "Category"
props.content_status = "Draft"
props.last_modified_by = "Editor"
props.revision = 1                            # int
props.created                                 # datetime
props.modified                                # datetime
```

## 3.11 Length Units

```python
from pptx.util import Inches, Cm, Mm, Pt, Emu

Inches(1)         # 914400 EMU
Cm(2.54)          # 914400 EMU
Mm(25.4)          # 914400 EMU
Pt(72)            # 914400 EMU
Emu(914400)       # Direct EMU value

# All dimension properties accept these Length objects
```

---

# Quick Reference: Import Cheat Sheet

```python
# ---- openpyxl ----
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, GradientFill, Border, Side, Alignment, Protection, NamedStyle
from openpyxl.styles.colors import Color
from openpyxl.styles.numbers import FORMAT_PERCENTAGE, FORMAT_NUMBER_COMMA_SEPARATED1
from openpyxl.formatting.rule import CellIsRule, FormulaRule, ColorScaleRule, DataBarRule, IconSetRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.worksheet.pagebreak import Break
from openpyxl.chart import BarChart, LineChart, PieChart, ScatterChart, AreaChart, Reference, Series
from openpyxl.chart.axis import DateAxis, NumericAxis
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.trendline import Trendline
from openpyxl.chart.legend import Legend
from openpyxl.drawing.image import Image
from openpyxl.comments import Comment
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.workbook.defined_name import DefinedName

# ---- python-docx ----
from docx import Document
from docx.shared import Inches, Cm, Mm, Pt, Emu, Twips, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK, WD_UNDERLINE, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL, WD_ROW_HEIGHT_RULE
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.dml import MSO_THEME_COLOR
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml, OxmlElement

# ---- python-pptx ----
from pptx import Presentation
from pptx.util import Inches, Cm, Mm, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_TICK_MARK, XL_TICK_LABEL_POSITION
from pptx.enum.dml import MSO_THEME_COLOR, MSO_LINE_DASH_STYLE, MSO_PATTERN
from pptx.chart.data import CategoryChartData, XyChartData, BubbleChartData
```
