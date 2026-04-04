# Video & Audio Processing Examples

Working code blocks for FFmpeg CLI.

---

## Video Conversion

### Convert Video (MP4 to MKV, Codec Change)

```bash
# MP4 to MKV with H.265 encoding
ffmpeg -i /tmp/input.mp4 -c:v libx265 -crf 28 -c:a aac -b:a 128k /tmp/output.mkv

# MP4 to WebM (VP9 + Opus)
ffmpeg -i /tmp/input.mp4 -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus /tmp/output.webm

# AVI to MP4 (H.264)
ffmpeg -i /tmp/input.avi -c:v libx264 -crf 23 -c:a aac /tmp/output.mp4
```

### Remux Without Re-encoding

```bash
# Change container without re-encoding (fast)
ffmpeg -i /tmp/input.mp4 -c copy /tmp/output.mkv

# MKV to MP4 (stream copy)
ffmpeg -i /tmp/input.mkv -c copy -movflags +faststart /tmp/output.mp4
```

---

## Extraction & Trimming

### Extract Audio from Video

```bash
# Extract audio as MP3
ffmpeg -i /tmp/input.mp4 -vn -acodec libmp3lame -q:a 2 /tmp/audio.mp3

# Extract audio as WAV (lossless)
ffmpeg -i /tmp/input.mp4 -vn -acodec pcm_s16le /tmp/audio.wav

# Extract audio as AAC (copy if already AAC)
ffmpeg -i /tmp/input.mp4 -vn -c:a copy /tmp/audio.aac
```

### Trim / Cut Video

```bash
# Cut from 00:01:30 for 60 seconds (re-encode for precision)
ffmpeg -i /tmp/input.mp4 -ss 00:01:30 -t 60 -c:v libx264 -c:a aac /tmp/clip.mp4

# Cut from 00:01:30 to 00:03:00 (stream copy, fast but keyframe-aligned)
ffmpeg -i /tmp/input.mp4 -ss 00:01:30 -to 00:03:00 -c copy /tmp/clip.mp4

# Precise cut (input seeking + re-encode)
ffmpeg -ss 00:01:30 -i /tmp/input.mp4 -t 60 -c:v libx264 -crf 23 -c:a aac /tmp/clip.mp4
```

### Extract Subtitles

```bash
# List all streams to find subtitle track
ffprobe -v error -show_entries stream=index,codec_type,codec_name -of csv /tmp/input.mkv

# Extract SRT subtitles (stream 0:s:0 = first subtitle track)
ffmpeg -i /tmp/input.mkv -map 0:s:0 /tmp/subtitles.srt

# Extract ASS subtitles
ffmpeg -i /tmp/input.mkv -map 0:s:0 /tmp/subtitles.ass
```

---

## Merging & Concatenation

### Merge / Concatenate Videos (Concat Demuxer)

```bash
# Create file list
cat > /tmp/filelist.txt << 'EOF'
file '/tmp/part1.mp4'
file '/tmp/part2.mp4'
file '/tmp/part3.mp4'
EOF

# Concatenate (same codec/resolution)
ffmpeg -f concat -safe 0 -i /tmp/filelist.txt -c copy /tmp/merged.mp4

# Concatenate with re-encode (different codecs/resolutions)
ffmpeg -f concat -safe 0 -i /tmp/filelist.txt -c:v libx264 -crf 23 -c:a aac /tmp/merged.mp4
```

### Add Audio to Video

```bash
# Replace audio track
ffmpeg -i /tmp/video.mp4 -i /tmp/audio.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 /tmp/output.mp4

# Mix audio with existing (overlay)
ffmpeg -i /tmp/video.mp4 -i /tmp/music.mp3 \
  -filter_complex "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[a]" \
  -c:v copy -map 0:v -map "[a]" /tmp/output.mp4
```

### Remove Audio from Video

```bash
ffmpeg -i /tmp/input.mp4 -c:v copy -an /tmp/silent.mp4
```

---

## Thumbnails & Frames

### Thumbnail Extraction

