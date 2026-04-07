#!/usr/bin/env bash
# YouTube 影片總結腳本
# 流程: 字幕下載 → Whisper語音識別 → 摘要 → 台灣腔TTS → Discord

set -e

YTDLP="/home/openclaw/.openclaw/ytdlp-env/bin/yt-dlp"
WHISPER="/home/openclaw/.local/bin/whisper"
WHISPER_MODEL_DIR="/home/openclaw/.cache/whisper"
OUTPUT_DIR="/tmp"
DISCORD_CHANNEL="1486326928578183270"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 檢查參數
if [[ $# -lt 1 ]]; then
    echo "用法: $0 <YouTube_URL>"
    exit 1
fi

URL="$1"
VIDEO_ID=$(echo "$URL" | grep -oP 'v=[^&]+' | cut -d'=' -f2 || echo "video")
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
AUDIO_FILE="${OUTPUT_DIR}/youtube_audio_${TIMESTAMP}.mp3"
TRANSCRIPT_FILE="${OUTPUT_DIR}/transcript_${TIMESTAMP}.txt"
SUMMARY_FILE="${OUTPUT_DIR}/summary_${TIMESTAMP}.txt"
TTS_FILE="${OUTPUT_DIR}/tts_summary_${TIMESTAMP}.wav"

log_info "開始處理: $URL"

# ===== 步驟1: 嘗試下載字幕 =====
log_info "步驟1: 嘗試下載字幕..."
SUBTITLE_DIR="${OUTPUT_DIR}/subs_${TIMESTAMP}"
mkdir -p "$SUBTITLE_DIR"

$YTDLP --write-subs --write-auto-subs \
    --subs-lang zh-Hans,zh-Hant,en \
    --convert-subs srt \
    -o "${SUBTITLE_DIR}/%(title)s.%(ext)s" \
    "$URL" 2>&1 | head -5 || true

# 檢查是否下載到字幕
SUBTITLE_FILE=$(find "$SUBTITLE_DIR" -name "*.srt" 2>/dev/null | head -1)

# ===== 步驟2: 下載音頻 =====
if [[ -z "$SUBTITLE_FILE" ]]; then
    log_warn "未找到字幕，下載音頻..."
    $YTDLP -x --audio-format mp3 \
        -o "${OUTPUT_DIR}/youtube_audio_${TIMESTAMP}.%(ext)s" \
        "$URL" 2>&1 | tail -3
    
    # 找到下載的音頻文件
    AUDIO_FILE=$(find "$OUTPUT_DIR" -name "youtube_audio_${TIMESTAMP}.*" -type f 2>/dev/null | head -1)
    
    if [[ -z "$AUDIO_FILE" ]]; then
        log_error "音頻下載失敗"
        exit 1
    fi
    
    # ===== 步驟3: Whisper 語音識別 (A2000 GPU) =====
    log_info "步驟2: Whisper 語音識別 (GPU)..."
    $WHISPER "$AUDIO_FILE" \
        --model large-v3-turbo \
        --model_dir "$WHISPER_MODEL_DIR" \
        --output_dir "$OUTPUT_DIR" \
        --output_format txt \
        --language Chinese \
        2>&1 | tail -10
    
    # 讀取轉錄結果
    TRANSCRIPT_FILE=$(find "$OUTPUT_DIR" -name "youtube_audio_${TIMESTAMP}.txt" -type f 2>/dev/null | head -1)
else
    log_info "找到字幕文件: $SUBTITLE_FILE"
    # 將字幕轉換為純文字
    TRANSCRIPT_FILE="${OUTPUT_DIR}/transcript_${TIMESTAMP}.txt"
    cat "$SUBTITLE_FILE" | sed 's/<[^>]*>//g' | grep -v '^$' > "$TRANSCRIPT_FILE"
fi

if [[ -z "$TRANSCRIPT_FILE" ]] || [[ ! -f "$TRANSCRIPT_FILE" ]]; then
    log_error "轉錄失敗"
    exit 1
fi

log_info "轉錄完成: $TRANSCRIPT_FILE"

# ===== 步驟4: 總結內容 =====
log_info "步驟3: 總結內容 (3000字以內)..."

# 讀取轉錄內容
TRANSCRIPT_CONTENT=$(cat "$TRANSCRIPT_FILE")

# 這裏調用 AI 進行總結
# 這裡假設有一個 Python 腳本處理總結
python3 << 'EOF'
import sys
import json

transcript = sys.stdin.read()

# 這裡是簡化的總結邏輯
# 實際應該調用 AI 模型進行智能總結
summary = transcript[:3000] if len(transcript) > 3000 else transcript

with open("/tmp/summary_current.txt", "w") as f:
    f.write(summary)

print(f"SUMMARY_LENGTH:{len(summary)}")
EOF

SUMMARY_FILE="/tmp/summary_current.txt"
SUMMARY_CONTENT=$(cat "$SUMMARY_FILE")

# ===== 步驟5: TTS 生成語音 =====
log_info "步驟4: 生成台灣腔語音..."

edge-tts -t "$SUMMARY_CONTENT" \
    -v zh-TW-HsiaoChenNeural \
    --write-media "$TTS_FILE" 2>&1

if [[ ! -f "$TTS_FILE" ]]; then
    log_error "TTS 生成失敗"
    exit 1
fi

# ===== 步驟6: 發送到 Discord =====
log_info "步驟5: 發送到 Discord..."

python3 << PYEOF
import os, json, requests

CONFIG_PATH = '/home/openclaw/.openclaw/openclaw.json'
audio_path = '$TTS_FILE'
summary_text = open('$SUMMARY_FILE').read()[:500]

with open(CONFIG_PATH, 'r') as f:
    token = json.load(f).get('channels', {}).get('discord', {}).get('token')

url = 'https://discord.com/api/v10/channels/$DISCORD_CHANNEL/messages'
headers = {'Authorization': f'Bot {token}'}

with open(audio_path, 'rb') as f:
    audio_data = f.read()

files = {'file': ('youtube_summary.wav', audio_data, 'audio/wav')}
data = {'content': f'📺 YouTube 影片總結（平翵腔）\n\n{summary_text}...(以下請聽語音)...'}

resp = requests.post(url, headers=headers, data=data, files=files)
print('Discord status:', resp.status_code, 'OK' if resp.status_code == 200 else 'Error')
PYEOF

# 清理臨時文件
rm -rf "$SUBTITLE_DIR" 2>/dev/null || true

log_info "完成！"
