#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="/home/openclaw/.openclaw/workspace/skills/clipping-to-audio"
PROCESS_PY="$SKILL_DIR/scripts/process_clipping.py"
TTS_PY="$SKILL_DIR/scripts/tts_segments.py"

JSON_OUT=$(python3 "$PROCESS_PY" "${1:-}")
echo "$JSON_OUT"
ZH_FILE=$(python3 - <<'PY' "$JSON_OUT"
import json,sys
obj=json.loads(sys.argv[1])
print(obj['chinese_tts'])
PY
)
TITLE=$(basename "$ZH_FILE" .tts.zh.txt)
python3 "$TTS_PY" "$ZH_FILE" --title "$TITLE"