```bash
# Single frame at 00:00:05
ffmpeg -i /tmp/input.mp4 -ss 00:00:05 -frames:v 1 /tmp/thumbnail.jpg

# Multiple frames (one every 10 seconds)
ffmpeg -i /tmp/input.mp4 -vf "fps=1/10" /tmp/thumb_%04d.jpg

# Smart thumbnail (select most representative frame from each scene)
ffmpeg -i /tmp/input.mp4 -vf "select='gt(scene,0.3)',scale=320:-1" -vsync vfr /tmp/scene_%04d.jpg

# Thumbnail sheet (4x4 grid)
ffmpeg -i /tmp/input.mp4 -frames 1 -vf "select=not(mod(n\,100)),scale=320:-1,tile=4x4" /tmp/sheet.jpg
```

---

## GIF & Animated Formats

### GIF Creation (with Palette Optimization)

```bash
# Step 1: Generate optimized palette
ffmpeg -i /tmp/input.mp4 -ss 00:00:02 -t 5 \
  -vf "fps=15,scale=480:-1:flags=lanczos,palettegen" /tmp/palette.png

# Step 2: Create GIF using palette
ffmpeg -i /tmp/input.mp4 -i /tmp/palette.png -ss 00:00:02 -t 5 \
  -filter_complex "fps=15,scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse" /tmp/output.gif
```

### Animated WebP Creation

```bash
ffmpeg -i /tmp/input.mp4 -ss 00:00:02 -t 5 \
  -vf "fps=15,scale=480:-1" -c:v libwebp -lossless 0 -quality 75 -loop 0 /tmp/output.webp
```

---

## Compression & Scaling

### Compress Video (CRF Encoding)

```bash
# H.264 (CRF 18=visually lossless, 23=default, 28=smaller)
ffmpeg -i /tmp/input.mp4 -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k \
  -movflags +faststart /tmp/compressed.mp4

# H.265 (better compression, same quality at higher CRF)
ffmpeg -i /tmp/input.mp4 -c:v libx265 -crf 28 -preset medium -c:a aac -b:a 128k /tmp/compressed.mp4

# Target file size (~25MB for a 5-min video)
# bitrate = target_size_bits / duration_seconds = 25*8*1024*1024 / 300 ≈ 700k
ffmpeg -i /tmp/input.mp4 -c:v libx264 -b:v 700k -pass 1 -f null /dev/null && \
ffmpeg -i /tmp/input.mp4 -c:v libx264 -b:v 700k -pass 2 -c:a aac -b:a 96k /tmp/compressed.mp4
```

### Resize / Scale Video

```bash
# Scale to 1280x720
ffmpeg -i /tmp/input.mp4 -vf "scale=1280:720" -c:a copy /tmp/720p.mp4

# Scale width to 1280, auto height (preserve aspect ratio, ensure even)
ffmpeg -i /tmp/input.mp4 -vf "scale=1280:-2" -c:a copy /tmp/resized.mp4

# Scale to half size
ffmpeg -i /tmp/input.mp4 -vf "scale=iw/2:ih/2" -c:a copy /tmp/half.mp4
```

### Crop Video

```bash
# Crop to 640x480 from center
ffmpeg -i /tmp/input.mp4 -vf "crop=640:480" -c:a copy /tmp/cropped.mp4

# Crop with offset (640x480 starting at x=100, y=50)
ffmpeg -i /tmp/input.mp4 -vf "crop=640:480:100:50" -c:a copy /tmp/cropped.mp4

# Auto-detect and remove black bars
ffmpeg -i /tmp/input.mp4 -vf "cropdetect" -f null /dev/null 2>&1 | tail -5
# Then apply detected crop values
ffmpeg -i /tmp/input.mp4 -vf "crop=1280:536:0:92" -c:a copy /tmp/cropped.mp4
```

---

## Overlays & Effects

### Add Text Overlay (drawtext)

```bash
# Static text
ffmpeg -i /tmp/input.mp4 -vf \
  "drawtext=text='Hello World':fontsize=48:fontcolor=white:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h-th-20" \
  -c:a copy /tmp/text_overlay.mp4

# Timestamp overlay
ffmpeg -i /tmp/input.mp4 -vf \
  "drawtext=text='%{pts\\:hms}':fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5:x=10:y=10" \
  -c:a copy /tmp/timestamped.mp4
```

