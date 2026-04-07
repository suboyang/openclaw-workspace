---
name: youtube-summary
description: "YouTube影片總結：下載視頻音頻 → Whisper語音識別 → 摘要 → 台灣腔TTS。優先使用本地GPU A2000推理。"
metadata: {"openclaw":{"emoji":"📺","requires":{"bins":["ffmpeg","ffprobe"]}}}
---

# YouTube 影片總結流程

## 完整流程

```
YouTube URL → 字幕下載 → Whisper語音識別 → 摘要(3000字) → 台灣腔TTS → Discord
```

## 使用的環境

- **yt-dlp**: `/home/openclaw/.openclaw/ytdlp-env/bin/yt-dlp`
- **Whisper**: `/home/openclaw/.local/bin/whisper` (large-v3-turbo, GPU加速)
- **TTS**: Edge-TTS `zh-TW-HsiaoChenNeural` (台灣女聲)

## 步驟說明

### 1. 字幕優先策略
```bash
# 嘗試下載字幕
yt-dlp --write-subs --write-auto-subs --subs-lang zh-Hans,zh-Hant,en -o "/tmp/%(title)s.%(ext)s" "URL"
```

### 2. 無字幕時音頻下載
```bash
yt-dlp -x --audio-format mp3 -o "/tmp/youtube_audio.%(ext)s" "URL"
```

### 3. Whisper 語音識別 (A2000 GPU)
```bash
whisper /tmp/audio.mp3 --model large-v3-turbo --model_dir /home/openclaw/.cache/whisper --output_dir /tmp --output_format txt
```

### 4. 總結內容 (3000字以內)
- 保持原文核心觀點
- 使用中文繁體
- 濃縮精華

### 5. TTS 生成語音
```bash
edge-tts -t "摘要內容" -v zh-TW-HsiaoChenNeural --write-media /tmp/summary.wav
```

## 使用方式

```bash
bash /home/openclaw/.openclaw/workspace/skills/youtube-summary/scripts/summarize.sh "YouTube_URL"
```

## 輸出

- 音頻文件：自動發送到 Discord
- 文字摘要：Discord 文字回覆
