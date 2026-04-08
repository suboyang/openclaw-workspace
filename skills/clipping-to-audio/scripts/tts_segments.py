#!/usr/bin/env python3
import argparse
import json
import math
import os
import subprocess
from pathlib import Path

WORK_DIR = Path("/home/openclaw/.openclaw/workspace/tmp")
FINAL_AUDIO_DIR = Path("/home/openclaw/.openclaw/workspace/audio-news")
TTS_PY = "/home/openclaw/.openclaw/workspace/skills/youtube-summary-qwen/scripts/tts_only.py"
TTS_ENV = "/home/openclaw/.openclaw/qwen-tts-env/bin/python"
DISCORD_CHANNEL = "1486326928578183270"


def run(cmd, **kwargs):
    return subprocess.run(cmd, text=True, capture_output=True, check=True, **kwargs)


def get_power_profile():
    try:
        return run(["powerprofilesctl", "get"]).stdout.strip()
    except Exception:
        return ""


def set_perf():
    original = get_power_profile()
    if original and original != "performance":
        subprocess.run(["powerprofilesctl", "set", "performance"], check=False)
    return original


def restore_power(original):
    if original and original != "performance":
        subprocess.run(["powerprofilesctl", "set", original], check=False)
    elif not original:
        subprocess.run(["powerprofilesctl", "set", "power-saver"], check=False)


def stop_gdm():
    active = subprocess.run(["systemctl", "is-active", "gdm3"], capture_output=True, text=True).stdout.strip()
    if active == "active":
        subprocess.run(["sudo", "systemctl", "stop", "gdm3"], check=False)
        return True
    return False


def start_gdm():
    subprocess.run(["sudo", "systemctl", "start", "gdm3"], check=False)


def split_text(text: str, target_chars: int = 260):
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    segments = []
    current = []
    current_len = 0
    for p in paragraphs:
        plen = len(p)
        if current and current_len + plen > target_chars:
            segments.append("\n\n".join(current))
            current = [p]
            current_len = plen
        else:
            current.append(p)
            current_len += plen
    if current:
        segments.append("\n\n".join(current))
    return segments


def synthesize_segments(text_file: Path, title: str):
    text = text_file.read_text(encoding="utf-8", errors="ignore").strip()
    segments = split_text(text)
    out_dir = WORK_DIR / f"clipping_audio_{title}"
    out_dir.mkdir(parents=True, exist_ok=True)
    wavs = []
    for idx, seg in enumerate(segments, start=1):
        seg_txt = out_dir / f"part{idx:02d}.txt"
        seg_wav = out_dir / f"part{idx:02d}.wav"
        seg_txt.write_text(seg, encoding="utf-8")
        env = os.environ.copy()
        env["CUDA_LAUNCH_BLOCKING"] = "1"
        subprocess.run([TTS_ENV, TTS_PY, str(seg_txt), str(seg_wav)], check=True, env=env)
        wavs.append(seg_wav)
    return out_dir, wavs


def merge_mp3(wavs, output_mp3: Path):
    list_file = output_mp3.with_suffix(".list.txt")
    list_file.write_text("\n".join([f"file '{w}'" for w in wavs]), encoding="utf-8")
    merged_wav = output_mp3.with_suffix(".wav")
    slowed_wav = output_mp3.with_suffix(".slowed.wav")
    subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(merged_wav), "-y"], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-i", str(merged_wav), "-filter:a", "atempo=0.95", str(slowed_wav), "-y"], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-i", str(slowed_wav), "-codec:a", "libmp3lame", "-qscale:a", "2", str(output_mp3), "-y"], check=True, capture_output=True)
    return output_mp3


def send_discord(mp3: Path, title: str):
    subprocess.run([
        "openclaw", "message", "send",
        "--channel", "discord",
        "--target", f"channel:{DISCORD_CHANNEL}",
        "--media", str(mp3),
        "--message", f"🎙️ clipping-to-audio - {title}"
    ], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text_file")
    ap.add_argument("--title", required=True)
    args = ap.parse_args()

    original_power = set_perf()
    gdm_was_running = stop_gdm()
    try:
        out_dir, wavs = synthesize_segments(Path(args.text_file), args.title)
        FINAL_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        final_mp3 = FINAL_AUDIO_DIR / f"{args.title}.final.mp3"
        merge_mp3(wavs, final_mp3)
        send_discord(final_mp3, args.title)
        print(json.dumps({"final_mp3": str(final_mp3), "segments": len(wavs)}, ensure_ascii=False))
    finally:
        if gdm_was_running:
            start_gdm()
        restore_power(original_power)


if __name__ == "__main__":
    main()
