#!/usr/bin/env python3
"""
Local STT - Default: ModelScope Paraformer-large (GPU accelerated)
Usage: python3 transcribe.py <audio_file> [options]
"""

import sys
import os
import argparse

MODEL_PATH = "/home/openclaw/.cache/modelscope/hub/models/damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"

def transcribe_with_paraformer(audio_path, output_path=None, json_mode=False):
    """Use FunASR Paraformer for STT"""
    os.environ['MODELSCOPE_CACHE'] = '/home/openclaw/.cache/modelscope'
    
    from funasr import AutoModel
    
    print(f"🎙️ Loading Paraformer-large (GPU)...")
    model = AutoModel(model=MODEL_PATH, device='cuda')
    
    print(f"🔍 Transcribing: {audio_path}")
    result = model.generate(
        input=audio_path,
        batch_size_s=300,
        merge_vad=True,
        merge_length_s=15
    )
    
    text = result[0]['text']
    
    if json_mode:
        import json
        output = {
            'text': text,
            'segments': result
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print()
        print("=== Transcription ===")
        print(text)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"\n✅ Saved to: {output_path}")
    
    return text

def transcribe_with_whisper(audio_path, output_path=None, json_mode=False):
    """Use Whisper CLI as backup"""
    import subprocess
    
    cmd = ['whisper', audio_path, '--model', 'small', '--device', 'cuda', '--output_format', 'txt']
    if json_mode:
        cmd.append('--output_format')
        cmd.append('json')
    
    print(f"🎙️ Using Whisper CLI (backup)...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout)
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
    else:
        print(f"Error: {result.stderr}")
    
    return result.stdout

def main():
    parser = argparse.ArgumentParser(description='Local STT with Paraformer (default GPU)')
    parser.add_argument('audio', help='Audio file path')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')
    parser.add_argument('--whisper', '-w', action='store_true', help='Use Whisper instead of Paraformer')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.audio):
        print(f"Error: File not found: {args.audio}")
        sys.exit(1)
    
    if args.whisper:
        transcribe_with_whisper(args.audio, args.output, args.json)
    else:
        transcribe_with_paraformer(args.audio, args.output, args.json)

if __name__ == '__main__':
    main()
