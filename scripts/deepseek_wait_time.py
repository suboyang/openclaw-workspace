#!/usr/bin/env python3
"""
DeepSeek 等待时间计算器
根据字幕/转写文本长度，预估 DeepSeek 总结所需的等待时间。

原则：
- 总结字数 >= 原文 1/3，但不超过 3000 字
- DeepSeek 生成速度约 30 字/秒
- 额外加 20 秒安全缓冲
"""

import sys


def estimate_summary_wait_time(transcript_text: str) -> int:
    """
    根据字幕文本长度，预估 DeepSeek 总结所需的等待时间（秒）。

    返回值：建议等待秒数
    """
    transcript_len = len(transcript_text.strip())

    # 预估总结字数：原文 1/3，上限 3000 字
    estimated_summary_len = min(transcript_len // 3, 3000)

    # DeepSeek 生成速度约 30 字/秒
    generation_time = estimated_summary_len / 30

    # 额外安全缓冲 20 秒
    total_wait = generation_time + 20

    return int(total_wait)


def main():
    if len(sys.argv) < 2:
        print("用法: python deepseek_wait_time.py <transcript_file>")
        print("或:  python deepseek_wait_time.py --text '字幕文本内容'")
        sys.exit(1)

    if sys.argv[1] == "--text" and len(sys.argv) >= 3:
        transcript_text = sys.argv[2]
    else:
        from pathlib import Path
        transcript_path = Path(sys.argv[1])
        if not transcript_path.exists():
            print(f"文件不存在: {transcript_path}", file=sys.stderr)
            sys.exit(1)
        transcript_text = transcript_path.read_text(encoding='utf-8', errors='ignore')

    transcript_len = len(transcript_text.strip())
    estimated_summary = min(transcript_len // 3, 3000)
    wait_time = estimate_summary_wait_time(transcript_text)

    print(f"转写文本长度: {transcript_len} 字")
    print(f"预估总结字数: {estimated_summary} 字 (原文 1/3，上限 3000)")
    print(f"DeepSeek 生成速度: 30 字/秒")
    print(f"预估生成时间: {estimated_summary / 30:.1f} 秒")
    print(f"安全缓冲: +20 秒")
    print(f"---")
    print(f"建议等待时间: {wait_time} 秒")

    return wait_time


if __name__ == "__main__":
    main()
