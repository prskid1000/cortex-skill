# Image Processing Examples

Working code blocks for Pillow (Python) and ImageMagick (CLI).

---

## Pillow (Python)

### Open, Resize, Save in Different Format

```python
from PIL import Image

img = Image.open("/tmp/input.png")
img_resized = img.resize((800, 600), Image.LANCZOS)
img_resized.save("/tmp/output.jpg", "JPEG", quality=90)
```

### Crop, Rotate, Flip

```python
from PIL import Image

img = Image.open("/tmp/input.jpg")

# Crop (left, upper, right, lower)
cropped = img.crop((100, 100, 500, 400))
cropped.save("/tmp/cropped.jpg")

# Rotate 45 degrees (expand canvas to fit)
rotated = img.rotate(45, expand=True, fillcolor="white")
rotated.save("/tmp/rotated.jpg")

# Flip horizontally / vertically
flipped_h = img.transpose(Image.FLIP_LEFT_RIGHT)
flipped_v = img.transpose(Image.FLIP_TOP_BOTTOM)
flipped_h.save("/tmp/flipped_h.jpg")
flipped_v.save("/tmp/flipped_v.jpg")
```

### Text Watermark

```python
from PIL import Image, ImageDraw, ImageFont

img = Image.open("/tmp/input.jpg").convert("RGBA")
txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
draw = ImageDraw.Draw(txt_layer)

# Use a truetype font (or default if unavailable)
try:
    font = ImageFont.truetype("arial.ttf", 48)
except OSError:
    font = ImageFont.load_default()

# Semi-transparent white text, bottom-right
text = "SAMPLE"
bbox = draw.textbbox((0, 0), text, font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
x = img.width - tw - 20
y = img.height - th - 20
draw.text((x, y), text, fill=(255, 255, 255, 128), font=font)

result = Image.alpha_composite(img, txt_layer)
result.convert("RGB").save("/tmp/watermarked.jpg")
```

### Logo Overlay (Paste with Alpha)

```python
from PIL import Image

base = Image.open("/tmp/photo.jpg").convert("RGBA")
logo = Image.open("/tmp/logo.png").convert("RGBA")

# Resize logo to 1/5 of base width
logo_w = base.width // 5
logo_h = int(logo.height * (logo_w / logo.width))
logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

# Paste at bottom-right with alpha mask
position = (base.width - logo_w - 10, base.height - logo_h - 10)
base.paste(logo, position, logo)  # third arg = alpha mask
base.convert("RGB").save("/tmp/with_logo.jpg")
```

### Filters: Blur, Sharpen, Edge Detect

```python
from PIL import Image, ImageFilter

img = Image.open("/tmp/input.jpg")

blurred = img.filter(ImageFilter.GaussianBlur(radius=5))
blurred.save("/tmp/blurred.jpg")

sharpened = img.filter(ImageFilter.SHARPEN)
sharpened.save("/tmp/sharpened.jpg")

edges = img.filter(ImageFilter.FIND_EDGES)
edges.save("/tmp/edges.jpg")

embossed = img.filter(ImageFilter.EMBOSS)
embossed.save("/tmp/embossed.jpg")

# Custom kernel
kernel = ImageFilter.Kernel(
    size=(3, 3),
    kernel=[0, -1, 0, -1, 5, -1, 0, -1, 0],
    scale=1, offset=0
)
custom = img.filter(kernel)
custom.save("/tmp/custom_filter.jpg")
```

### Enhance: Brightness, Contrast, Color, Sharpness

```python
from PIL import Image, ImageEnhance

img = Image.open("/tmp/input.jpg")

# Each factor: 1.0 = original, <1.0 = less, >1.0 = more
ImageEnhance.Brightness(img).enhance(1.3).save("/tmp/bright.jpg")
ImageEnhance.Contrast(img).enhance(1.5).save("/tmp/contrast.jpg")
ImageEnhance.Color(img).enhance(1.4).save("/tmp/saturated.jpg")
ImageEnhance.Sharpness(img).enhance(2.0).save("/tmp/sharp.jpg")
```

