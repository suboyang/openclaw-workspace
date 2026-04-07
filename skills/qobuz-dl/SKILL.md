---
name: qobuz-dl
description: Download albums from Qobuz using qobuz-dl CLI. Supports FLAC/Hi-Res quality, automatic cover art embedding, and organized folder structure by artist/album.
metadata:
  openclaw:
    emoji: 🎵
    requires:
      bins: ["qobuz-dl", "python3"]
---

# Qobuz Music Downloader

Download albums/tracks/playlists from Qobuz using `qobuz-dl`.

## Default Path

**`/home/openclaw/nas/Daphile/Qobuz Download`**

Music is automatically organized: `{Artist}/{Album} ({Year}) [{Quality}]/`

## Usage

### Download album
```
下載 https://play.qobuz.com/album/0074644545029
```

### Download with specific quality
```bash
# Quality 5 = MP3 320kbps (free account)
# Quality 6 = FLAC 16/44.1 (Studio)
# Quality 7 = FLAC 24/≤96kHz (Studio) ← DEFAULT
# Quality 27 = FLAC 24/>96kHz (Studio)
qobuz-dl dl "URL" -q 7
```

## Folder Format

```
/{Artist}/{Album} ({Year}) [{Quality}]/
├── 01. Track Title.flac
├── 02. Track Title.flac
└── cover.jpg
```

## Quality Options

| Code | Format | Account |
|------|---------|---------|
| 5 | MP3 320kbps | Free |
| 6 | FLAC 16/44.1 | Studio |
| 7 | FLAC 24/≤96kHz | Studio ⭐ |
| 27 | FLAC 24/>96kHz | Studio |

**Default: `-q 7`**

## Options

- `-d PATH` — Download directory (default: `/home/openclaw/nas/Daphile/Qobuz Download`)
- `-q INT` — Quality level (default: 7)
- `--embed-art` — Embed cover into audio files
- `--folder-format` — Custom folder naming
- `--no-db` — Skip database

## Notes

- Requires Qobuz Studio subscription for lossless quality
- Downloads are DRM-free after download
- Artist/Album metadata automatically extracted
