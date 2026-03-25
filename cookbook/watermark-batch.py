#!/usr/bin/env python3
"""
Cortex Example: watermark-batch
Description: Batch apply text watermark to images
Tags: image,pillow,watermark,batch
Captured: 2026-03-25
Source: watermark-batch.py

Usage:
  python ~/.claude/skills/cortex/cookbook/watermark-batch.py
"""

#!/usr/bin/env python3
"""
Batch apply text watermark to images. Configurable text, opacity, position.

Usage:
    python watermark-batch.py input_dir/ output_dir/ --text "CONFIDENTIAL"
    python watermark-batch.py input_dir/ output_dir/ --text "DRAFT" --opacity 0.3 --position center --fontsize 72
"""

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

POSITIONS = {
    "center": lambda w, h, tw, th: ((w - tw) // 2, (h - th) // 2),
    "bottom-right": lambda w, h, tw, th: (w - tw - 20, h - th - 20),
    "bottom-left": lambda w, h, tw, th: (20, h - th - 20),
    "top-right": lambda w, h, tw, th: (w - tw - 20, 20),
    "top-left": lambda w, h, tw, th: (20, 20),
}


def apply_watermark(img, text, opacity=0.3, position="center", fontsize=48):
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.truetype("arial.ttf", fontsize)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pos_fn = POSITIONS.get(position, POSITIONS["center"])
    x, y = pos_fn(img.width, img.height, tw, th)

    alpha = int(255 * opacity)
    draw.text((x, y), text, fill=(255, 255, 255, alpha), font=font)

    return Image.alpha_composite(img, overlay)


def main():
    parser = argparse.ArgumentParser(description="Batch watermark images")
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    parser.add_argument("--text", required=True)
    parser.add_argument("--opacity", type=float, default=0.3)
    parser.add_argument("--position", choices=POSITIONS.keys(), default="center")
    parser.add_argument("--fontsize", type=int, default=48)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    images = [f for f in input_dir.iterdir() if f.suffix.lower() in SUPPORTED]
    print(f"Watermarking {len(images)} images with '{args.text}'...")

    for img_path in sorted(images):
        try:
            img = Image.open(img_path)
            result = apply_watermark(img, args.text, args.opacity, args.position, args.fontsize)
            out = output_dir / img_path.name
            # Convert back to RGB for JPEG
            if img_path.suffix.lower() in (".jpg", ".jpeg"):
                result = result.convert("RGB")
            result.save(str(out))
            print(f"  {img_path.name}")
        except Exception as e:
            print(f"  ERROR: {img_path.name}: {e}")

    print(f"\nDone → {output_dir}")


if __name__ == "__main__":
    main()