### ImageOps: Autocontrast, Equalize, Posterize, Pad/Contain/Cover

```python
from PIL import Image, ImageOps

img = Image.open("/tmp/input.jpg")

ImageOps.autocontrast(img, cutoff=1).save("/tmp/autocontrast.jpg")
ImageOps.equalize(img).save("/tmp/equalized.jpg")
ImageOps.posterize(img, bits=3).save("/tmp/posterized.jpg")

# Pad to exact size with letterboxing
padded = ImageOps.pad(img, (800, 800), color="black", centering=(0.5, 0.5))
padded.save("/tmp/padded.jpg")

# Contain (fit within box, preserve aspect ratio)
contained = ImageOps.contain(img, (800, 800))
contained.save("/tmp/contained.jpg")

# Cover (fill box, crop excess)
covered = ImageOps.cover(img, (800, 800))
covered.save("/tmp/covered.jpg")
```

### Create Diagram from Scratch

```python
from PIL import Image, ImageDraw, ImageFont

width, height = 800, 600
img = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(img)

try:
    font = ImageFont.truetype("arial.ttf", 16)
    title_font = ImageFont.truetype("arial.ttf", 24)
except OSError:
    font = ImageFont.load_default()
    title_font = font

# Title
draw.text((width // 2 - 80, 20), "System Diagram", fill="black", font=title_font)

# Boxes
boxes = [
    ((50, 100, 200, 180), "Client", "#4A90D9"),
    ((300, 100, 500, 180), "API Server", "#E67E22"),
    ((550, 100, 750, 180), "Database", "#27AE60"),
]
for (x1, y1, x2, y2), label, color in boxes:
    draw.rounded_rectangle([x1, y1, x2, y2], radius=10, fill=color, outline="black", width=2)
    tw = draw.textlength(label, font=font)
    draw.text(((x1 + x2 - tw) / 2, (y1 + y2) / 2 - 8), label, fill="white", font=font)

# Arrows
draw.line([(200, 140), (300, 140)], fill="black", width=2)
draw.polygon([(295, 135), (300, 140), (295, 145)], fill="black")
draw.line([(500, 140), (550, 140)], fill="black", width=2)
draw.polygon([(545, 135), (550, 140), (545, 145)], fill="black")

img.save("/tmp/diagram.png")
```

### Batch Resize (Process Directory)

```python
from PIL import Image
from pathlib import Path

input_dir = Path("/tmp/photos")
output_dir = Path("/tmp/photos_resized")
output_dir.mkdir(exist_ok=True)

max_size = (1024, 1024)

for f in input_dir.glob("*"):
    if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        img = Image.open(f)
        img.thumbnail(max_size, Image.LANCZOS)  # in-place, preserves aspect ratio
        out_path = output_dir / f.name
        img.save(out_path, quality=85)
        print(f"Resized {f.name} -> {img.size}")
```

### Animated GIF Creation from Frames

```python
from PIL import Image
from pathlib import Path

frames = []
for f in sorted(Path("/tmp/frames").glob("frame_*.png")):
    frames.append(Image.open(f).convert("RGBA"))

if frames:
    frames[0].save(
        "/tmp/animation.gif",
        save_all=True,
        append_images=frames[1:],
        duration=100,       # ms per frame
        loop=0,             # 0 = infinite loop
        optimize=True,
    )
```

### EXIF Data Reading and Auto-Rotation

```python
from PIL import Image, ExifTags
from PIL.ImageOps import exif_transpose

img = Image.open("/tmp/photo.jpg")

# Read EXIF data
exif_data = img.getexif()
for tag_id, value in exif_data.items():
    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
    print(f"{tag_name}: {value}")

# Auto-rotate based on EXIF orientation
img_corrected = exif_transpose(img)
img_corrected.save("/tmp/photo_corrected.jpg")
```

### Color Channel Operations

