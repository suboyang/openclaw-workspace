#!/usr/bin/env bash
set -euo pipefail

ORIGINAL_POWER_PROFILE=""
set_performance_mode() {
  if command -v powerprofilesctl >/dev/null 2>&1; then
    ORIGINAL_POWER_PROFILE=$(powerprofilesctl get 2>/dev/null || true)
    if [ -n "$ORIGINAL_POWER_PROFILE" ] && [ "$ORIGINAL_POWER_PROFILE" != "performance" ]; then
      echo "⚡ 切換到 performance 模式..."
      powerprofilesctl set performance >/dev/null 2>&1 || true
    fi
  fi
}
restore_power_mode() {
  if command -v powerprofilesctl >/dev/null 2>&1; then
    if [ -n "$ORIGINAL_POWER_PROFILE" ] && [ "$ORIGINAL_POWER_PROFILE" != "performance" ]; then
      echo "🔋 恢復到 $ORIGINAL_POWER_PROFILE 模式..."
      powerprofilesctl set "$ORIGINAL_POWER_PROFILE" >/dev/null 2>&1 || true
    elif [ -z "$ORIGINAL_POWER_PROFILE" ]; then
      powerprofilesctl set power-saver >/dev/null 2>&1 || true
    fi
  fi
}
trap restore_power_mode EXIT
set_performance_mode

URL="${1:-}"
if [ -z "$URL" ]; then
  echo "Usage: read_translate_tts.sh <bloomberg-url>"
  exit 1
fi

echo "This skill workflow is managed primarily by the agent."
echo "URL: $URL"
echo

echo "Expected steps:"
echo "1. Connect Chrome CDP"
echo "2. Open Bloomberg article"
echo "3. Extract article text"
echo "4. Translate/adapt into Chinese narration"
echo "5. Split into 3 segments"
echo "6. Run Qwen3-TTS on each segment"
echo "7. Merge MP3 files"
echo "8. Send final MP3 to Discord"