### Burn Subtitles

```bash
# Burn SRT subtitles into video
ffmpeg -i /tmp/input.mp4 -vf "subtitles=/tmp/subtitles.srt" -c:a copy /tmp/subtitled.mp4

# With custom styling
ffmpeg -i /tmp/input.mp4 -vf \
  "subtitles=/tmp/subtitles.srt:force_style='FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2'" \
  -c:a copy /tmp/subtitled.mp4
```

### Add Watermark Image Overlay

```bash
# Logo at top-right corner
ffmpeg -i /tmp/input.mp4 -i /tmp/logo.png \
  -filter_complex "overlay=W-w-10:10" -c:a copy /tmp/watermarked.mp4

# Semi-transparent watermark
ffmpeg -i /tmp/input.mp4 -i /tmp/logo.png \
  -filter_complex "[1:v]format=rgba,colorchannelmixer=aa=0.3[logo];[0:v][logo]overlay=W-w-10:10" \
  -c:a copy /tmp/watermarked.mp4
```

### Fade In / Out (Video + Audio)

```bash
# Fade in first 2 seconds, fade out last 2 seconds (for a 60-second video)
ffmpeg -i /tmp/input.mp4 -vf "fade=t=in:st=0:d=2,fade=t=out:st=58:d=2" \
  -af "afade=t=in:st=0:d=2,afade=t=out:st=58:d=2" /tmp/faded.mp4
```

---

## Speed & Direction

### Speed Up / Slow Down

```bash
# 2x speed
ffmpeg -i /tmp/input.mp4 -filter_complex "[0:v]setpts=0.5*PTS[v];[0:a]atempo=2.0[a]" \
  -map "[v]" -map "[a]" /tmp/fast.mp4

# 0.5x speed (slow motion)
ffmpeg -i /tmp/input.mp4 -filter_complex "[0:v]setpts=2.0*PTS[v];[0:a]atempo=0.5[a]" \
  -map "[v]" -map "[a]" /tmp/slow.mp4

# 4x speed (chain atempo for >2x audio)
ffmpeg -i /tmp/input.mp4 -filter_complex "[0:v]setpts=0.25*PTS[v];[0:a]atempo=2.0,atempo=2.0[a]" \
  -map "[v]" -map "[a]" /tmp/4x.mp4
```

### Reverse Video

```bash
# Reverse video and audio
ffmpeg -i /tmp/input.mp4 -vf reverse -af areverse /tmp/reversed.mp4
```

---

## Audio Operations

### Audio Conversion

```bash
# WAV to MP3 (VBR quality 2 = ~190kbps)
ffmpeg -i /tmp/input.wav -codec:a libmp3lame -q:a 2 /tmp/output.mp3

# MP3 to AAC
ffmpeg -i /tmp/input.mp3 -c:a aac -b:a 192k /tmp/output.m4a

# FLAC to MP3
ffmpeg -i /tmp/input.flac -codec:a libmp3lame -b:a 320k /tmp/output.mp3

# Any format to WAV
ffmpeg -i /tmp/input.m4a -acodec pcm_s16le -ar 44100 /tmp/output.wav
```

### Normalize Audio (loudnorm)

```bash
# Two-pass loudness normalization (EBU R128)
# Pass 1: analyze
ffmpeg -i /tmp/input.mp3 -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null /dev/null 2>&1 | tail -12

# Pass 2: apply (use values from pass 1)
ffmpeg -i /tmp/input.mp3 -af \
  "loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=-23:measured_TP=-4:measured_LRA=15:measured_thresh=-34:linear=true" \
  /tmp/normalized.mp3

# Simple one-pass normalization
ffmpeg -i /tmp/input.mp3 -af loudnorm=I=-16:TP=-1.5:LRA=11 /tmp/normalized.mp3
```

### Change Audio Volume

```bash
# Double volume
ffmpeg -i /tmp/input.mp4 -af "volume=2.0" -c:v copy /tmp/louder.mp4

# Halve volume
ffmpeg -i /tmp/input.mp4 -af "volume=0.5" -c:v copy /tmp/quieter.mp4

# Set to specific dB
ffmpeg -i /tmp/input.mp4 -af "volume=5dB" -c:v copy /tmp/boosted.mp4
```