```python
from PIL import Image

img = Image.open("/tmp/input.jpg")

# Split into channels
r, g, b = img.split()

# Save individual channels as grayscale
r.save("/tmp/red_channel.jpg")
g.save("/tmp/green_channel.jpg")
b.save("/tmp/blue_channel.jpg")

# Merge channels back (swap red and blue)
swapped = Image.merge("RGB", (b, g, r))
swapped.save("/tmp/swapped_channels.jpg")

# Convert to grayscale
gray = img.convert("L")
gray.save("/tmp/grayscale.jpg")
```

### Thumbnail Generation

```python
from PIL import Image

img = Image.open("/tmp/input.jpg")

# thumbnail() modifies in-place, preserves aspect ratio, never upscales
img.thumbnail((256, 256), Image.LANCZOS)
img.save("/tmp/thumbnail.jpg", quality=85)
```

### Format Conversion (PNG to JPEG, WebP, etc.)

```python
from PIL import Image

img = Image.open("/tmp/input.png")

# PNG -> JPEG (must convert RGBA to RGB first)
if img.mode == "RGBA":
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img, mask=img.split()[3])
    img = bg
img.save("/tmp/output.jpg", "JPEG", quality=90)

# To WebP
img.save("/tmp/output.webp", "WEBP", quality=85)

# To BMP
img.save("/tmp/output.bmp", "BMP")

# To TIFF
img.save("/tmp/output.tiff", "TIFF")
```

---

## ImageMagick (`magick` CLI)

### Resize, Crop, Rotate

```bash
# Resize to 800x600 (may distort aspect ratio)
magick /tmp/input.jpg -resize 800x600! /tmp/resized.jpg

# Resize to fit within 800x600 (preserve aspect ratio)
magick /tmp/input.jpg -resize 800x600 /tmp/resized.jpg

# Resize by percentage
magick /tmp/input.jpg -resize 50% /tmp/half.jpg

# Crop 400x300 starting at offset +100+50
magick /tmp/input.jpg -crop 400x300+100+50 +repage /tmp/cropped.jpg

# Rotate 90 degrees clockwise
magick /tmp/input.jpg -rotate 90 /tmp/rotated.jpg

# Auto-orient based on EXIF
magick /tmp/input.jpg -auto-orient /tmp/oriented.jpg
```

### Format Conversion (including PDF to PNG)

```bash
# JPEG to PNG
magick /tmp/input.jpg /tmp/output.png

# PNG to WebP
magick /tmp/input.png -quality 85 /tmp/output.webp

# PDF to PNG (one image per page, 300 DPI)
magick -density 300 /tmp/document.pdf /tmp/page_%03d.png

# SVG to PNG at specific size
magick -density 300 /tmp/input.svg -resize 1024x1024 /tmp/output.png
```

### Add Border, Trim Whitespace

```bash
# Add a 10px red border
magick /tmp/input.jpg -bordercolor red -border 10 /tmp/bordered.jpg

# Add rounded-corner border
magick /tmp/input.jpg -border 20 -bordercolor white \
  \( +clone -alpha extract -draw "roundrectangle 0,0,%[fx:w-1],%[fx:h-1],15,15" \) \
  -alpha off -compose CopyOpacity -composite /tmp/rounded.png

# Trim whitespace around content
magick /tmp/input.png -trim +repage /tmp/trimmed.png

# Trim with fuzz tolerance (for near-white edges)
magick /tmp/input.png -fuzz 10% -trim +repage /tmp/trimmed.png
```

### Text Annotation

```bash
# Add text at bottom
magick /tmp/input.jpg -gravity South -pointsize 36 \
  -fill white -stroke black -strokewidth 1 \
  -annotate +0+10 "Sample Text" /tmp/annotated.jpg

# Add text with background box
magick /tmp/input.jpg -gravity North -pointsize 24 \
  -fill white -undercolor "rgba(0,0,0,0.6)" \
  -annotate +0+10 " Title Text " /tmp/titled.jpg
```

### Composite / Overlay Images

