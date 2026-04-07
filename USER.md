# USER.md - About Your Human


# User Profile: OpenClaw Master

## 核心身份 (Core Identity)
- **职业背景**: 效力于联想 (Lenovo)，熟悉企业级硬件逻辑与技术支持流程。
- **技术栈**: 熟练使用 Ubuntu 24.04 LTS，精通 Python 虚拟环境 (venv) 管理，具备处理英伟达 (NVIDIA) 驱动与 CUDA 环境的实战经验。
- **当前项目**: 正在深度调优 OpenClaw 助手，并在本地部署高性能语音识别 (SenseVoiceSmall / Faster-Whisper) 与量化交易系统。

## 硬件环境 (Hardware Context)
- **运算核心**: NVIDIA **RTX A2000 Laptop** (OEM) 8GB GDDR6
  - CUDA: 2560 cores | Base/Boost: 1215-1687 MHz
  - Tensor Core: 80 | RT Core: 20
  - Bus: 128-bit | 頻寬: 192 GB/s
  - FP32: 8 TFLOPS | **FP16: 8 TFLOPS**
  - *注意*: 助手在提供模型建议时，应优先考虑 8GB 显存上限。
- **运算核心**: 使用联想P3 Ultal Gen2 作为家庭数据中心的核心服务器。
  - *注意*: 助手在提供模型建议时，应优先考虑 8GB 显存上限。A2000 FP16 性能優秀，SD 推理約 3-4 秒。
- **存储布局**: 
  - 本地 SSD (系统与工作区)。
  - 远程 NAS (192.168.180.162) 挂载点：
    - `/mnt/nas_hgst`: 8T 电影仓。   
    - `/mnt/nas_toshiba`: 3T 电影仓。
    - `/mnt/nas_wdc`: 5T 下载盘。
    - `/mnt/nas`: 960GB 常用资料库。
    - `/home/openclaw/nas/Daphile/Qobuz Download`:  音乐库。


- **网络环境**: 长期使用 Proxy/VPN 访问全球技术资源，具备 10 年以上的科学上网经验。

## 兴趣与偏好 (Interests & Preferences)
- **学习目标**: 
  - 深入研究量化交易 (Quantitative Trading)，结合 Python 与金融背景。
  - 提升英语能力，目前正与女朋友一起练习，计划阅读英文原版《1984》。
  - 喜欢使用Qobuz查找并下载音乐, 家里部署了Hifi系统。
- **沟通风格**: 
  - 拒绝废话，喜欢直接、准确的指令和路径分析。
  - 偏好自动化解决方案，讨厌重复的手动配置。

## 助手交互准则 (Interaction Guidelines)
1. **硬件优先**: 在执行 AI 任务前，默认考虑 A2000 的显存分配（8GB FP16）。
2. **GPU 优先原則**: 以下任務**必須優先使用本地 A2000 GPU 推理**：
   - OCR 文字識別
   - 視頻轉碼
   - 語音識別（STT）
   - 文字轉語音（TTS）
   - 語音訊息理解
2. **术语对齐**: 保持专业的技术术语沟通，必要时提供中英双语的技术解释以辅助英语学习。
3. **主动记忆**: 自动记录 NAS 挂载路径的变化及 Python 环境的更新，无需重复提醒。
