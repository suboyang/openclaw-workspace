#!/usr/bin/env bash
set -euo pipefail

URL="${1:-}"
LANG_MODE="${2:-auto}"   # auto | en | zh
OUT_FILE="${3:-/home/openclaw/.openclaw/workspace/tmp/downsub_raw.txt}"
WORKDIR="/home/openclaw/.openclaw/workspace"

if [ -z "$URL" ]; then
  echo "用法: $0 <video-url> [auto|en|zh] [output-file]"
  exit 1
fi

mkdir -p "$(dirname "$OUT_FILE")"
TMP_SNAPSHOT=$(mktemp)
cleanup() {
  rm -f "$TMP_SNAPSHOT"
}
trap cleanup EXIT

# 取可用 page，优先新标签页
PAGE_ID=$(python3 - <<'PY'
import urllib.request, json
pages=json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read().decode())
page_id=None
for p in pages:
    if p.get('type')=='page' and p.get('url')=='chrome://newtab/':
        page_id=p.get('id'); break
if not page_id:
    for p in pages:
        if p.get('type')=='page':
            page_id=p.get('id'); break
print(page_id or '')
PY
)

if [ -z "$PAGE_ID" ]; then
  echo "❌ 找不到可用的 Chrome page id"
  exit 2
fi

agent-browser connect "ws://127.0.0.1:9222/devtools/page/$PAGE_ID" >/dev/null
agent-browser open "https://downsub.com/" >/dev/null
sleep 3
agent-browser fill ref=e16 "$URL" >/dev/null
agent-browser click ref=e15 >/dev/null
sleep 10
agent-browser snapshot > "$TMP_SNAPSHOT"

case "$LANG_MODE" in
  en)
    TARGET_LABEL="English (auto-generated)"
    ;;
  zh)
    TARGET_LABEL="Chinese (Simplified)"
    ;;
  auto)
    TARGET_LABEL=""
    ;;
  *)
    echo "❌ LANG_MODE 只能是 auto/en/zh"
    exit 3
    ;;
esac

RAW_REF=""
if [ -n "$TARGET_LABEL" ]; then
  RAW_REF=$(python3 - <<'PY' "$TMP_SNAPSHOT" "$TARGET_LABEL"
import sys,re
text=open(sys.argv[1],encoding='utf-8',errors='ignore').read().splitlines()
label=sys.argv[2]
for i,line in enumerate(text):
    if label in line:
        for j in range(max(0,i-8), i+8):
            m=re.search(r'button "RAW" \[ref=(e\d+)\]', text[j])
            if m:
                print(m.group(1))
                raise SystemExit
print('')
PY
)
fi

if [ -z "$RAW_REF" ]; then
  RAW_REF=$(python3 - <<'PY' "$TMP_SNAPSHOT"
import sys,re
text=open(sys.argv[1],encoding='utf-8',errors='ignore').read().splitlines()
for line in text:
    m=re.search(r'button "RAW" \[ref=(e\d+)\]', line)
    if m:
        print(m.group(1))
        break
PY
)
fi

if [ -z "$RAW_REF" ]; then
  echo "❌ 没找到 DownSub 的 RAW 按钮"
  exit 4
fi

agent-browser click "ref=$RAW_REF" >/dev/null || agent-browser click $RAW_REF >/dev/null
sleep 3
agent-browser snapshot > "$TMP_SNAPSHOT"

python3 - <<'PY' "$TMP_SNAPSHOT" "$OUT_FILE"
import sys,re
src=sys.argv[1]
out=sys.argv[2]
text=open(src,encoding='utf-8',errors='ignore').read()
# snapshot 进入 raw 页面后通常只剩一条 StaticText
parts=re.findall(r'- StaticText "([\s\S]*?)"', text)
if not parts:
    raise SystemExit(1)
content=max(parts, key=len)
content=content.replace('\\n','\n')
with open(out,'w',encoding='utf-8') as f:
    f.write(content.strip()+'\n')
print(len(content))
PY

echo "✅ DownSub RAW 已保存: $OUT_FILE"
