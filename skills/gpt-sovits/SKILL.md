---
name: gpt-sovits
description: GPT-SoVITS voice cloning and TTS. Train a custom voice model from audio samples, then generate speech with that voice.
metadata:
  openclaw:
    emoji: 🎙️
    requires:
      bins: ["python3", "git", "ffmpeg"]
---

# GPT-SoVITS 語音克隆

GPT-SoVITS 是一個語音克隆 TTS 模型，給予 5-30 秒的音頻樣本即可訓練一個客製化語音模型。

## 工作流程

```
1. 準備音頻樣本（5-30秒，乾淨無噪音）
2. 訓練語音模型（5-10 分鐘 GPU 訓練）
3. 用訓練好的聲音生成 TTS
```

## 快速使用

### 訓練模型
```bash
python3 /home/openclaw/.openclaw/workspace/scripts/gpt-sovits-train.sh /path/to/audio.wav
```

### 生成 TTS
```bash
python3 /home/openclaw/.openclaw/workspace/scripts/gpt-sovits-infer.sh "要說的文字" output.wav
```

## 腳本位置

- 訓練腳本：`/home/openclaw/.openclaw/workspace/scripts/gpt-sovits-train.sh`
- 推理腳本：`/home/openclaw/.openclaw/workspace/scripts/gpt-sovits-infer.sh`
- 模型目錄：`/home/openclaw/gpt-sovits/pretrained_models/`
- GSV 訓練輸出：`/mnt/nas_data/tmp/gpt_sovits_output/`

## 訓練參數

- 默認訓練輪數：10
- 訓練設備：A2000 GPU
- 所需 VRAM：~6GB

## 注意

- 樣本音頻需要清晰，最好是朗讀內容
- 支持中文、英文、日文等多語言
- 訓練完成後會自動保存模型，下次無需重新訓練
