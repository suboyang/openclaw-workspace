---
name: local-whisper
description: Local speech-to-text using ModelScope Paraformer-large (GPU) as default, with Whisper CLI as backup.
metadata: {"clawdbot":{"emoji":"🎙️","requires":{"bins":["python3","ffmpeg"]}}}
---

# Local Whisper STT

**Default: ModelScope Paraformer-large (A2000 GPU accelerated)**

## Usage

```bash
# Default: Paraformer-large (GPU)
python3 /home/openclaw/.openclaw/workspace/skills/local-whisper/scripts/transcribe.py audio.wav

# Specify output file
python3 /home/openclaw/.openclaw/workspace/skills/local-whisper/scripts/transcribe.py audio.wav --output result.txt

# JSON output
python3 /home/openclaw/.openclaw/workspace/skills/local-whisper/scripts/transcribe.py audio.wav --json

# Backup: Whisper CLI
whisper audio.wav --model small --device cuda
```

## Models

| Model | Engine | Device | Notes |
|-------|--------|--------|-------|
| **Paraformer-large** | FunASR | A2000 GPU | **Default** - Chinese fastest ✅ |
| Whisper small | OpenAI | CPU/GPU | Backup - multilingual |

## Models Location

- **Paraformer**: `/home/openclaw/.cache/modelscope/hub/models/damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch`
- **Whisper**: `~/.cache/whisper/`

## Scripts

- `/home/openclaw/.openclaw/workspace/skills/local-whisper/scripts/transcribe.py` - Main script (Paraformer default)
