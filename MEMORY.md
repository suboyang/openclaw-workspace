# MEMORY.md - 台台小助手长期记忆

## 📅 重要待办事项记录

### 2026年4月4日
- **GPU升级**: T1000 → **NVIDIA A2000 8GB** (Ampere, FP16)
- **⚠️ 重要原則**: OCR、視頻轉碼、語音識別、TTS、語音理解，**第一優先使用本地 A2000 GPU 推理**

### 2026年3月31日

## 🛠️ 已安装技能记录

### 核心技能
1. **find-skills-skill** - 搜索和发现OpenClaw技能
2. **self-improving-agent-cn** - AI自我改进与记忆系统
3. **excel-xlsx** - Excel/XLSX文件处理
4. **discord** - Discord控制与交互
5. **word-docx** - Word文档处理
6. **ocr-local** - 本地OCR识别
7. **weather** - 天气查询
8. **local-whisper** - 本地语音转文本

## 🎯 用户偏好记录

### 文件分享
- **默认24小时有效期**，HTTP server 自动关闭

### 语音识别（STT）默认模型
- **默认**: ModelScope Paraformer-large（FunASR 引擎，A2000 GPU 加速）
- **备用**: Whisper CLI（CPU / 多语言）
- 模型路径: `/home/openclaw/.cache/modelscope/hub/models/damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch`
- 脚本: `/home/openclaw/.openclaw/workspace/skills/openai-whisper/scripts/transcribe.sh`


- **通用目录**: `/mnt/nas_data/tmp/{photos,videos,audio}`
- **YouTube 下载**: `/mnt/nas_data/tmp/youtube`
- **edge-tts 音頻**: `/mnt/nas_data/tmp/edge-tts`
- **SD 图片输出**: `/mnt/nas_data/tmp/sd_output`（ComfyUI SD 1.5）
- **自动清理**: 每天凌晨 3:00 删除 30 天前内容
- **cron**: `0 3 * * *` ✅



### 工作习惯
- 喜欢安装实用技能
- 关注天气信息
- 使用语音输入
- 需要待办事项提醒

### YouTube 影片總結流程（標準化）
1. **yt-dlp** 下載（ytdlp-env 環境）
2. **優先字幕**：--write-subs --write-auto-subs
3. **無字幕時**：下載音頻 → Whisper (large-v3-turbo, GPU)
4. **總結**：3000字以內
5. **TTS**：Edge-TTS zh-TW-HsiaoChenNeural（台灣腔）
6. **發送**：Discord 語音消息
- 腳本：`/home/openclaw/.openclaw/workspace/skills/youtube-summary/scripts/summarize.sh`

### Shell 环境
- **Shell**: oh-my-zsh（已切换完成）


- 使用OpenClaw系统
- 通过Discord交互
- 安装多个生产力技能

## 📝 重要事件时间线

### 2026年3月
- **3月30日**: 完成多项任务（音乐整理、NAS配置、开机通知系统）
- **3月31日**: 
  - 上午: 安装多个技能，查询天气
  - 中午: 记录"回复AVL邮件"待办事项

## 💡 学习与改进

### 从交互中学到的
1. 用户经常查询天气信息
2. 需要语音转文本功能
3. 重视文档处理能力
4. 需要任务提醒功能

### 待改进
1. 建立更完善的提醒系统
2. 优化任务管理流程
3. 增强日历集成

---
*最后更新: 2026-03-31 12:53*
*记忆系统: 台台小助手*

### 2026年4月5日
- **Qwen3-TTS-0.6B-CustomVoice** 测试成功，用户满意
  - 模型路径: `~/.cache/models/qwen-tts-0.6B-CustomVoice/`
  - 音色: Serena（溫柔女聲）表現優秀
  - 之後整理語音資料優先使用此模型
  - Python 環境: `~/.openclaw/qwen-tts-env/`

### 2026年4月5日 10:38
- **youtube-summary-qwen skill** 更新完畢
  - 優先使用字幕下載（video-transcript-downloader）
  - 無字幕時降級到 Whisper Large V3 Turbo
  - TTS 設置：Serena 溫柔女聲，語速稍慢
  - 已整合到工作流程

### 2026年4月5日 17:52
- **音頻文件命名規則**：總結音頻文件必須與YouTube影片標題一致
  - 例如：影片標題為「秦晖：塞尔维亚和南斯拉夫简史（第一讲）」，音頻檔名也應為「秦晖：塞尔维亚和南斯拉夫简史（第一讲）.wav/.mp3」
  - 避免：隨機UUID或時間戳命名

### 2026年4月5日 17:56
- **總結內容長度規則**：總結音頻時長 ≥ 原始影片時長的25%
  - 例如：40分鐘影片 → 至少10分鐘音頻
  - 目前約8000字摘要 → 約5-8分鐘音頻（Serena慢速）
  - 需確保摘要內容充分，不過度濃縮

### 2026年4月5日 21:07
- **GPU 任務工作流程**：
  - 跑 GPU 任務（Qwen3-TTS/Whisper/SD）前先停 GDM：`sudo systemctl stop gdm3`
  - 任務完成後開 GDM：`sudo systemctl start gdm3`
  - 原因：A2000 同時供顯示和計算，高負載時 Xorg/GDM 會崩潰導致 GPU 掛掉

### 2026年4月5日 21:08
- **GPU 任務自動化**：summarize.sh 現在會自動停/開 GDM
  - 腳本使用 trap確保任何情況下都會恢復 GDM
  - 手動干預需求降到零
