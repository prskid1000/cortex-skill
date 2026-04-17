# `claw media` — Audio / Video Operations

> Source directory: [scripts/claw/src/claw/media/](../../scripts/claw/src/claw/media/)

Canonical CLI reference for `claw media ...`. Thin ergonomic wrapper over `ffmpeg` + `ffprobe` for the 80% of jobs that don't need a handwritten filter graph.

## Contents

- **AUDIO EXTRACT** — pull audio from video
  - [extract-audio — format-picked encode](#11-extract-audio)
- **FRAMES** — still(s) from a video
  - [thumbnail — single frame or contact sheet](#21-thumbnail)
- **GIF** — video to animated GIF
  - [gif — palette-correct two-step](#31-gif)
- **TRIM / SLICE** — cut a range
  - [trim — fast keyframe or precise re-encode](#41-trim)
- **COMPRESS** — shrink file size
  - [compress — target-size or CRF](#51-compress)
- **SCALE** — resize video
  - [scale — geometry-driven](#61-scale)
- **CONCAT** — join clips
  - [concat — demuxer or re-encode](#71-concat)
- **SUBTITLES** — SRT to pixels
  - [burn-subs — hardsub with styling](#81-burn-subs)
- **AUDIO NORMALIZE** — loudness
  - [loudnorm — EBU R128 two-pass](#91-loudnorm)
- **EFFECTS** — time & visual tweaks
  - [speed — atempo-chained](#101-speed) · [fade — v+a together](#102-fade) · [crop-auto — cropdetect then apply](#103-crop-auto)
- **INFO** — inspect streams
  - [info — normalized ffprobe](#111-info)

---

## Critical Rules

1. **Safe-write default.** Every verb producing a file requires `--out FILE`. If the target exists, the command refuses; add `--force` to overwrite or `--backup` to sidecar `.bak` the existing file.
2. **Timestamps accept two syntaxes.** `HH:MM:SS[.ms]` (`00:01:30.5`) or plain seconds (`90.5`). Both round-trip through ffmpeg's `-ss` / `-to`. Mixing is allowed — `--from 10 --to 00:01:30` is fine.
3. **`--json` for reads, `--stream` for jobs.** `info --json` emits jc-style normalized keys, with `*_utc` suffix on any tz-aware datetime fields. `--stream` makes long encodes emit one JSON progress line per second on stderr.
4. **Selector syntax.** Frame/time ranges: `N | a-b | all | odd | even | z-1 | 1-5,7` (used by `thumbnail --count`). `z-1` = second-to-last.
5. **Exit codes.** `0` success, `2` bad args / selector parse, `3` input missing, `4` output exists without `--force`, `5` underlying ffmpeg error (stderr surfaced), `6` not enough disk for two-pass.
6. **Self-documenting.** `claw media --help` lists verbs; `claw media <verb> --help` prints flag table.
7. **Pass-log files go to a tempdir** — ffmpeg's two-pass and loudnorm dump `.log` / `.mbtree` to CWD by default; `claw` always passes `-passlogfile "$(mktemp -d)/pass"` and cleans up on exit (including SIGINT).
8. **`--dry-run` prints the ffmpeg command** that would run — copy-pasteable into a terminal — without executing.
9. **Common output flags.** Every mutating verb inherits `--force`, `--backup`, `--dry-run`, `--json`, `--quiet`, `--mkdir` via the shared `@common_output_options` decorator. Individual verb blocks only call them out when the verb overrides the default; run `claw media <verb> --help` for the authoritative per-verb flag list.

---

## 1.1 extract-audio

> Source: [scripts/claw/src/claw/media/extract_audio.py](../../scripts/claw/src/claw/media/extract_audio.py)

Pull audio from a video into a clean audio-only file. Format inferred from `--format`; `--quality` maps to the codec's native quality knob.

```
claw media extract-audio <video> --out <out> [--format mp3|wav|aac|opus|flac] [--quality N] [--track 0]
```

| Flag | Default | Notes |
|---|---|---|
| `--format` | inferred from `--out` extension | |
| `--quality` | `2` for mp3 (VBR q:a), `5` for opus (bitrate tier), ignored for wav/flac | |
| `--track` | `0` | Audio stream index if multiple |

```
claw media extract-audio interview.mp4 --format mp3 --quality 2 --out interview.mp3
claw media extract-audio concert.mkv --format flac --out concert.flac
```

---

## 2.1 thumbnail

> Source: [scripts/claw/src/claw/media/thumbnail.py](../../scripts/claw/src/claw/media/thumbnail.py)

Grab one still or a contact sheet. Single frame = `--at`; grid = `--count N --grid WxH`.

```
claw media thumbnail <video> --out <out.jpg> (--at T | --count N --grid WxH) [--width N]
```

| Flag | Notes |
|---|---|
| `--at` | Timestamp of single frame |
| `--count` | Total frames to pick (evenly-spaced across duration) |
| `--grid` | e.g. `4x4` — required with `--count`, must satisfy `cols*rows == count` |
| `--width` | Per-frame width; height auto |

```
claw media thumbnail clip.mp4 --at 00:00:30 --width 1280 --out poster.jpg
claw media thumbnail lecture.mkv --count 16 --grid 4x4 --width 320 --out contact.jpg
```

---

## 3.1 gif

> Source: [scripts/claw/src/claw/media/gif.py](../../scripts/claw/src/claw/media/gif.py)

Video → animated GIF using the two-step `palettegen` + `paletteuse` chain (standalone `-vf scale=...,gif` looks like garbage).

```
claw media gif <video> --out <out.gif> --start T --duration D [--width N] [--fps 15] [--dither bayer|sierra|none]
```

| Flag | Default |
|---|---|
| `--start` | `0` |
| `--duration` | required |
| `--width` | `480` |
| `--fps` | `15` |
| `--dither` | `bayer` (smaller file; `sierra` for better gradients) |

```
claw media gif demo.mp4 --start 00:00:05 --duration 4 --width 600 --fps 20 --out demo.gif
```

---

## 4.1 trim

> Source: [scripts/claw/src/claw/media/trim.py](../../scripts/claw/src/claw/media/trim.py)

Cut a time range. Two modes:

- **Fast path** (default) — keyframe stream-copy. Millisecond cut-points snap to the nearest preceding keyframe. Zero re-encode; seconds per hour of source.
- **Precise path** (`--precise`) — re-encode with exact cut points. Slower; preserves container quality.

```
claw media trim <video> --out <out> --from T1 --to T2 [--precise] [--codec h264]
```

```
claw media trim meeting.mp4 --from 00:15:00 --to 00:18:30 --out clip.mp4            # stream copy
claw media trim meeting.mp4 --from 900 --to 912.5 --precise --out exact.mp4          # re-encode
```

---

## 5.1 compress

> Source: [scripts/claw/src/claw/media/compress.py](../../scripts/claw/src/claw/media/compress.py)

Shrink a video to a target size or CRF. `--target-size` runs two-pass with computed bitrate; `--crf` runs one-pass at constant quality. Mutually exclusive.

```
claw media compress <video> --out <out> (--target-size SIZE | --crf N) [--codec h264|h265|vp9|av1] [--preset P] [--audio-bitrate 128k]
```

| Flag | Default | Notes |
|---|---|---|
| `--codec` | `h264` | `h265` saves ~40%; `av1` ~50% at much slower encode |
| `--preset` | `medium` | libx264: `ultrafast` → `veryslow` |
| `--target-size` | — | e.g. `25M`, `1.5G` |
| `--crf` | — | Codec-appropriate: 18-28 (h264/h265), 30-40 (vp9) |

```
claw media compress raw.mov --target-size 25M --codec h265 --out small.mp4
claw media compress raw.mov --crf 23 --preset slow --out quality.mp4
```

---

## 6.1 scale

> Source: [scripts/claw/src/claw/media/scale.py](../../scripts/claw/src/claw/media/scale.py)

Resize video. Geometry uses ImageMagick syntax (same as `claw img`): `1280x720`, `50%`, `1280x-1` (preserve aspect), `1280x720!` (force exact, stretch allowed).

```
claw media scale <video> --geometry <GEOM> --out <out> [--codec h264] [--crf 20]
```

```
claw media scale 4k.mp4 --geometry 1920x1080 --out hd.mp4
claw media scale vertical.mp4 --geometry 720x-1 --out 720p.mp4     # keep aspect
```

---

## 7.1 concat

> Source: [scripts/claw/src/claw/media/concat.py](../../scripts/claw/src/claw/media/concat.py)

Join multiple clips. Default uses ffmpeg's concat demuxer (no re-encode) — **requires identical codec, resolution, framerate, and audio params** across inputs. If inputs differ, pass `--reencode` to normalize first.

Internally: writes a concat list file to a tempdir (`file 'abs/path'` per line) and cleans up on exit.

```
claw media concat <file1> <file2> ... --out <out> [--reencode] [--codec h264]
```

```
claw media concat intro.mp4 body.mp4 outro.mp4 --out final.mp4
claw media concat *.mp4 --reencode --codec h264 --out joined.mp4
```

---

## 8.1 burn-subs

> Source: [scripts/claw/src/claw/media/burn_subs.py](../../scripts/claw/src/claw/media/burn_subs.py)

Hardcode subtitles into pixels. Uses libass — supports SSA/ASS styling and SRT. Positional: subs file passed via `--srt`.

```
claw media burn-subs <video> --srt <SRT> --out <out> [--style 'FONT=Arial,SIZE=28,COLOR=#ffffff,OUTLINE=2,SHADOW=1']
```

| `--style` key | Libass equivalent |
|---|---|
| `FONT=` | `Fontname` |
| `SIZE=` | `Fontsize` |
| `COLOR=` | `PrimaryColour` (hex RGB) |
| `OUTLINE=` | `Outline` (px) |
| `SHADOW=` | `Shadow` (px) |
| `BG=` | `BorderStyle=3` + `BackColour` |

```
claw media burn-subs lecture.mp4 --srt lecture.srt --style 'FONT=Inter,SIZE=26,OUTLINE=2' --out hardsubbed.mp4
```

---

## 9.1 loudnorm

> Source: [scripts/claw/src/claw/media/loudnorm.py](../../scripts/claw/src/claw/media/loudnorm.py)

EBU R128 loudness normalization, two-pass. First pass measures; second pass applies the computed gain. Pass logs live in a tempdir and are removed after.

```
claw media loudnorm <audio|video> --out <out> [--I -16] [--TP -1.5] [--LRA 11] [--dry-run]
```

| Flag | Default | Target |
|---|---|---|
| `--I` | `-16` | Integrated loudness (LUFS); `-14` for Spotify/YouTube, `-23` for broadcast (EBU R128) |
| `--TP` | `-1.5` | True peak max (dBTP) |
| `--LRA` | `11` | Loudness range (LU) |

```
claw media loudnorm podcast.wav --I -16 --TP -1.5 --out podcast-normed.wav
claw media loudnorm episode.mp4 --I -23 --out broadcast.mp4         # keeps video stream
```

`--dry-run` runs only pass 1 and prints measurements — useful for scripts that want to check whether normalization is even needed.

---

## 10.1 speed

> Source: [scripts/claw/src/claw/media/speed.py](../../scripts/claw/src/claw/media/speed.py)

Change playback speed. Video uses `setpts`; audio is `atempo`. ffmpeg's `atempo` is capped at `0.5..2.0` per instance — for `>2×` or `<0.5×`, `claw` auto-chains multiple `atempo` filters to hit the requested factor exactly.

```
claw media speed <video> --factor F --out <out> [--no-audio]
```

```
claw media speed tutorial.mp4 --factor 1.5 --out 1x5.mp4          # 1.5× speed
claw media speed timelapse.mp4 --factor 8 --out fast.mp4          # atempo chained
claw media speed slomo.mp4 --factor 0.25 --out slow.mp4           # 0.25× (4× slower)
```

---

## 10.2 fade

> Source: [scripts/claw/src/claw/media/fade.py](../../scripts/claw/src/claw/media/fade.py)

Fade in/out, video and audio together.

```
claw media fade <video> --out <out> [--in N] [--out-sec N]
```

| Flag | Meaning |
|---|---|
| `--in` | Fade-in duration (sec) from start of clip |
| `--out-sec` | Fade-out duration (sec) ending at end of clip |

```
claw media fade clip.mp4 --in 2 --out-sec 2 --out faded.mp4
```

---

## 10.3 crop-auto

> Source: [scripts/claw/src/claw/media/crop_auto.py](../../scripts/claw/src/claw/media/crop_auto.py)

Detect and remove letterbox/pillarbox bars. Runs `cropdetect` for ~10 seconds, takes the mode, then applies `crop=W:H:X:Y`.

```
claw media crop-auto <video> --out <out> [--probe-duration 10] [--limit 24]
```

| Flag | Default | Notes |
|---|---|---|
| `--probe-duration` | `10` sec | Longer = more robust for varied scenes |
| `--limit` | `24` | `cropdetect` black threshold (0-255) |

```
claw media crop-auto widescreen-in-4x3.mp4 --out fixed.mp4
```

---

## 11.1 info

> Source: [scripts/claw/src/claw/media/info.py](../../scripts/claw/src/claw/media/info.py)

`ffprobe` normalized output — jc-style keys, nested `format` / `streams` / `chapters`, `*_utc` suffix on tz-aware datetime fields (`creation_time_utc`).

```
claw media info <file> [--json] [--stream video|audio|subtitle]
```

```
claw media info movie.mkv                         # pretty table
claw media info movie.mkv --json                  # full jc-style dump
claw media info movie.mkv --stream audio --json   # just audio tracks
```

Typical JSON:
```json
{
  "format": { "duration": 5432.1, "bit_rate": 4800000, "size_bytes": 3259000000, "creation_time_utc": "2026-03-12T19:04:11Z" },
  "streams": [
    { "index": 0, "type": "video", "codec": "h264", "width": 1920, "height": 1080, "fps": 23.976, "bit_rate": 4500000 },
    { "index": 1, "type": "audio", "codec": "aac", "channels": 2, "sample_rate": 48000, "bit_rate": 192000 }
  ]
}
```

---

## Footguns (why each verb exists)

- **Two-pass dumps log files to CWD.** `claw` routes `-passlogfile` to a tempdir and cleans it up. If you kill the process mid-encode, the dir is also removed.
- **`concat` demuxer silently corrupts when codecs differ** — frames play but timestamps drift, audio desyncs. `claw media concat` probes inputs first and errors out with a suggestion to pass `--reencode`.
- **`atempo` saturates beyond `0.5..2.0`** — `claw media speed --factor 8` chains three `atempo=2.0` filters so the audio actually keeps up.
- **`cropdetect` on a single frame is unreliable** (fade-ins look letterboxed) — `claw media crop-auto` samples over a window.
- **`-ss` before vs after `-i` is the difference between accurate-and-slow vs fast-and-keyframe-snapping.** `trim --precise` uses output-side seek; the default uses input-side for speed.
- **`loudnorm` single-pass is a lie** — ffmpeg docs recommend two-pass. `claw` always runs two-pass unless `--dry-run`.

## Do-not-wrap list

The following belong in raw `ffmpeg`, not `claw media`:

- **`-filter_complex` graphs** — arbitrary node graphs with labels, splits, hardware-bridging. ffmpeg flag syntax is already a DSL; wrapping it would mean either losing capability or reinventing ffmpeg.
- **HDR tonemapping** (`zscale=t=linear:npl=100,tonemap=...`). Use raw ffmpeg or HandBrake.
- **HLS ladder generation / adaptive streaming** (`-var_stream_map`, variant playlists). Niche; `ffmpeg` or a packager like Shaka is the right tool.
- **Video stabilization** (vidstab — `vidstabdetect` → `vidstabtransform`). Two-pass filter graph; write it by hand.
- **3D / stereoscopic processing.**

## When `claw media` isn't enough

Drop to the underlying tool:

**ffmpeg** — binary install (Windows: `scoop install ffmpeg`; macOS: `brew install ffmpeg`; Linux: distro pkg) · [docs](https://ffmpeg.org/ffmpeg.html)
- On Windows, `ffmpeg` installed via scoop/choco is a `.cmd`/`.exe` shim — `subprocess.run(["ffmpeg", ...])` from Python fails to find it; always `shutil.which("ffmpeg")` first.
- `-y` overwrites without prompting; its absence makes ffmpeg wait for `y\n` on stdin — a script without `-y` hangs forever when the output exists.
- Stream mapping is order-dependent: `-map 0:v:0 -map 0:a:0` vs `-map 0:a:0 -map 0:v:0` flips the stream order in the output, which some players (QuickTime) treat differently. Also, `-c copy` after filters silently ignores the filters — `-c:v libx264` is usually what you want.

**ffprobe** — ships with ffmpeg · [docs](https://ffmpeg.org/ffprobe.html)
- Default output is human-prose; for scripting use `-show_streams -show_format -of json` or `claw media info --json`.
- Duration reported as `format.duration` may differ from the longest stream's duration (container vs stream); trust `stream.duration` for precision.

**Pillow** — see [`claw img` escape hatches](img.md#when-claw-img-isnt-enough) for Pillow gotchas (used for thumbnail / poster-frame post-processing).

**ImageMagick** — see [`claw img` escape hatches](img.md#when-claw-img-isnt-enough) for ImageMagick gotchas (used for contact-sheet grids).

---

## Quick Reference

| Task | Command |
|---|---|
| Extract MP3 | `claw media extract-audio in.mp4 --format mp3 --out out.mp3` |
| Poster frame | `claw media thumbnail in.mp4 --at 00:00:30 --out poster.jpg` |
| Contact sheet | `claw media thumbnail in.mp4 --count 16 --grid 4x4 --out sheet.jpg` |
| Short GIF | `claw media gif in.mp4 --start 5 --duration 4 --width 600 --out out.gif` |
| Fast trim | `claw media trim in.mp4 --from 60 --to 90 --out clip.mp4` |
| Precise trim | `claw media trim in.mp4 --from 60 --to 90 --precise --out clip.mp4` |
| Target 25 MB | `claw media compress in.mp4 --target-size 25M --out small.mp4` |
| Downscale 1080p | `claw media scale in.mp4 --geometry 1920x1080 --out hd.mp4` |
| Join clips | `claw media concat a.mp4 b.mp4 --out joined.mp4` |
| Hardsub | `claw media burn-subs in.mp4 --srt in.srt --out hard.mp4` |
| Normalize podcast | `claw media loudnorm in.wav --I -16 --out out.wav` |
| 2× speed | `claw media speed in.mp4 --factor 2 --out fast.mp4` |
| Auto de-letterbox | `claw media crop-auto in.mp4 --out fixed.mp4` |
| Inspect streams | `claw media info in.mp4 --json` |
