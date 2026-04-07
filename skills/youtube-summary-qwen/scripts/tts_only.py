#!/usr/bin/env python3
"""
Qwen3-TTS 獨立語音生成腳本
用法: python tts_only.py "文字檔案" "輸出.wav"
"""

import sys
import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel

MODEL_PATH = "/home/openclaw/.cache/models/qwen-tts-0.6B-CustomVoice"

def generate_speech(text: str, output_path: str):
    print(f"Loading Qwen3-TTS model from {MODEL_PATH}...")
    model = Qwen3TTSModel.from_pretrained(
        MODEL_PATH,
        device_map="cuda:0",
        dtype=torch.bfloat16,
    )
    
    print(f"Generating speech with Serena (溫柔慢速)...")
    wavs, sr = model.generate_custom_voice(
        text=text,
        language="Chinese",
        speaker="Serena",
        instruct="用特別溫柔親切的語氣說，節奏舒緩從容，語速稍慢，請溫柔且有耐心地朗讀",
    )
    
    sf.write(output_path, wavs[0], sr)
    print(f"Saved to: {output_path}")
    print(f"Duration: {len(wavs[0])/sr:.1f} seconds")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python tts_only.py <文字檔案> <輸出.wav>")
        sys.exit(1)
    
    text_file = sys.argv[1]
    output_path = sys.argv[2]
    
    with open(text_file, "r", encoding="utf-8") as f:
        text = f.read()
    
    generate_speech(text, output_path)
