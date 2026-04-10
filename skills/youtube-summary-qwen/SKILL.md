---
name: youtube-summary-qwen
description: YouTube影片總結+語音版：字幕優先下載→無字幕時Whisper識別→摘要→翻譯(英文時)→Qwen3-TTS Serena語音。支援中英文，自動檢測。
metadata:
  openclaw:
    emoji: 🎙️
    requires:
      bins:
        - ffmpeg
        - ffprobe
modified: 2026-04-08T02:03:16+08:00
---

# YouTube 影片總結 + Qwen3-TTS 語音 (多語言版)

## 完整流程

```
YouTube URL
  ├─ 有字幕 → 下載字幕 → 轉文字
  └─ 無字幕 → Whisper識別(英文/中文)
      ├─ 英文 → 摘要(EN) → 翻譯(繁中)
      └─ 中文 → 摘要(ZH)
  └─ Qwen3-TTS(中文語音) → Discord
```

## 使用的工具

- **字幕下載**: `video-transcript-downloader` + `youtube-transcript-plus`
- **語音識別**: Whisper Large V3 Turbo (A2000 GPU)
- **总结**: 不少于推理内容的1/3,不多于3000字总结.
- **翻譯**: 先总结全文内容, 再进行中文翻译.
- **分段**:分成3~10段录制,每段文字不多于400字 
- **TTS**: Qwen3-TTS-0.6B-CustomVoice (Serena 溫柔女聲)
- **合成**:把所有段录制音频合成一个文件
- **文件名**:最总合成音频文件名和youtube链接视频标题一致
- **yt-dlp**: `/home/openclaw/.openclaw/ytdlp-env/bin/yt-dlp`

## 語言檢測邏輯

- 有字幕：直接讀取字幕內容，檢測是否含中文字符
- 無字幕：Whisper 自動檢測語言
- **有中文** → 判定為中文內容，跳過翻譯
- **無中文** → 判定為英文內容，自動翻譯成繁體中文

## 字幕優先策略

```bash
# Step 1: 嘗試 youtube-transcript-plus
# Step 2: 若失敗則先用 get_best_subtitles.sh 判斷並下載最佳字幕
#         - 優先中文字幕
#         - 優先 vtt
#         - vtt 失敗時自動降級 ttml/srv3/srv2/srv1/json3
# Step 3: 下載到的字幕一律交給 subtitle_to_text.py 轉成乾淨純文本
# Step 4: 只有整條字幕鏈路失敗，才降級到 Whisper
```

## 当前标准化流程

1. 任何视频链接，先判断字幕，不直接先跑 Whisper。
2. 默认优先使用 `get_best_subtitles.sh`。
3. 如果字幕内容里有中文，就按中文链路继续。
4. 如果判断到主要是英文内容，或者 `get_best_subtitles.sh` 这条链路报错/不稳定，再切到 `get_best_subtitles_en.sh`，优先抓 `en-orig` / `en`。
5. 如果 `get_best_subtitles.sh` 和 `get_best_subtitles_en.sh` 都失效，就使用 Chrome 打开 `https://downsub.com/`，输入视频链接，选择合适的 `RAW` 字幕作为 fallback。
6. 如果所有字幕链路都失败（包括 DownSub 也拿不到可用字幕），就降级到 Whisper 做转写。
7. 字幕文件、DownSub RAW 内容或 Whisper 转写结果统一整理成纯文本，再进入总结步骤。
8. 英文视频主流程改为：英文字幕纯文本 → DeepSeek 先总结英文内容 → DeepSeek 输出中文总结稿 → Qwen3-TTS。
9. 中文视频主流程改为：中文字幕/中文转录 → DeepSeek 中文总结稿 → Qwen3-TTS。
10. 总结稿要求：尽量不少于原文三分之一，但不超过 3000 字。
11. 总结稿必须分成自然段，尽量 300~500 字一段，方便后续音频制作。
12. `summarize_transcript.py` 不再作为主流程步骤，只保留为备用/实验脚本。
13. 最终交给 Qwen3-TTS 生成音频，并发送到 Discord。

## 新增辅助脚本

- `/home/openclaw/.openclaw/workspace/scripts/get_best_subtitles.sh`
- `/home/openclaw/.openclaw/workspace/scripts/get_best_subtitles_en.sh`
- `/home/openclaw/.openclaw/workspace/scripts/downsub_raw_fetch.sh`
- `/home/openclaw/.openclaw/workspace/scripts/subtitle_to_text.py`
- `/home/openclaw/.openclaw/workspace/scripts/subtitle_debug.sh`

## Qwen3-TTS 設置

- **音色**: Serena（溫柔女聲）
- **語速**: 舒緩從容，語速稍慢
- **提示詞**: "用特別溫柔親切的語氣說，節奏舒緩從容，請溫柔且有耐心"
- **模型**: `~/.cache/models/qwen-tts-0.6B-CustomVoice/`

## 使用方式

```bash
bash ~/.openclaw/workspace/skills/youtube-summary-qwen/scripts/summarize.sh "YouTube_URL"
```

## 輸出

1. **文字摘要** (Discord 文字訊息，300字以内)
2. **語音摘要** (Discord 音頻訊息，Serena 溫柔女聲)

## 腳本列表

- `scripts/summarize.sh` - 主腳本（字幕優先 → Whisper 降級）
- `scripts/tts_only.py` - 獨立 TTS 腳本
- `scripts/transcript_only.sh` - 僅下載字幕腳本

## 当前默认总结路径

### 中文视频
字幕纯文本 → `deepseek-summary-browser` → Qwen3-TTS

### 英文视频
优先 `get_best_subtitles.sh`，异常时切 `get_best_subtitles_en.sh`，仍失败时使用 Chrome + DownSub 提取 English RAW；如果连 DownSub 也失败，则降级到 Whisper 转写 → 英文纯文本 → `deepseek-summary-browser` 先总结英文内容，再输出中文分段稿 → Qwen3-TTS

### 中文字幕缺失 / 所有字幕链失败
直接降级到 Whisper 转写，再进入后续总结与 TTS。

也就是说，YouTube 视频总结现在默认优先使用浏览器中的 DeepSeek 做在线总结，再把返回的中文分段稿交给 Qwen3-TTS；而字幕不可得时，保留 Whisper 作为最终兜底方案。`summarize_transcript.py` 不再作为主流程步骤。

## 備註

- 字幕轉文字成功率約 70-80%（取決於影片是否開放字幕）
- Whisper 識別成功率接近 100%
- 摘要保持 **3000字以內**
