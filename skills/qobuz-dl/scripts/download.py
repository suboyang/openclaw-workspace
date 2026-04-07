#!/usr/bin/env python3
"""
Qobuz Downloader Skill
Downloads albums from Qobuz using qobuz-dl CLI

Usage:
    python3 download.py <qobuz_url> [quality] [output_dir]
    python3 download.py "https://play.qobuz.com/album/0074644545029"
    python3 download.py "URL" 27 "/path/to/folder"
"""

import subprocess
import sys
import os

DEFAULT_QUALITY = "7"
DEFAULT_DIR = "/home/openclaw/nas/Daphile/Qobuz Download"

def get_quality_label(q):
    labels = {
        "5": "MP3 320kbps",
        "6": "FLAC 16/44.1",
        "7": "FLAC 24/≤96kHz",
        "27": "FLAC 24/>96kHz"
    }
    return labels.get(q, f"Quality {q}")

def download(url, quality=DEFAULT_QUALITY, output_dir=DEFAULT_DIR):
    os.makedirs(output_dir, exist_ok=True)
    
    quality_label = get_quality_label(quality)
    
    print(f"🎵 Qobuz Downloader")
    print(f"   URL: {url}")
    print(f"   Quality: {quality_label}")
    print(f"   Output: {output_dir}")
    print()
    
    cmd = [
        "qobuz-dl", "dl",
        url,
        "-d", output_dir,
        "-q", quality,
        "--embed-art"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd)
    return result.returncode

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 download.py <qobuz_url> [quality] [output_dir]")
        print("Example: python3 download.py 'https://play.qobuz.com/album/0074644545029'")
        sys.exit(1)
    
    url = sys.argv[1]
    quality = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_QUALITY
    output_dir = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_DIR
    
    exit_code = download(url, quality, output_dir)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
