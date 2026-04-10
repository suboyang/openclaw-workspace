#!/usr/bin/env python3
"""
YouTube 影片总结 - 使用 Ollama 本地模型
不再依赖 DeepSeek 浏览器
用法: deepseek_browser_summary.py <input_txt> <output_txt> [zh|en]
"""
import json
import subprocess
import sys
import urllib.request
import requests
from pathlib import Path

# ============ DeepSeek 浏览器方式已注释掉 ============
# 以下为 Ollama 本地推理替代方案
# ===============================================

PROMPT_TEMPLATE_ZH = """请把下面一份中文视频字幕或转写内容，总结成一份适合中文语音朗读的中文总结稿，并严格遵守：
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

PROMPT_TEMPLATE_EN = """请把下面一份英文视频字幕内容，先理解并总结其核心观点、结构、论证逻辑和重要细节，然后直接输出一份适合中文语音朗读的中文总结稿，并严格遵守：
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


OLLAMA_MODEL = "minimax-m2.7:cloud"
OLLAMA_URL = "http://localhost:11434/api/generate"


def run(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)
    return result.stdout


def estimate_wait_time(text: str) -> int:
    """根据文本长度预估 Ollama 总结所需等待时间（秒）。"""
    transcript_len = len(text.strip())
    estimated_summary = min(transcript_len // 3, 3000)
    # Ollama 本地推理速度约 50-100 tokens/秒
    generation_time = estimated_summary / 60
    return int(generation_time + 10)


def ollama_summarize(prompt: str, timeout: int = 600) -> str:
    """调用 Ollama API 进行总结。"""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
        }
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    result = resp.json()
    return result.get("response", "")


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
    print(f'使用 Ollama 总结，模型: {OLLAMA_MODEL}', file=sys.stderr)
    print(f'预估等待时间: {wait_time} 秒 (字幕 {len(text)} 字)', file=sys.stderr)

    # ============ DeepSeek 浏览器方式已注释掉 ============
    # 以下代码不再使用
    #
    # page_id = get_page_id()
    # if not page_id:
    #     print('找不到可用的 Chrome page id', file=sys.stderr)
    #     sys.exit(3)
    #
    # run(f'agent-browser connect ws://127.0.0.1:9222/devtools/page/{page_id}')
    # run('agent-browser open "https://chat.deepseek.com/"')
    # time.sleep(6)
    # ...
    # ===============================================

    # 使用 Ollama 进行总结
    print('正在调用 Ollama 进行总结...', file=sys.stderr)
    result = ollama_summarize(prompt, timeout=wait_time + 60)
    output_path.write_text(result, encoding='utf-8')
    print(f'✅ 总结完成，已保存: {output_path}', file=sys.stderr)


if __name__ == '__main__':
    main()
