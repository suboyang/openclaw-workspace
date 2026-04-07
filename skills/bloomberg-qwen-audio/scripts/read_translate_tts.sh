#!/usr/bin/env bash
set -euo pipefail

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
