#!/usr/bin/env python3
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PROMPT_TEMPLATE_ZH = """请把下面这份中文视频字幕或转写内容，总结成一份适合中文语音朗读的中文总结稿，并严格遵守：
1. 总结长度尽量不少于原文信息密度的三分之一，但总字数不要超过3000字。
2. 输出必须分成多个自然段。
3. 每段尽量控制在300到500字。
4. 不要写成一个大整段。
5. 不要加入原文没有的事实。
6. 保留核心观点、时间线、因果关系与重要细节。
7. 直接输出中文总结正文，不要写额外前言、标题或说明。

以下是中文原文：

{text}
"""

PROMPT_TEMPLATE_EN = """请把下面这份英文视频字幕内容，先理解并总结其核心观点、结构、论证逻辑和重要细节，然后直接输出一份适合中文语音朗读的中文总结稿，并严格遵守：
1. 先完成英文内容理解，再输出中文，不要逐句硬翻。
2. 总结长度尽量不少于原文信息密度的三分之一，但总字数不要超过3000字。
3. 输出必须分成多个自然段。
4. 每段尽量控制在300到500字。
5. 不要写成一个大整段。
6. 不要加入原文没有的事实。
7. 保留核心观点、时间线、因果关系与重要细节。
8. 直接输出中文总结正文，不要写额外前言、标题或说明。

以下是英文字幕原文：

{text}
"""


def run(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)
    return result.stdout


def get_page_id():
    data = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read().decode())
    for p in data:
        if p.get('type') == 'page' and 'deepseek.com' in p.get('url', ''):
            return p['id']
    for p in data:
        if p.get('type') == 'page' and p.get('url') == 'chrome://newtab/':
            return p['id']
    for p in data:
        if p.get('type') == 'page':
            return p['id']
    return None


def get_textbox_ref(snapshot_text: str):
    for line in snapshot_text.splitlines():
        if 'textbox' in line and '[ref=' in line:
            return line.split('[ref=')[1].split(']')[0]
    return None


def estimate_wait_time(text: str) -> int:
    """根据文本长度预估 DeepSeek 总结所需等待时间（秒）。"""
    transcript_len = len(text.strip())
    estimated_summary = min(transcript_len // 3, 3000)
    generation_time = estimated_summary / 30
    return int(generation_time + 20)


def main():
    if len(sys.argv) < 3:
        print('用法: deepseek_browser_summary.py <input_txt> <output_txt> [zh|en]', file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    lang_mode = sys.argv[3] if len(sys.argv) >= 4 else 'zh'
    text = input_path.read_text(encoding='utf-8', errors='ignore').strip()
    if not text:
        print('输入文本为空', file=sys.stderr)
        sys.exit(2)

    template = PROMPT_TEMPLATE_EN if lang_mode == 'en' else PROMPT_TEMPLATE_ZH
    prompt = template.format(text=text[:18000])

    # 动态计算等待时间
    wait_time = estimate_wait_time(text)
    print(f'预估等待时间: {wait_time} 秒 (字幕 {len(text)} 字，预估总结 ~{min(len(text)//3, 3000)} 字)', file=sys.stderr)

    page_id = get_page_id()
    if not page_id:
        print('找不到可用的 Chrome page id', file=sys.stderr)
        sys.exit(3)

    run(f'agent-browser connect ws://127.0.0.1:9222/devtools/page/{page_id}')
    run('agent-browser open "https://chat.deepseek.com/"')
    time.sleep(6)

    snap = run('agent-browser snapshot')
    textbox_ref = get_textbox_ref(snap)
    if not textbox_ref:
        print('找不到 DeepSeek 输入框', file=sys.stderr)
        sys.exit(4)

    prompt_file = Path('/home/openclaw/.openclaw/workspace/tmp/deepseek_prompt.txt')
    prompt_file.write_text(prompt, encoding='utf-8')

    # 清空并用 keyboard type 从文件内容输入，避免 shell 转义地狱
    run(f'agent-browser click ref={textbox_ref}')
    time.sleep(1)
    run(f'agent-browser fill ref={textbox_ref} ""')

    chunk_size = 1200
    for i in range(0, len(prompt), chunk_size):
        chunk = prompt[i:i+chunk_size]
        chunk_file = Path('/home/openclaw/.openclaw/workspace/tmp/deepseek_chunk.txt')
        chunk_file.write_text(chunk, encoding='utf-8')
        safe = chunk.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        run(f'agent-browser keyboard type "{safe}"')
        time.sleep(0.5)

    run('agent-browser press Enter')
    time.sleep(wait_time)

    result = run('agent-browser snapshot')
    output_path.write_text(result, encoding='utf-8')
    print(f'✅ DeepSeek 输出已保存: {output_path}')


if __name__ == '__main__':
    main()
