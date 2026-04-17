# `claw img` — Image Operations

> Source directory: [scripts/claw/src/claw/img/](../../scripts/claw/src/claw/img/)

Canonical CLI reference for `claw img ...`. Thin ergonomic wrapper over Pillow + ImageMagick. For anything below the one-line-wrap threshold — drop to `magick` directly.

## Contents

- **RESIZE / CROP** — shape geometry
  - [resize — ImageMagick geometry](#11-resize) · [fit — crop to fill](#12-fit) · [pad — letterbox](#13-pad) · [thumb — fast downscale](#14-thumb) · [crop — explicit box](#15-crop)
- **ENHANCE** — tonal & sharpness correction
  - [enhance — autocontrast/equalize/posterize/solarize](#21-enhance) · [sharpen — unsharp mask](#22-sharpen)
- **COMPOSITE** — layer images together
  - [composite — alpha-correct paste](#31-composite) · [watermark — text or logo](#32-watermark) · [overlay — scaled corner logo](#33-overlay)
- **CONVERT** — format translation
  - [convert — extension-dispatched](#41-convert) · [to-jpeg — alpha-safe flatten](#42-to-jpeg) · [to-webp — modern web format](#43-to-webp)
- **META** — EXIF / filename
  - [exif — read/strip/auto-rotate](#51-exif) · [rename — template-driven rename](#52-rename)
- **BATCH** — pipelines over a directory
  - [batch — op chain on a dir](#61-batch)
- **ANIMATE** — multi-frame output
  - [gif-from-frames — directory to animated GIF](#71-gif-from-frames)

---

## Critical Rules

1. **Safe-write default.** Every verb that produces a file requires `--out FILE`. If the target exists, the command refuses to run; add `--force` to overwrite, or `--backup` to move the existing file to `PATH.bak` before writing.
2. **Selectors are ImageMagick syntax, verbatim.** Geometry strings accept `100x200`, `50%`, `100x200!` (force exact), `100x200>` (shrink-only, never upscale), `100x200^` (minimum fit), `100x200+10+10` (offset). Color strings: `#RRGGBB`, `#RRGGBBAA`, or an X11 name (`red`, `transparent`).
3. **Machine-readable output via `--json`.** All read-only verbs (`exif`, `batch --dry-run`) support `--json` and emit jc-style normalized keys. Binary verbs emit a JSON manifest on stderr when `--json` is passed.
4. **Exit codes.** `0` success, `2` bad args / selector parse error, `3` input missing, `4` output exists without `--force`, `5` underlying tool error (Pillow/ImageMagick exit surfaced).
5. **Self-documenting.** `claw img --help` lists verbs; `claw img <verb> --help` prints the full flag table for that verb and exits `0`.
6. **Streaming for giant batches.** `--stream` makes mutating verbs emit one line of JSON per processed file (usable with `jq` / `xargs`); without it, they buffer until end.
7. **Resample defaults.** Downscales default to `LANCZOS`; upscales to `BICUBIC`. Override with `--resample nearest|bilinear|bicubic|lanczos` when you know better.
8. **ICC profiles are stripped by default** to avoid surprise color shifts on color-managed targets. Pass `--preserve-icc` to keep them; `exif strip` preserves ICC unless `--strip-icc` is also set.
9. **Common output flags.** Every mutating verb inherits `--force`, `--backup`, `--dry-run`, `--json`, `--quiet`, `--mkdir` via the shared `@common_output_options` decorator. Individual verb blocks only call them out when the verb overrides the default; run `claw img <verb> --help` for the authoritative per-verb flag list.

---

## 1.1 resize

> Source: [scripts/claw/src/claw/img/resize.py](../../scripts/claw/src/claw/img/resize.py)

Scale an image using ImageMagick geometry. One-shot; no aspect-ratio inference gymnastics.

```
claw img resize <in> --geometry <GEOM> --out <out> [--resample lanczos] [--preserve-icc] [--force]
```

| Flag | Default | Notes |
|---|---|---|
| `--geometry` | (required) | ImageMagick geometry string — see Critical Rules |
| `--resample` | `lanczos` on shrink, `bicubic` on grow | |
| `--preserve-icc` | off | Keep embedded ICC profile |

```
claw img resize hero.png --geometry 1200x630 --out hero-og.png
claw img resize photo.jpg --geometry '2048x>' --out photo-shrunk.jpg   # shrink-only
claw img resize logo.svg --geometry 256x256! --out logo-256.png        # force exact
```

---

## 1.2 fit

> Source: [scripts/claw/src/claw/img/fit.py](../../scripts/claw/src/claw/img/fit.py)

Crop-to-fill using `PIL.ImageOps.fit` — image is scaled then cropped so both dimensions exactly match `--size`. Use for thumbnails that must be a precise shape.

```
claw img fit <in> --size WxH --out <out> [--center X,Y] [--resample lanczos]
```

| Flag | Default | Notes |
|---|---|---|
| `--size` | (required) | `WxH` in pixels |
| `--center` | `0.5,0.5` | Centering bias: `0,0` = top-left, `1,1` = bottom-right, `0.5,0.3` = slightly above middle |

```
claw img fit portrait.jpg --size 400x400 --center 0.5,0.3 --out avatar.jpg
```

---

## 1.3 pad

> Source: [scripts/claw/src/claw/img/pad.py](../../scripts/claw/src/claw/img/pad.py)

Letterbox to a target canvas — image preserved at max size that fits, remainder filled with `--color`.

```
claw img pad <in> --size WxH --color <color> --out <out>
```

| Flag | Default |
|---|---|
| `--size` | required |
| `--color` | `black` |

```
claw img pad 9x16.jpg --size 1920x1080 --color '#111111' --out 16x9-padded.jpg
```

---

## 1.4 thumb

> Source: [scripts/claw/src/claw/img/thumb.py](../../scripts/claw/src/claw/img/thumb.py)

Fast thumbnail for feed/grid use. Calls `Image.thumbnail(size, LANCZOS)`, applies `ImageOps.exif_transpose` (honors EXIF rotation), and enables JPEG `draft` mode to skip full decode on huge inputs.

```
claw img thumb <in> --max <N> --out <out> [--format jpeg|webp|png]
```

| Flag | Default | Notes |
|---|---|---|
| `--max` | required | Longest edge, in pixels |
| `--format` | inferred from `--out` | |

```
claw img thumb raw-12mp.jpg --max 512 --out thumb.jpg
```

---

## 1.5 crop

> Source: [scripts/claw/src/claw/img/crop.py](../../scripts/claw/src/claw/img/crop.py)

Crop an explicit pixel box.

```
claw img crop <in> --box x,y,w,h --out <out>
```

```
claw img crop screenshot.png --box 100,200,800,600 --out region.png
```

---

## 2.1 enhance

> Source: [scripts/claw/src/claw/img/enhance.py](../../scripts/claw/src/claw/img/enhance.py)

Tonal corrections via `ImageOps`. Flags are independent; pass any combination.

```
claw img enhance <in> --out <out> [--autocontrast [--cutoff N]] [--equalize] [--posterize N] [--solarize T]
```

| Flag | Type | Meaning |
|---|---|---|
| `--autocontrast` | bool | Stretch histogram |
| `--cutoff` | `0-49` | Percent to trim from each end (default `0`) |
| `--equalize` | bool | Histogram equalization |
| `--posterize` | `1-8` | Bits per channel |
| `--solarize` | `0-255` | Threshold for inversion |

```
claw img enhance scan.jpg --autocontrast --cutoff 1 --out scan-clean.jpg
```

---

## 2.2 sharpen

> Source: [scripts/claw/src/claw/img/sharpen.py](../../scripts/claw/src/claw/img/sharpen.py)

Unsharp mask — the only sharpen worth shipping. Wraps `ImageFilter.UnsharpMask(radius, percent, threshold)`.

```
claw img sharpen <in> --out <out> [--radius 2] [--amount 150] [--threshold 3]
```

| Flag | Default | Notes |
|---|---|---|
| `--radius` | `2` | Blur radius in pixels |
| `--amount` | `150` | Sharpening percent |
| `--threshold` | `3` | Skip pixels below this contrast |

```
claw img sharpen portrait.jpg --radius 1.5 --amount 120 --threshold 2 --out portrait-sharp.jpg
```

---

## 3.1 composite

> Source: [scripts/claw/src/claw/img/composite.py](../../scripts/claw/src/claw/img/composite.py)

Alpha-correct compositing. `--bg` and `--fg` can be files or hex colors; `--at x,y` positions the foreground.

```
claw img composite --bg <BG> --fg <FG> --at x,y --out <out> [--alpha 1.0]
```

| Flag | Notes |
|---|---|
| `--bg` | Path or color (fills canvas if color) |
| `--fg` | Path — pasted using its own alpha channel |
| `--at` | Pixel offset |
| `--alpha` | Multiply foreground alpha (0.0-1.0) |

```
claw img composite --bg card.png --fg stamp.png --at 40,40 --out stamped.png
```

---

## 3.2 watermark

> Source: [scripts/claw/src/claw/img/watermark.py](../../scripts/claw/src/claw/img/watermark.py)

Stamp text or a logo across the image. Position is a corner code: `TL|TC|TR|CL|CC|CR|BL|BC|BR`.

```
claw img watermark <in> --out <out> (--text T | --image LOGO) [--position BR] [--opacity 0.5] [--margin 20] [--font PATH] [--size PT] [--color #fff]
```

```
claw img watermark report.jpg --text '© 2026' --position BR --opacity 0.4 --out wm.jpg
claw img watermark slide.png --image logo.png --position TR --out slide-branded.png
```

---

## 3.3 overlay

> Source: [scripts/claw/src/claw/img/overlay.py](../../scripts/claw/src/claw/img/overlay.py)

Logo-on-corner helper — scales the logo to a fraction of the base image's shortest edge and pastes with alpha.

```
claw img overlay <in> --logo <LOGO> --scale 0.2 --position BR --out <out> [--margin 20]
```

```
claw img overlay hero.jpg --logo brand.png --scale 0.12 --position BL --out hero-branded.jpg
```

---

## 4.1 convert

> Source: [scripts/claw/src/claw/img/convert_.py](../../scripts/claw/src/claw/img/convert_.py)

Format translation dispatched by `<out>` extension. No transforms; use `resize`/`fit`/`enhance` for those. Preserves EXIF unless `--strip-exif`.

```
claw img convert <in> <out> [--quality N] [--lossless] [--strip-exif] [--preserve-icc]
```

Supported: `.png .jpg .jpeg .webp .gif .tiff .bmp .ico .pdf` (input), all of the above plus `.avif` via ImageMagick.

```
claw img convert logo.png logo.webp --quality 90
claw img convert screenshot.png screenshot.pdf
```

---

## 4.2 to-jpeg

> Source: [scripts/claw/src/claw/img/to_jpeg.py](../../scripts/claw/src/claw/img/to_jpeg.py)

Alpha-safe JPEG flatten — transparent pixels are composited onto `--bg` before encode. Prevents the silent black-background footgun.

```
claw img to-jpeg <in> --out <out.jpg> [--bg white] [--quality 85] [--progressive]
```

```
claw img to-jpeg screenshot.png --bg white --out screenshot.jpg
```

---

## 4.3 to-webp

> Source: [scripts/claw/src/claw/img/to_webp.py](../../scripts/claw/src/claw/img/to_webp.py)

```
claw img to-webp <in> --out <out.webp> [--quality 85] [--lossless] [--animated] [--method 6]
```

| Flag | Notes |
|---|---|
| `--lossless` | Quality flag ignored |
| `--animated` | For animated GIF → animated WebP |
| `--method` | `0-6`; higher = slower, smaller |

```
claw img to-webp cover.png --lossless --out cover.webp
claw img to-webp spin.gif --animated --out spin.webp
```

---

## 5.1 exif

> Source: [scripts/claw/src/claw/img/exif.py](../../scripts/claw/src/claw/img/exif.py)

Three sub-verbs: read, strip, auto-rotate.

```
claw img exif <in> [--json]                  # print EXIF (jc-style keys, *_utc suffix on datetimes)
claw img exif strip <in> --out <out>         # remove EXIF (preserves ICC unless --strip-icc)
claw img exif auto-rotate <in> --out <out>   # ImageOps.exif_transpose; result has Orientation=1
```

```
claw img exif DSC_0001.NEF --json | jq '.exif.DateTimeOriginal_utc'
claw img exif strip upload.jpg --out upload-clean.jpg
claw img exif auto-rotate phone-pic.jpg --out upright.jpg
```

---

## 5.2 rename

> Source: [scripts/claw/src/claw/img/rename.py](../../scripts/claw/src/claw/img/rename.py)

Rename files by a token template sourced from EXIF. Tokens use `exiftool` syntax — `{Tag[:format]}`. `{seq}` is a zero-padded collision-safe counter.

```
claw img rename <files...> --template '<TEMPLATE>' [--dry-run] [--force] [--lowercase-ext]
```

Supported tokens (common): `{CreateDate:%Y%m%d}`, `{CreateDate:%H%M%S}`, `{Camera}` (Make+Model), `{Make}`, `{Model}`, `{LensModel}`, `{FocalLength}`, `{ISO}`, `{ImageWidth}`, `{ImageHeight}`, `{ext}`, `{origname}`, `{seq}`.

```
claw img rename *.jpg --template '{CreateDate:%Y%m%d}_{Camera}_{seq}.{ext}' --dry-run
claw img rename vacation/*.NEF --template '{CreateDate:%Y-%m-%d}/IMG_{seq:04}.{ext}'
```

`--dry-run` prints planned renames without touching the filesystem.

---

## 6.1 batch

> Source: [scripts/claw/src/claw/img/batch.py](../../scripts/claw/src/claw/img/batch.py)

Run an op chain on every image matching a directory glob. Op chain syntax: `op1:arg1|op2:arg2|...`. Ops: `resize:GEOM`, `fit:WxH`, `thumb:MAX`, `sharpen[:radius,amount,threshold]`, `strip`, `autocontrast`, `jpeg:QUALITY`, `webp:QUALITY`, `png`, `rotate:AUTO`.

```
claw img batch <dir> --op '<chain>' [--out <dir>] [--recursive] [--pattern '*.{jpg,png}'] [--workers N] [--dry-run] [--stream]
```

| Flag | Default |
|---|---|
| `--pattern` | `*.{jpg,jpeg,png,webp,tif,tiff,heic}` |
| `--workers` | `min(8, cpu_count())` |
| `--out` | in-place (rewrite original) — `--backup` recommended |
| `--recursive` | off |

```
claw img batch ./photos --op 'resize:2048x|strip|jpeg:85' --out ./web --recursive
claw img batch ./ --op 'rotate:auto|webp:90' --backup --stream
```

---

## 7.1 gif-from-frames

> Source: [scripts/claw/src/claw/img/gif_from_frames.py](../../scripts/claw/src/claw/img/gif_from_frames.py)

Make an animated GIF from a directory of frames (lexicographically sorted).

```
claw img gif-from-frames <dir> --fps N --out <out.gif> [--loop 0] [--optimize] [--pattern '*.png']
```

| Flag | Default |
|---|---|
| `--fps` | required |
| `--loop` | `0` (infinite) |
| `--optimize` | off (enable for smaller files; slower) |
| `--pattern` | `*.png` |

```
claw img gif-from-frames ./frames --fps 15 --optimize --out cycle.gif
```

---

## Footguns (why each verb exists)

- **`Image.thumbnail()` mutates in place** and silently no-ops if the image is already smaller. `claw img thumb` always returns a copy and logs when no work was done.
- **JPEG-from-RGBA drops alpha with a black background.** `claw img to-jpeg --bg white` does the flatten for you; `claw img convert foo.png foo.jpg` also flattens and warns on stderr.
- **`resize` with PIL defaults to BILINEAR** — blurry downscales. `claw img resize` defaults to LANCZOS on shrink.
- **ImageMagick strips ICC profiles silently on some conversions.** `--preserve-icc` is explicit.
- **EXIF `Orientation` tag is honored by some viewers, not others.** `claw img exif auto-rotate` bakes the rotation into pixels and sets Orientation=1.

## Do-not-wrap list

The following belong in raw `magick`, not `claw img`:

- **Arbitrary filter chains** (`-morphology Convolve ...`, `-fx` expression language, `-evaluate-sequence Median`). `magick` is already a DSL — wrapping it in flags would be lossy.
- **`ImageDraw` primitive drawing** (lines, arcs, Bézier curves with per-point control). Write Python.
- **Per-channel math** (`magick in.png -channel R -evaluate multiply 0.9 +channel out.png`). Raw magick is the right interface.
- **Multi-image mathematical ops across frames** (sequence-level composite, stereographic projections). Niche; use `magick`.

## When `claw img` isn't enough

Drop to the underlying tool:

**Pillow** — `pip install Pillow` · [docs](https://pillow.readthedocs.io/)
- Import is `from PIL import Image`; the package is `Pillow` but the module is `PIL` (legacy fork-rename).
- `Image.open()` is lazy — `img.size` works but pixel access (`img.load()`, `.crop()`, `.save()`) is where it actually reads bytes. A `FileNotFoundError` can surface on the `.save()` line, not `open()`.
- Transparent PNGs saved as JPEG silently flatten to black background — composite onto `Image.new("RGB", img.size, "white")` before `.save("x.jpg")` or use `claw img to-jpeg --bg white`.

**ImageMagick** — binary install (Windows: `scoop install imagemagick`; macOS: `brew install imagemagick`; Linux: distro pkg) · [docs](https://imagemagick.org/script/command-line-options.php)
- On Windows, the CLI is `magick.cmd` (and `magick convert.cmd`) — resolve with `shutil.which("magick")` before `subprocess.run`, since `subprocess` doesn't auto-expand `.cmd` shims.
- ImageMagick 7 uses `magick ...` as the single entry point; `convert` on a box with IM6 installed is a *different* binary (and on modern Windows PATH, can be the built-in `convert.exe` disk-converter — disaster).
- `-resize 100x100` preserves aspect; `-resize 100x100!` (with `!`) ignores it. The `!` gets eaten by `bash` without quoting — always quote geometry strings.

---

## Quick Reference

| Task | Command |
|---|---|
| Shrink to fit 1200×630 | `claw img resize in.jpg --geometry 1200x630 --out out.jpg` |
| Crop square avatar | `claw img fit in.jpg --size 400x400 --out avatar.jpg` |
| Letterbox to 16:9 | `claw img pad in.jpg --size 1920x1080 --color black --out out.jpg` |
| Feed thumbnail | `claw img thumb in.jpg --max 512 --out thumb.jpg` |
| Strip EXIF | `claw img exif strip in.jpg --out clean.jpg` |
| Auto-rotate phone pic | `claw img exif auto-rotate in.jpg --out upright.jpg` |
| PNG → WebP lossless | `claw img to-webp in.png --lossless --out out.webp` |
| RGBA PNG → JPEG safely | `claw img to-jpeg in.png --bg white --out out.jpg` |
| Watermark corner | `claw img watermark in.jpg --text '© 2026' --position BR --out wm.jpg` |
| Batch resize+strip+webp | `claw img batch ./photos --op 'resize:2048x\|strip\|webp:85' --out ./web` |
| Frames → GIF | `claw img gif-from-frames ./frames --fps 15 --out out.gif` |
| Dump EXIF as JSON | `claw img exif in.jpg --json` |
