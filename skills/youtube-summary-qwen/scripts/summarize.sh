#!/bin/bash
# YouTube Summary + Qwen3-TTS Script
# 優先使用字幕，無字幕時降級到 Whisper
# 流程:
#   有字幕: YouTube → 字幕下載 → 文字處理 → 翻譯(如需要) → Qwen3-TTS → Discord
#   無字幕: YouTube → Whisper識別 → 文字處理 → 翻譯(如需要) → Qwen3-TTS → Discord

set -e

URL="${1:-}"
MODE="${2:-}"
FORCE_WHISPER=false
ORIGINAL_POWER_PROFILE=""
LOG_GPU_TASK_PY="/home/openclaw/.openclaw/workspace/scripts/log_gpu_task.py"
GPU_TASK_ID=""
GPU_TASK_STATUS="failed"
GPU_ERROR_MESSAGE=""

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
if [ -z "$URL" ]; then
    echo "用法: bash summarize.sh \"YouTube_URL\" [--force-whisper]"
    exit 1
fi
if [ "$MODE" = "--force-whisper" ]; then
    FORCE_WHISPER=true
fi

# ========== GPU 模式：自動停 GDM ==========
stop_gdm_if_needed() {
    if systemctl is-active gdm3 >/dev/null 2>&1; then
        echo "🔴 停止 GDM (釋放 GPU)..."
        sudo systemctl stop gdm3
        sleep 2
        GDM_WAS_RUNNING=1
    else
        GDM_WAS_RUNNING=0
    fi
}

start_gdm_if_needed() {
    :
}

cleanup() {
    if [ -n "$GPU_TASK_ID" ]; then
        python3 "$LOG_GPU_TASK_PY" end \
            --id "$GPU_TASK_ID" \
            --status "$GPU_TASK_STATUS" \
            ${TTS_MP3:+--output-path "$TTS_MP3"} \
            --model-name "Qwen3-TTS" \
            ${GPU_ERROR_MESSAGE:+--error-message "$GPU_ERROR_MESSAGE"} >/dev/null 2>&1 || true
    fi
    restore_power_mode
}
trap cleanup EXIT

TEMP_DIR="/mnt/nas_data/tmp/youtube"
mkdir -p "$TEMP_DIR"
WORK_DIR="/home/openclaw/.openclaw/workspace/tmp"
mkdir -p "$WORK_DIR"

export PATH="/home/openclaw/.openclaw/ytdlp-env/bin:$PATH"
SKILL_DIR="/home/openclaw/.openclaw/workspace/skills/youtube-summary-qwen"
VTD_SCRIPT="$SKILL_DIR/scripts/vtd.js"
BEST_SUB_SCRIPT="/home/openclaw/.openclaw/workspace/scripts/get_best_subtitles.sh"
BEST_SUB_EN_SCRIPT="/home/openclaw/.openclaw/workspace/scripts/get_best_subtitles_en.sh"
DOWNSUB_RAW_SCRIPT="/home/openclaw/.openclaw/workspace/scripts/downsub_raw_fetch.sh"
SUBTITLE_TO_TEXT_SCRIPT="/home/openclaw/.openclaw/workspace/scripts/subtitle_to_text.py"
DEEPSEEK_SUMMARY_SCRIPT="/home/openclaw/.openclaw/workspace/scripts/deepseek_browser_summary.py"

set_performance_mode

