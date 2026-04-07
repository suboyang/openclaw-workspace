#!/bin/bash
# Paraformer STT using FunASR
# Default: ModelScope Paraformer-large (GPU accelerated)
# Usage: ./transcribe.sh audio.wav [--model paraformer-large] [--language zh] [--output /path/to/output.txt]

set -e

AUDIO_FILE="$1"
OUTPUT_FILE=""
MODEL="paraformer-large"
LANGUAGE="zh"

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --model|-m)
            MODEL="$2"
            shift 2
            ;;
        --language|-l)
            LANGUAGE="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --json|-j)
            JSON_MODE=1
            shift
            ;;
        --help|-h)
            echo "Usage: $0 <audio_file> [--model MODEL] [--language LANG] [--output FILE] [--json]"
            echo "  Default model: paraformer-large (GPU accelerated)"
            echo "  Default language: zh (Chinese)"
            echo "  Supported models: paraformer-large"
            exit 0
            ;;
        *)
            AUDIO_FILE="$1"
            shift
            ;;
    esac
done

if [ -z "$AUDIO_FILE" ]; then
    echo "Error: Audio file required"
    exit 1
fi

if [ ! -f "$AUDIO_FILE" ]; then
    echo "Error: File not found: $AUDIO_FILE"
    exit 1
fi

echo "🎙️ Paraformer STT (GPU Accelerated)"
echo "   Model: $MODEL"
echo "   Language: $LANGUAGE"
echo "   File: $AUDIO_FILE"

# Use FunASR with Paraformer
MODEL_PATH="/home/openclaw/.cache/modelscope/hub/models/damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"

python3 -c "
import sys
import os
os.environ['MODELSCOPE_CACHE'] = '/home/openclaw/.cache/modelscope'

from funasr import AutoModel

print('Loading Paraformer model...')
model = AutoModel(
    model='$MODEL_PATH',
    device='cuda'
)

print('Transcribing...')
result = model.generate(
    input='$AUDIO_FILE',
    batch_size_s=300,
    merge_vad=True,
    merge_length_s=15
)

text = result[0]['text']
print()
print('=== Result ===')
print(text)

\$JSON_MODE && exit(0)

if [ ! -z \"$OUTPUT_FILE\" ]; then
    echo \"\$text\" > \"$OUTPUT_FILE\"
    echo \"Saved to: $OUTPUT_FILE\"
fi
"
