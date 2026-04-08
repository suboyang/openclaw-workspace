#!/usr/bin/env python3
"""
字幕下载逻辑 - 仅下载字幕，不做总结
用法: python3 summarize.py "YouTube_URL"
"""
import subprocess
import sys
import time
from pathlib import Path

WORK_DIR = Path("/home/openclaw/.openclaw/workspace/tmp")
WORK_DIR.mkdir(parents=True, exist_ok=True)

YTDLP_BIN = "/home/openclaw/.openclaw/ytdlp-env/bin/yt-dlp"
BEST_SUB_SCRIPT = "/home/openclaw/.openclaw/workspace/scripts/get_best_subtitles.sh"
BEST_SUB_EN_SCRIPT = "/home/openclaw/.openclaw/workspace/scripts/get_best_subtitles_en.sh"
DOWNSUB_RAW_SCRIPT = "/home/openclaw/.openclaw/workspace/scripts/downsub_raw_fetch.sh"
SUBTITLE_TO_TEXT_SCRIPT = "/home/openclaw/.openclaw/workspace/scripts/subtitle_to_text.py"


def run(cmd, timeout=120):
    """执行 shell 命令"""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )
    return result


def get_video_title(url: str) -> str:
    """获取视频标题"""
    result = run(f"{YTDLP_BIN} --get-title --no-playlist {url}", timeout=30)
    title = result.stdout.strip().split('\n')[0]
    # 清理非法字符
    import re
    title = re.sub(r'[\\/:*?"<>|]', '_', title)[:100]
    return title


def check_subtitle_available(url: str) -> tuple[bool, bool]:
    """
    检查视频是否有字幕
    返回 (has_subtitle, is_chinese_subtitle)
    """
    print("🔍 檢查字幕可用性...")
    result = run(f"{YTDLP_BIN} --list-subs --no-playlist {url}", timeout=30)
    stdout = result.stdout

    has_sub = False
    has_zh = False
    has_en = False

    # 解析 --list-subs 输出
    for line in stdout.split('\n'):
        # 中文字幕
        if 'zh' in line and ('vtt' in line or 'ttml' in line or 'srv' in line):
            has_sub = True
            has_zh = True
        # 英文字幕
        if 'en' in line and ('vtt' in line or 'ttml' in line or 'srv' in line):
            has_sub = True
            has_en = True

    print(f"  中文字幕: {'✅' if has_zh else '❌'}")
    print(f"  英文字幕: {'✅' if has_en else '❌'}")
    return has_sub, has_zh


def download_best_subtitle(url: str, title: str) -> Path | None:
    """
    下载中文字幕：get_best_subtitles.sh
    格式优先级: vtt > ttml > srv3 > srv2 > srv1 > json3
    """
    print("\n📥 嘗試下載中文字幕 (get_best_subtitles.sh)...")
    sub_dir = WORK_DIR / f"subs_zh_{int(time.time())}"
    sub_dir.mkdir(parents=True, exist_ok=True)

    result = run(f"bash {BEST_SUB_SCRIPT} {url} {sub_dir}", timeout=180)
    print(f"  stdout: {result.stdout[:500]}")

    # 查找字幕文件
    for ext in ['.vtt', '.ttml', '.srv3', '.srv2', '.srv1', '.json3']:
        files = list(sub_dir.glob(f"*{ext}"))
        if files:
            sub_file = files[0]
            print(f"  ✅ 找到字幕: {sub_file.name} ({sub_file.stat().st_size} bytes)")
            return sub_file

    print("  ❌ 未找到字幕文件")
    return None


def download_en_subtitle(url: str, title: str) -> Path | None:
    """
    下载英文字幕：get_best_subtitles_en.sh
    """
    print("\n📥 嘗試下載英文字幕 (get_best_subtitles_en.sh)...")
    sub_dir = WORK_DIR / f"subs_en_{int(time.time())}"
    sub_dir.mkdir(parents=True, exist_ok=True)

    result = run(f"bash {BEST_SUB_EN_SCRIPT} {url} {sub_dir}", timeout=180)
    print(f"  stdout: {result.stdout[:500]}")

    for ext in ['.vtt', '.ttml', '.srv3', '.srv2', '.srv1', '.json3']:
        files = list(sub_dir.glob(f"*{ext}"))
        if files:
            sub_file = files[0]
            print(f"  ✅ 找到字幕: {sub_file.name} ({sub_file.stat().st_size} bytes)")
            return sub_file

    print("  ❌ 未找到字幕文件")
    return None


def download_downsub_raw(url: str, title: str) -> Path | None:
    """
    Chrome 打开 DownSub 抓 RAW 字幕
    """
    print("\n📥 嘗試 DownSub RAW (Chrome)...")
    downsub_file = WORK_DIR / f"downsub_raw_{int(time.time())}.txt"

    result = run(f"bash {DOWNSUB_RAW_SCRIPT} {url} auto {downsub_file}", timeout=180)
    print(f"  stdout: {result.stdout[:500]}")
    print(f"  stderr: {result.stderr[:500]}")

    if downsub_file.exists() and downsub_file.stat().st_size > 100:
        print(f"  ✅ DownSub RAW 成功: {downsub_file.stat().st_size} bytes")
        return downsub_file

    print("  ❌ DownSub RAW 失敗")
    return None


