#!/usr/bin/env bash
set -euo pipefail

URL="${1:-}"
OUT_DIR="${2:-/home/openclaw/.openclaw/workspace/tmp/subtitles_en}"

if [ -z "$URL" ]; then
  echo "用法: $0 <video-url> [output-dir]"
  exit 1
fi

mkdir -p "$OUT_DIR"
TMP_LIST=$(mktemp)
cleanup() {
  rm -f "$TMP_LIST"
}
trap cleanup EXIT

echo "🔍 檢查英文字幕: $URL"
yt-dlp --list-subs --no-playlist "$URL" > "$TMP_LIST"

echo "📄 可用字幕列表："
cat "$TMP_LIST"
echo

SELECTED_LANG=""
HAS_MANUAL=false
HAS_AUTO=false

# 優先手動英文字幕
for lang in en-orig en; do
  if awk '/Available subtitles for/{flag=1;next}/Available automatic captions for/{flag=0}flag' "$TMP_LIST" | grep -q "^$lang[[:space:]]"; then
    SELECTED_LANG="$lang"
    HAS_MANUAL=true
    break
  fi
done

# 再找自動英文字幕
if [ -z "$SELECTED_LANG" ]; then
  for lang in en-orig en; do
    if awk '/Available automatic captions for/{flag=1;next}flag' "$TMP_LIST" | grep -q "^$lang[[:space:]]"; then
      SELECTED_LANG="$lang"
      HAS_AUTO=true
      break
    fi
  done
fi

if [ -z "$SELECTED_LANG" ]; then
  echo "❌ 沒有找到英文字幕（en-orig / en）"
  exit 2
fi

if [ "$HAS_MANUAL" = true ]; then
  echo "✅ 選擇字幕：$SELECTED_LANG（手動字幕）"
else
  echo "✅ 選擇字幕：$SELECTED_LANG（自動字幕）"
fi

echo "⬇️ 下載英文字幕（優先 vtt，失敗則降級）..."
OUTPUT_TMPL="$OUT_DIR/%(title)s.%(id)s.%(ext)s"
FORMATS=("vtt" "ttml" "srv3" "srv2" "srv1" "json3" "best")
DOWNLOADED=false
for fmt in "${FORMATS[@]}"; do
  echo "   - 嘗試格式: $fmt"
  if yt-dlp \
    --skip-download \
    --write-subs \
    --write-auto-subs \
    --sub-langs "$SELECTED_LANG" \
    --sub-format "$fmt" \
    -o "$OUTPUT_TMPL" \
    "$URL"; then
    DOWNLOADED=true
    break
  fi
  echo "   ! 格式 $fmt 失敗，嘗試下一種..."
done

if [ "$DOWNLOADED" != true ]; then
  echo "❌ 英文字幕下載失敗：所有候選格式都不可用"
  exit 3
fi

echo
echo "📁 下載完成，輸出目錄：$OUT_DIR"
find "$OUT_DIR" -maxdepth 1 \( -name "*.vtt" -o -name "*.ttml" -o -name "*.srv3" -o -name "*.srv2" -o -name "*.srv1" -o -name "*.json3" \) -printf "%f\n" | sort