---

## Advanced

### Video Stabilization

```bash
# Pass 1: detect shakes
ffmpeg -i /tmp/shaky.mp4 -vf vidstabdetect=shakiness=5:accuracy=15 -f null /dev/null

# Pass 2: apply stabilization
ffmpeg -i /tmp/shaky.mp4 -vf vidstabtransform=smoothing=10:input=transforms.trf -c:a copy /tmp/stabilized.mp4
```

### Split Into Segments

```bash
# Split into 30-second segments
ffmpeg -i /tmp/input.mp4 -c copy -f segment -segment_time 30 \
  -reset_timestamps 1 /tmp/segment_%03d.mp4

# Split at specific times
ffmpeg -i /tmp/input.mp4 -c copy -f segment \
  -segment_times "60,120,180" -reset_timestamps 1 /tmp/segment_%03d.mp4
```

### Denoise Video

```bash
# Light denoise (nlmeans)
ffmpeg -i /tmp/input.mp4 -vf "nlmeans=s=3:p=7:r=15" -c:a copy /tmp/denoised.mp4

# Medium denoise
ffmpeg -i /tmp/input.mp4 -vf "nlmeans=s=6:p=7:r=15" -c:a copy /tmp/denoised.mp4

# Denoise + sharpen combo
ffmpeg -i /tmp/input.mp4 -vf "nlmeans=s=4:p=7:r=15,unsharp=5:5:0.5" -c:a copy /tmp/clean.mp4
```

### Screen Recording (Windows gdigrab)

```bash
# Record full desktop
ffmpeg -f gdigrab -framerate 30 -i desktop -c:v libx264 -crf 20 -preset ultrafast /tmp/screen.mp4

# Record specific window
ffmpeg -f gdigrab -framerate 30 -i title="Untitled - Notepad" -c:v libx264 -crf 20 /tmp/window.mp4

# Record region (offset 100,200 size 1280x720)
ffmpeg -f gdigrab -framerate 30 -offset_x 100 -offset_y 200 -video_size 1280x720 \
  -i desktop -c:v libx264 -crf 20 -preset ultrafast /tmp/region.mp4
```

### Get Media Info (ffprobe JSON)

```bash
# Full metadata as JSON
ffprobe -v quiet -print_format json -show_format -show_streams /tmp/input.mp4

# Duration only
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 /tmp/input.mp4

# Resolution only
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 /tmp/input.mp4

# Codec info
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,bit_rate,r_frame_rate -of json /tmp/input.mp4
```

### HLS Streaming Output

```bash
# Create HLS stream with multiple quality levels
ffmpeg -i /tmp/input.mp4 -c:v libx264 -crf 23 -c:a aac -b:a 128k \
  -hls_time 10 -hls_list_size 0 -hls_segment_filename "/tmp/hls/segment_%03d.ts" \
  /tmp/hls/playlist.m3u8

# Multi-bitrate HLS
ffmpeg -i /tmp/input.mp4 \
  -map 0:v -map 0:a -map 0:v -map 0:a \
  -c:v libx264 -c:a aac \
  -b:v:0 1000k -s:v:0 640x360 -b:a:0 96k \
  -b:v:1 3000k -s:v:1 1280x720 -b:a:1 128k \
  -var_stream_map "v:0,a:0 v:1,a:1" \
  -hls_time 10 -hls_list_size 0 \
  -master_pl_name master.m3u8 \
  -f hls /tmp/hls/stream_%v.m3u8
```

### Hardware-Accelerated Encoding (NVENC)

```bash
# H.264 NVENC encoding (requires NVIDIA GPU)
ffmpeg -i /tmp/input.mp4 -c:v h264_nvenc -preset p4 -cq 23 -c:a copy /tmp/nvenc.mp4

# H.265 NVENC
ffmpeg -i /tmp/input.mp4 -c:v hevc_nvenc -preset p4 -cq 28 -c:a copy /tmp/nvenc_hevc.mp4

# Check available hardware encoders
ffmpeg -encoders 2>/dev/null | grep -i nvenc
```