```bash
# Overlay logo at bottom-right with 50% opacity
magick /tmp/photo.jpg /tmp/logo.png -gravity SouthEast \
  -geometry 200x200+10+10 -compose Over -composite /tmp/overlaid.jpg

# Overlay with transparency
magick /tmp/photo.jpg \( /tmp/logo.png -alpha set -channel A -evaluate set 50% \) \
  -gravity SouthEast -geometry +10+10 -composite /tmp/overlaid.jpg
```

### Montage (Grid of Images)

```bash
# 3-column grid with labels
magick montage /tmp/img1.jpg /tmp/img2.jpg /tmp/img3.jpg \
  /tmp/img4.jpg /tmp/img5.jpg /tmp/img6.jpg \
  -tile 3x -geometry 300x300+5+5 -background white \
  /tmp/montage.jpg

# Grid with filenames as labels
magick montage /tmp/photos/*.jpg -tile 4x -geometry 200x200+2+2 \
  -label "%f" -pointsize 12 /tmp/contact_sheet.jpg
```

### Batch Convert (mogrify)

```bash
# Convert all PNGs to JPEG in-place
magick mogrify -format jpg /tmp/images/*.png

# Resize all JPEGs to max 1024px wide (in-place)
magick mogrify -resize 1024x /tmp/images/*.jpg

# Batch convert to output directory
mkdir -p /tmp/converted
magick mogrify -format webp -path /tmp/converted /tmp/images/*.jpg
```

### Color Adjustments

```bash
# Brightness +20%, contrast +10%
magick /tmp/input.jpg -brightness-contrast 20x10 /tmp/adjusted.jpg

# Levels (stretch histogram)
magick /tmp/input.jpg -level 10%,90% /tmp/levels.jpg

# Gamma correction
magick /tmp/input.jpg -gamma 1.2 /tmp/gamma.jpg

# Grayscale
magick /tmp/input.jpg -colorspace Gray /tmp/gray.jpg

# Sepia tone
magick /tmp/input.jpg -sepia-tone 80% /tmp/sepia.jpg

# Negate (invert colors)
magick /tmp/input.jpg -negate /tmp/negated.jpg
```

### Effects

```bash
# Gaussian blur
magick /tmp/input.jpg -blur 0x5 /tmp/blurred.jpg

# Sharpen
magick /tmp/input.jpg -sharpen 0x2 /tmp/sharpened.jpg

# Charcoal sketch
magick /tmp/input.jpg -charcoal 2 /tmp/charcoal.jpg

# Pencil sketch
magick /tmp/input.jpg -sketch 0x20+120 /tmp/sketch.jpg

# Oil paint
magick /tmp/input.jpg -paint 4 /tmp/oilpaint.jpg

# Vignette
magick /tmp/input.jpg -vignette 0x40 /tmp/vignette.jpg
```

### Compare Two Images

```bash
# Visual diff (outputs red pixels where different)
magick compare /tmp/image_a.png /tmp/image_b.png /tmp/diff.png

# Get numerical difference metric
magick compare -metric RMSE /tmp/image_a.png /tmp/image_b.png null: 2>&1
```

### Strip Metadata, Add ICC Profile

```bash
# Strip all metadata
magick /tmp/input.jpg -strip /tmp/stripped.jpg

# Add sRGB ICC profile
magick /tmp/input.jpg -profile /tmp/sRGB.icc /tmp/profiled.jpg

# Convert color profile
magick /tmp/input.jpg -profile /tmp/sRGB.icc -profile /tmp/AdobeRGB.icc /tmp/converted.jpg
```

### Create Animated GIF from Images

```bash
# Create GIF from numbered frames
magick -delay 10 -loop 0 /tmp/frames/frame_*.png /tmp/animation.gif

# With resize and optimization
magick -delay 8 -loop 0 /tmp/frames/*.png -resize 480x480 \
  -layers Optimize /tmp/optimized.gif

# Crossfade between images (slower, heavier)
magick -delay 100 /tmp/img1.jpg -delay 10 -morph 20 \
  /tmp/img2.jpg -delay 100 /tmp/img2.jpg -layers Optimize /tmp/crossfade.gif
```
