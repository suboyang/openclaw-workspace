---
name: yt-dlp
description: Download videos and audio from YouTube, Twitter, and 1000+ sites using yt-dlp. Supports video merging, subtitle extraction, and format conversion.
metadata: {"openclaw":{"emoji":"📺","requires":{"bins":["ffmpeg","ffprobe"]}}}
---

# yt-dlp Skill

Download videos and audio from YouTube, Twitter, and 1000+ sites.

## Usage

```bash
# Download video (best quality)
ytdlp "https://www.youtube.com/watch?v=..."

# Download audio only (MP3)
ytdlp --extract-audio --audio-format mp3 "URL"

# Download best quality + merge to MP4
ytdlp -f "bestvideo+bestaudio/best" --merge-output-format mp4 "URL"

# Download with subtitles
ytdlp --write-subs --write-auto-subs "URL"

# Download playlist
ytdlp --playlist-start 1 --playlist-end 10 "PLAYLIST_URL"

# Show available formats
ytdlp --list-formats "URL"
```

## Options

| Option | Description |
|--------|-------------|
| `-f, --format` | Video format code (e.g., best, worst, 720p) |
| `--extract-audio` | Extract audio only |
| `--audio-format mp3` | Audio format: mp3, m4a, wav, flac |
| `--write-subs` | Download subtitles |
| `--write-auto-subs` | Download auto-generated subtitles |
| `--merge-output-format mp4` | Merge to MP4 container |
| `-o, --output` | Output filename template |
| `--playlist-start/end` | Playlist range |
| `--list-formats` | List available formats |
| `--no-check-certificates` | Skip SSL verification |
| `--proxy` | Use proxy |
| `-i, --ignore-errors` | Continue on download errors |

## Output Templates

| Template | Description |
|----------|-------------|
| `%(title)s.%(ext)s` | Title + extension |
| `%(id)s.%(ext)s` | Video ID + extension |
| `%(uploader)s/%(title)s.%(ext)s` | In uploader folder |

## Common Sites

- YouTube, Twitter, TikTok, Instagram
- Twitch, Vimeo, Dailymotion
- Bilibili, Niconico
- Facebook, Reddit
- And 1000+ more

## Examples

**Download YouTube video:**
```bash
ytdlp "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Download audio and convert to MP3:**
```bash
ytdlp -x --audio-format mp3 "URL"
```

**Download at 720p:**
```bash
ytdlp -f "best[height<=720]" "URL"
```

**Download with Chinese subtitles:**
```bash
ytdlp --write-subs --write-auto-subs --subs-lang zh-Hans,zh-Hant "URL"
```

**Download playlist:**
```bash
ytdlp --playlist-start 1 --playlist-end 5 "PLAYLIST_URL"
```

## Environment

Uses the yt-dlp virtualenv at:
`/home/openclaw/.openclaw/ytdlp-env/`

Activate with:
```bash
source /home/openclaw/.openclaw/ytdlp-env/bin/activate
```
