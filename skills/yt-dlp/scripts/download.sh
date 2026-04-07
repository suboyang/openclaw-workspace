#!/usr/bin/env bash
# yt-dlp wrapper script for OpenClaw
# Usage: download.sh [options] URL [URL...]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="/home/openclaw/.openclaw/ytdlp-env"
YTDLP="$VENV_DIR/bin/yt-dlp"

# Default output dir
OUTPUT_DIR="/mnt/nas_data/tmp/youtube"

# Parse arguments
URLS=()
OUTPUT_TEMPLATE="%(title)s.%(ext)s"

while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            OUTPUT_TEMPLATE="$2"
            shift 2
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        -x|--extract-audio)
            EXTRACT_AUDIO=1
            shift
            ;;
        --audio-format)
            AUDIO_FORMAT="$2"
            shift 2
            ;;
        --playlist-start)
            PLAYLIST_START="$2"
            shift 2
            ;;
        --playlist-end)
            PLAYLIST_END="$2"
            shift 2
            ;;
        --subs)
            WRITE_SUBS=1
            shift
            ;;
        --merge-output-format)
            MERGE_FORMAT="$2"
            shift 2
            ;;
        --list-formats)
            LIST_FORMATS=1
            shift
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: download.sh [options] URL [URL...]"
            echo ""
            echo "Options:"
            echo "  -o, --output TEMPLATE     Output filename template (default: %(title)s.%(ext)s)"
            echo "  -f, --format CODE         Video format (e.g., best, 720p)"
            echo "  -x, --extract-audio       Extract audio only"
            echo "  --audio-format FORMAT     Audio format: mp3, m4a, wav, flac"
            echo "  --playlist-start N        Playlist start index"
            echo "  --playlist-end N          Playlist end index"
            echo "  --subs                    Download subtitles"
            echo "  --merge-output-format FMT  Merge output format: mp4, mkv"
            echo "  --output-dir DIR          Output directory"
            echo "  --list-formats            List available formats"
            echo "  -h, --help                Show this help"
            exit 0
            ;;
        *)
            URLS+=("$1")
            shift
            ;;
    esac
done

if [[ ${#URLS[@]} -eq 0 ]]; then
    echo "Error: No URL provided"
    echo "Usage: download.sh [options] URL [URL...]"
    exit 1
fi

# Ensure output dir exists
mkdir -p "$OUTPUT_DIR"

# Build command
CMD=("$YTDLP")

# Add format options
if [[ -n "$FORMAT" ]]; then
    CMD+=("-f" "$FORMAT")
fi

if [[ -n "$EXTRACT_AUDIO" ]]; then
    CMD+=("-x")
fi

if [[ -n "$AUDIO_FORMAT" ]]; then
    CMD+=("--audio-format" "$AUDIO_FORMAT")
fi

if [[ -n "$WRITE_SUBS" ]]; then
    CMD+=("--write-subs" "--write-auto-subs" "--subs-lang" "zh-Hans,zh-Hant,en")
fi

if [[ -n "$MERGE_FORMAT" ]]; then
    CMD+=("--merge-output-format" "$MERGE_FORMAT")
fi

if [[ -n "$PLAYLIST_START" ]]; then
    CMD+=("--playlist-start" "$PLAYLIST_START")
fi

if [[ -n "$PLAYLIST_END" ]]; then
    CMD+=("--playlist-end" "$PLAYLIST_END")
fi

if [[ -n "$LIST_FORMATS" ]]; then
    CMD+=("--list-formats")
fi

# Output template
CMD+=("-o" "$OUTPUT_DIR/$OUTPUT_TEMPLATE")

# Add URLs
CMD+=("${URLS[@]}")

# Run
echo "Running: ${CMD[@]}"
exec "${CMD[@]}"