GPU_TASK_ID=$(python3 "$LOG_GPU_TASK_PY" start \
    --task-name "youtube-summary-qwen: ${URL}" \
    --task-type "youtube-summary-qwen" \
    --input-path "$URL" \
    --model-name "Qwen3-TTS" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')

echo "📺 開始處理: $URL"

# ========== Step 0: 獲取影片標題 ==========
echo "📝 Step 0: 獲取影片標題..."
VIDEO_TITLE=$(yt-dlp --get-title --no-playlist "$URL" 2>/dev/null | head -1 | sed 's/[\\/:*?"<>|]/_/g')
SAFE_TITLE=$(echo "$VIDEO_TITLE" | cut -c1-100)  # 限制長度
echo "📌 影片標題: $SAFE_TITLE"

# 停 GDM (如果正在運行)
stop_gdm_if_needed

TRANSCRIPT_FILE="$WORK_DIR/transcript_${SAFE_TITLE}_$$.txt"

# ========== Step 1: 嘗試下載字幕 ==========
echo "📥 Step 1: 嘗試下載字幕..."

SUBTITLE_SOURCE=""
USING_WHISPER=false

if [ "$FORCE_WHISPER" = true ]; then
    echo "⏩ 已指定 --force-whisper，跳過所有字幕鏈路，直接進入 Whisper..."
fi

# 1a: 嘗試 video-transcript-downloader (youtube-transcript-plus)
if [ "$FORCE_WHISPER" != true ]; then
    if node "$VTD_SCRIPT" transcript --url "$URL" --lang zh 2>/dev/null > "$TRANSCRIPT_FILE"; then
        if [ -s "$TRANSCRIPT_FILE" ] && [ $(wc -c < "$TRANSCRIPT_FILE") -gt 100 ]; then
            SUBTITLE_SOURCE="youtube-transcript-plus"
            echo "✅ 字幕下載成功 (youtube-transcript-plus)"
        fi
    fi
fi

# 1b: 若失敗，使用 get_best_subtitles.sh 做前置判斷 + 下載
if [ "$FORCE_WHISPER" != true ] && [ -z "$SUBTITLE_SOURCE" ]; then
    SUB_OUT_DIR="$WORK_DIR/subs_${SAFE_TITLE}_$$"
    mkdir -p "$SUB_OUT_DIR"
    if bash "$BEST_SUB_SCRIPT" "$URL" "$SUB_OUT_DIR"; then
        SUB_FILE=$(find "$SUB_OUT_DIR" -maxdepth 1 \( -name "*.vtt" -o -name "*.ttml" -o -name "*.srv3" -o -name "*.srv2" -o -name "*.srv1" -o -name "*.json3" \) | head -1)
        if [ -n "${SUB_FILE:-}" ] && [ -f "$SUB_FILE" ]; then
            python3 "$SUBTITLE_TO_TEXT_SCRIPT" "$SUB_FILE" "$TRANSCRIPT_FILE" >/dev/null 2>&1 || true
            if [ -s "$TRANSCRIPT_FILE" ] && [ $(wc -c < "$TRANSCRIPT_FILE") -gt 100 ]; then
                SUBTITLE_SOURCE="yt-dlp-best-subs"
                echo "✅ 字幕下載成功 (get_best_subtitles.sh + subtitle_to_text.py)"
            fi
        fi
    fi
fi

# 1c: 若仍失敗，英文鏈路嘗試 get_best_subtitles_en.sh
if [ "$FORCE_WHISPER" != true ] && [ -z "$SUBTITLE_SOURCE" ]; then
    SUB_OUT_DIR_EN="$WORK_DIR/subs_en_${SAFE_TITLE}_$$"
    mkdir -p "$SUB_OUT_DIR_EN"
    if bash "$BEST_SUB_EN_SCRIPT" "$URL" "$SUB_OUT_DIR_EN"; then
        SUB_FILE=$(find "$SUB_OUT_DIR_EN" -maxdepth 1 \( -name "*.vtt" -o -name "*.ttml" -o -name "*.srv3" -o -name "*.srv2" -o -name "*.srv1" -o -name "*.json3" \) | head -1)
        if [ -n "${SUB_FILE:-}" ] && [ -f "$SUB_FILE" ]; then
            python3 "$SUBTITLE_TO_TEXT_SCRIPT" "$SUB_FILE" "$TRANSCRIPT_FILE" >/dev/null 2>&1 || true
            if [ -s "$TRANSCRIPT_FILE" ] && [ $(wc -c < "$TRANSCRIPT_FILE") -gt 100 ]; then
                SUBTITLE_SOURCE="yt-dlp-best-subs-en"
                echo "✅ 英文字幕下載成功 (get_best_subtitles_en.sh + subtitle_to_text.py)"
            fi
        fi
    fi
fi

# 1d: 若仍失敗，使用 Chrome + DownSub 提取 RAW
if [ "$FORCE_WHISPER" != true ] && [ -z "$SUBTITLE_SOURCE" ]; then
    DOWNSUB_RAW_FILE="$WORK_DIR/downsub_raw_${SAFE_TITLE}_$$.txt"
    if bash "$DOWNSUB_RAW_SCRIPT" "$URL" auto "$DOWNSUB_RAW_FILE"; then
        if [ -s "$DOWNSUB_RAW_FILE" ] && [ $(wc -c < "$DOWNSUB_RAW_FILE") -gt 100 ]; then
            cp "$DOWNSUB_RAW_FILE" "$TRANSCRIPT_FILE"
            SUBTITLE_SOURCE="downsub-raw"
            echo "✅ 字幕下載成功 (Chrome + DownSub RAW)"
        fi
    fi
fi

# 1e: 若仍失敗，降級到 Whisper
if [ -z "$SUBTITLE_SOURCE" ]; then
    echo "⚠️  所有字幕鏈路失敗，降級到 Whisper 語音識別..."
    USING_WHISPER=true

    # 下載音頻
    AUDIO_FILE="$WORK_DIR/audio_${SAFE_TITLE}_$$.mp3"
    echo "📥 下載音頻..."
    yt-dlp -x --audio-format mp3 -o "$AUDIO_FILE" "$URL" 2>/dev/null

    # Whisper 識別
    echo "🎤 Whisper 語音識別..."
    whisper "$AUDIO_FILE" --model large-v3-turbo --model_dir /home/openclaw/.cache/whisper --output_dir "$WORK_DIR" --output_format txt 2>/dev/null

    # 找到轉錄文件
    TRANSCRIPT_FILE=$(ls ${AUDIO_FILE%.mp3}.txt 2>/dev/null | head -1)
    rm -f "$AUDIO_FILE"
fi

# 檢查轉錄結果
if [ -z "$TRANSCRIPT_FILE" ] || [ ! -s "$TRANSCRIPT_FILE" ]; then
    echo "❌ 轉錄失敗"
    GPU_ERROR_MESSAGE="transcript generation failed"
    start_gdm_if_needed
    exit 1
fi

echo "📝 轉錄完成: $TRANSCRIPT_FILE"

# ========== Step 2: 語言檢測 ==========
echo "🔍 Step 2: 語言檢測..."
LANG_DETECT=$(head -c 1000 "$TRANSCRIPT_FILE")
IS_CHINESE=false

if python3 - <<'PYEOF' "$TRANSCRIPT_FILE"
import sys, pathlib
text = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8', errors='ignore')[:1000]
print('YES' if any('\u4e00' <= ch <= '\u9fff' for ch in text) else 'NO')
PYEOF
then
    DETECT_RESULT=$(python3 - <<'PYEOF' "$TRANSCRIPT_FILE"
import sys, pathlib
text = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8', errors='ignore')[:1000]
print('YES' if any('\u4e00' <= ch <= '\u9fff' for ch in text) else 'NO')
PYEOF
)
    if [ "$DETECT_RESULT" = "YES" ]; then
        IS_CHINESE=true
        echo "🌐 檢測到: 中文"
    else
        echo "🌐 檢測到: 非中文"
    fi
else
    echo "🌐 語言檢測失敗，默認按非中文處理"
fi

# ========== Step 3: 生成摘要 ==========
echo "📝 Step 3: 生成摘要..."
SUMMARY_TEXT=$(cat "$TRANSCRIPT_FILE")

DEEPSEEK_OUT="$WORK_DIR/deepseek_summary_${SAFE_TITLE}_$$.txt"
if [ "$IS_CHINESE" = true ]; then
    echo "🌐 中文內容：調用 DeepSeek 瀏覽器做中文總結..."
    DEEPSEEK_LANG="zh"
else
    echo "🌐 非中文內容：調用 DeepSeek 瀏覽器總結英文內容並輸出中文稿..."
    DEEPSEEK_LANG="en"
fi

if python3 "$DEEPSEEK_SUMMARY_SCRIPT" "$TRANSCRIPT_FILE" "$DEEPSEEK_OUT" "$DEEPSEEK_LANG"; then
    if [ -s "$DEEPSEEK_OUT" ]; then
        FINAL_SUMMARY=$(cat "$DEEPSEEK_OUT")
    else
        echo "❌ DeepSeek 輸出為空"
        GPU_ERROR_MESSAGE="DeepSeek output empty"
        exit 1
    fi
else
    echo "❌ DeepSeek 瀏覽器總結失敗"
    GPU_ERROR_MESSAGE="DeepSeek summary failed"
    exit 1
fi

# ========== Step 3.5: 直接使用 Ollama 输出的纯文本 ==========
echo "🧹 Step 3.5: 复制 Ollama 总结文本..."
CLEAN_SUMMARY_FILE="$WORK_DIR/clean_summary_${SAFE_TITLE}_$$.txt"

# deepseek_browser_summary.py 现在直接输出纯文本，不需要再解析 HTML
if [ -s "$DEEPSEEK_OUT" ]; then
    cp "$DEEPSEEK_OUT" "$CLEAN_SUMMARY_FILE"
    echo "已复制总结文本到: $CLEAN_SUMMARY_FILE ($(wc -c < "$CLEAN_SUMMARY_FILE") 字)"
else
    echo "警告: 总结文件为空，Ollama 可能未成功生成内容"
    GPU_ERROR_MESSAGE="clean summary file empty"
    exit 1
fi

# ========== Step 4: Qwen3-TTS 語音生成 ==========
echo "🎙️ Step 4: Qwen3-TTS 語音生成..."
TTS_SCRIPT="$SKILL_DIR/scripts/tts_only.py"
TTS_OUTPUT="$WORK_DIR/${SAFE_TITLE}.wav"
SUMMARY_FILE="$CLEAN_SUMMARY_FILE"

~/.openclaw/qwen-tts-env/bin/python "$TTS_SCRIPT" "$SUMMARY_FILE" "$TTS_OUTPUT"

if [ ! -s "$TTS_OUTPUT" ]; then
    echo "❌ TTS 生成失敗"
    GPU_ERROR_MESSAGE="TTS generation failed"
    start_gdm_if_needed
    exit 1
fi

# 固定語速：Serena + atempo=0.95，然後轉 MP3（Discord 8MB 限制）
SLOWED_WAV="$WORK_DIR/${SAFE_TITLE}.slowed.wav"
ffmpeg -i "$TTS_OUTPUT" -filter:a "atempo=0.95" "$SLOWED_WAV" -y 2>/dev/null
ffmpeg -i "$SLOWED_WAV" -codec:a libmp3lame -qscale:a 2 "$WORK_DIR/${SAFE_TITLE}.mp3" -y 2>/dev/null
TTS_MP3="$WORK_DIR/${SAFE_TITLE}.mp3"

echo "✅ TTS 生成完成: $TTS_MP3"

# ========== Step 5: 發送到 Discord ==========
echo "📤 Step 5: 發送到 Discord..."

# 文字摘要
openclaw message send --channel discord --target channel:1486326928578183270 \
    --message "📝 YouTube 影片摘要\n📌 $SAFE_TITLE\n🌐 $([ "$IS_CHINESE" = true ] && echo '中文' || echo '英文→中文翻譯')\n\n$(cat "$SUMMARY_FILE" | head -c 2000)..."

# 語音
openclaw message send --channel discord --target channel:1486326928578183270 \
    --media "$TTS_MP3" \
    --message "🎙️ 語音版摘要 (Serena 溫柔慢速版) - $SAFE_TITLE"

# 清理（保留最終檔案）
rm -f "$TRANSCRIPT_FILE" "$SUMMARY_FILE" "$TTS_OUTPUT"

GPU_TASK_STATUS="completed"

echo "✅ 完成！"
echo "📁 輸出檔案: $TTS_MP3"