def subtitle_to_text(sub_file: Path) -> Path:
    """字幕文件转纯文本"""
    text_file = sub_file.with_suffix('.txt')
    result = subprocess.run(
        ["python3", str(SUBTITLE_TO_TEXT_SCRIPT), str(sub_file), str(text_file)],
        capture_output=True, text=True, timeout=60
    )
    print(f"  轉文字: {result.stdout.strip()}")
    return text_file


def whisper_transcribe(url: str, title: str) -> Path:
    """Whisper 语音识别"""
    print("\n🎤 降級到 Whisper 語音識別...")

    # 下载音频
    audio_file = WORK_DIR / f"audio_{title}_{int(time.time())}.mp3"
    print("  📥 下載音頻...")
    result = run(f'{YTDLP_BIN} -x --audio-format mp3 -o "{audio_file}" "{url}"', timeout=300)
    if result.returncode != 0:
        print(f"  ❌ 下載失敗: {result.stderr[:300]}")
        raise RuntimeError("音频下载失败")

    # Whisper 识别
    print("  🎤 Whisper 識別中...")
    transcript_file = audio_file.with_suffix('.txt')
    
    # 直接调用 subprocess，不走 run() 函数
    whisper_cmd = [
        'whisper', str(audio_file),
        '--model', 'large-v3-turbo',
        '--model_dir', '/home/openclaw/.cache/whisper',
        '--output_dir', str(WORK_DIR),
        '--output_format', 'txt'
    ]
    result = subprocess.run(
        whisper_cmd,
        capture_output=True, text=True, timeout=600
    )
    if result.returncode != 0:
        print(f"  ❌ Whisper 失敗: {result.stderr[:300]}")
        raise RuntimeError("Whisper 识别失败")

    # whisper 输出到 WORK_DIR，文件名是 audio_file.with_suffix('.txt')
    if not transcript_file.exists():
        # 可能在其他位置
        candidates = list(WORK_DIR.glob(f"audio_{title}_*.txt"))
        if candidates:
            transcript_file = candidates[-1]

    # 清理音频
    if audio_file.exists():
        audio_file.unlink()

    print(f"  ✅ Whisper 完成: {transcript_file}")
    return transcript_file


def main():
    if len(sys.argv) < 2:
        print("用法: python3 summarize.py \"YouTube_URL\"")
        sys.exit(1)

    url = sys.argv[1]
    print(f"📺 處理: {url}\n")

    # Step 0: 获取标题
    title = get_video_title(url)
    print(f"📌 標題: {title}\n")

    # Step 1: 检查字幕
    has_sub, has_zh = check_subtitle_available(url)

    transcript_file = None

    if has_sub:
        # 有字幕 → 按优先级下载
        if has_zh:
            # 先试中文字幕
            sub_file = download_best_subtitle(url, title)
            if sub_file:
                transcript_file = subtitle_to_text(sub_file)
                print(f"\n✅ 成功: {transcript_file}")
                print(f"   字数: {transcript_file.stat().st_size} bytes")
            else:
                # 中文字幕失败 → 试英文字幕
                sub_file = download_en_subtitle(url, title)
                if sub_file:
                    transcript_file = subtitle_to_text(sub_file)
                    print(f"\n✅ 成功 (英文): {transcript_file}")
                else:
                    # 英文字幕也失败 → 试 DownSub
                    ds_file = download_downsub_raw(url, title)
                    if ds_file:
                        transcript_file = ds_file
                        print(f"\n✅ 成功 (DownSub): {transcript_file}")
        else:
            # 只有英文字幕
            sub_file = download_en_subtitle(url, title)
            if sub_file:
                transcript_file = subtitle_to_text(sub_file)
                print(f"\n✅ 成功: {transcript_file}")
            else:
                ds_file = download_downsub_raw(url, title)
                if ds_file:
                    transcript_file = ds_file
                    print(f"\n✅ 成功 (DownSub): {transcript_file}")
    else:
        # 无字幕 → Whisper
        try:
            transcript_file = whisper_transcribe(url, title)
            print(f"\n✅ Whisper 完成: {transcript_file}")
            print(f"   字数: {transcript_file.stat().st_size} bytes")
        except Exception as e:
            print(f"\n❌ 全部失敗: {e}")
            sys.exit(1)

    if not transcript_file or not transcript_file.exists():
        print("\n❌ 轉錄失敗")
        sys.exit(1)

    print(f"\n📁 輸出: {transcript_file}")
    print(f"📁 大小: {transcript_file.stat().st_size} bytes")


if __name__ == "__main__":
    main()
