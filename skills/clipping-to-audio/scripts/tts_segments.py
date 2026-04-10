#!/usr/bin/env python3
import argparse
import json
import math
import os
import subprocess
from pathlib import Path

WORK_DIR = Path("/home/openclaw/.openclaw/workspace/tmp")
FINAL_AUDIO_DIR = Path("/home/openclaw/.openclaw/workspace/audio-news")
IMPORT_PY = "/home/openclaw/.openclaw/workspace/scripts/import_clippings_to_duckdb.py"
DUCKDB_PY = "/home/openclaw/.openclaw/duckdb-env/bin/python"
LOG_GPU_TASK_PY = "/home/openclaw/.openclaw/workspace/scripts/log_gpu_task.py"
TTS_PY = "/home/openclaw/.openclaw/workspace/skills/youtube-summary-qwen/scripts/tts_only_1.7B.py"
TTS_ENV = "/home/openclaw/.openclaw/qwen-tts-env/bin/python"
DISCORD_CHANNEL = "1486326928578183270"


def run(cmd, **kwargs):
    return subprocess.run(cmd, text=True, capture_output=True, check=True, **kwargs)


def set_perf():
    subprocess.run(["sudo", "cpupower", "frequency-set", "-g", "performance"], check=False)


def restore_power(_original=None):
    subprocess.run(["sudo", "cpupower", "frequency-set", "-g", "powersave"], check=False)


def stop_gdm():
    active = subprocess.run(["systemctl", "is-active", "gdm3"], capture_output=True, text=True).stdout.strip()
    if active == "active":
        subprocess.run(["sudo", "systemctl", "stop", "gdm3"], check=False)
        return True
    return False


def start_gdm():
    subprocess.run(["sudo", "systemctl", "start", "gdm3"], check=False)


def reset_nvidia_uvm_or_fail():
    rm = subprocess.run(["sudo", "rmmod", "nvidia_uvm"], capture_output=True, text=True)
    if rm.returncode != 0:
        raise RuntimeError(f"rmmod nvidia_uvm failed: {rm.stderr.strip() or rm.stdout.strip()}")
    mod = subprocess.run(["sudo", "modprobe", "nvidia_uvm"], capture_output=True, text=True)
    if mod.returncode != 0:
        raise RuntimeError(f"modprobe nvidia_uvm failed: {mod.stderr.strip() or mod.stdout.strip()}")


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
    out_dir = wavs[0].parent
    silence_wav = out_dir / "silence_1s.wav"
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", "1", str(silence_wav), "-y"
    ], check=True, capture_output=True)

    list_file = out_dir / "merge_gap1.list.txt"
    with list_file.open("w", encoding="utf-8") as f:
        for w in wavs:
            f.write(f"file '{w}'\n")
            f.write(f"file '{silence_wav}'\n")

    merged_wav = out_dir / "merged.wav"
    slowed_wav = out_dir / "merged.slowed.wav"
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


def sync_duckdb(source_file: str | None):
    if not source_file:
        return
    subprocess.run([DUCKDB_PY, IMPORT_PY, source_file], check=True)


def log_gpu_task_start(title: str, text_file: str) -> int | None:
    try:
        out = run([
            "python3", LOG_GPU_TASK_PY, "start",
            "--task-name", f"clipping-to-audio: {title}",
            "--task-type", "clipping-to-audio",
            "--input-path", text_file,
            "--model-name", "Qwen3-TTS-1.7B-CustomVoice",
        ]).stdout.strip()
        return json.loads(out).get("id")
    except Exception:
        return None


def log_gpu_task_end(task_id: int | None, status: str, output_path: str | None = None, error_message: str | None = None):
    if not task_id:
        return
    cmd = ["python3", LOG_GPU_TASK_PY, "end", "--id", str(task_id), "--status", status, "--model-name", "Qwen3-TTS"]
    if output_path:
        cmd += ["--output-path", output_path]
    if error_message:
        cmd += ["--error-message", error_message]
    subprocess.run(cmd, check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text_file")
    ap.add_argument("--title", required=True)
    ap.add_argument("--source-file")
    args = ap.parse_args()

    gdm_was_running = stop_gdm()
    task_id = log_gpu_task_start(args.title, args.text_file)
    try:
        reset_nvidia_uvm_or_fail()
        set_perf()
        out_dir, wavs = synthesize_segments(Path(args.text_file), args.title)
        FINAL_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        final_mp3 = FINAL_AUDIO_DIR / f"{args.title}.final.mp3"
        merge_mp3(wavs, final_mp3)
        sync_duckdb(args.source_file)
        send_discord(final_mp3, args.title)
        log_gpu_task_end(task_id, "completed", str(final_mp3))
        print(json.dumps({"final_mp3": str(final_mp3), "segments": len(wavs), "source_file": args.source_file}, ensure_ascii=False))
    except Exception as e:
        log_gpu_task_end(task_id, "failed", error_message=str(e))
        raise
    finally:
        if gdm_was_running:
            start_gdm()
        restore_power()


if __name__ == "__main__":
    main()
