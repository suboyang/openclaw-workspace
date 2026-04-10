---
name: openai-whisper
description: Local speech-to-text using ModelScope Paraformer (GPU accelerated) or Whisper CLI. Default: Paraformer-large on A2000 GPU.
homepage: https://www.modelscope.cn/models/iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch
metadata: {"clawdbot":{"emoji":"🎙️","requires":{"bins":["python3","ffmpeg"]}}}
---

# Local STT (Paraformer + Whisper)

默認使用 **ModelScope Paraformer-large**（GPU 加速），速度快且對中文支援更好。

## 使用方法

```bash
# 基本用法（預設：Paraformer-large，GPU）
./scripts/transcribe.sh audio.wav

# 指定輸出文件
./scripts/transcribe.sh audio.wav --output result.txt

# JSON 輸出
./scripts/transcribe.sh audio.wav --json

# Whisper 備用（CPU）
whisper audio.wav --model small
```

## 預設模型

| 模型 | 引擎 | 設備 | 速度 |
|------|------|------|------|
| **Paraformer-large** | FunASR | A2000 GPU | ~1秒 |

## 安裝的引擎

- **FunASR + Paraformer** — 默認，中文最快（A2000 GPU）
- **Whisper CLI** — 備用，支持多語言

## 模型位置

- Paraformer: `/home/openclaw/.cache/modelscope/hub/models/damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch`
- Whisper: `~/.cache/whisper/`

## 腳本位置

`/home/openclaw/.openclaw/workspace/skills/openai-whisper/scripts/transcribe.sh`
