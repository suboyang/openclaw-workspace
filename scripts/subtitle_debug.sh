#!/usr/bin/env bash
set -euo pipefail

URL="${1:-}"
OUT_DIR="${2:-/home/openclaw/.openclaw/workspace/tmp/subtitle_debug}"
BEST_SUB_SCRIPT="/home/openclaw/.openclaw/workspace/scripts/get_best_subtitles.sh"
SUBTITLE_TO_TEXT_SCRIPT="/home/openclaw/.openclaw/workspace/scripts/subtitle_to_text.py"

if [ -z "$URL" ]; then
  echo "用法: $0 <video-url> [output-dir]"
  exit 1
fi

mkdir -p "$OUT_DIR"

echo "=== Step 1: 下載最佳字幕 ==="
bash "$BEST_SUB_SCRIPT" "$URL" "$OUT_DIR"

echo
echo "=== Step 2: 找到下載結果 ==="
SUB_FILE=$(find "$OUT_DIR" -maxdepth 1 \( -name "*.vtt" -o -name "*.ttml" -o -name "*.srv3" -o -name "*.srv2" -o -name "*.srv1" -o -name "*.json3" \) | head -1)
if [ -z "${SUB_FILE:-}" ]; then
  echo "❌ 沒找到字幕文件"
  exit 2
fi

echo "字幕文件: $SUB_FILE"
TXT_OUT="$OUT_DIR/$(basename "$SUB_FILE").txt"

echo
echo "=== Step 3: 轉純文本 ==="
python3 "$SUBTITLE_TO_TEXT_SCRIPT" "$SUB_FILE" "$TXT_OUT"

echo
echo "=== Step 4: 純文本預覽（前100行） ==="
sed -n '1,100p' "$TXT_OUT"

echo
echo "=== Step 5: 文件資訊 ==="
ls -lh "$SUB_FILE" "$TXT_OUT"
