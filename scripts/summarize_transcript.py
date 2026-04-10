#!/usr/bin/env python3
import sys
import math
import json
from pathlib import Path

try:
    import requests
except Exception:
    requests = None

MODEL_NAME = "qwen3.5:9b"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"


def chunk_text(text: str, target=450, min_len=300, max_len=500):
    sentences = []
    buf = ''
    for ch in text:
        buf += ch
        if ch in '。！？!?；;\n':
            s = buf.strip()
            if s:
                sentences.append(s)
            buf = ''
    if buf.strip():
        sentences.append(buf.strip())

    paras = []
    cur = ''
    for s in sentences:
        if len(cur) + len(s) <= max_len:
            cur += s
        else:
            if cur:
                paras.append(cur.strip())
            cur = s
    if cur:
        paras.append(cur.strip())

    # merge too-short paragraphs forward where possible
    merged = []
    i = 0
    while i < len(paras):
        p = paras[i]
        if len(p) < min_len and i + 1 < len(paras) and len(p) + len(paras[i + 1]) <= max_len + 120:
            merged.append((p + paras[i + 1]).strip())
            i += 2
        else:
            merged.append(p)
            i += 1
    return merged


def naive_extract(text: str, target_chars: int):
    # very lightweight fallback summary by selecting representative sentences
    sentences = []
    buf = ''
    for ch in text:
        buf += ch
        if ch in '。！？!?；;\n':
            s = buf.strip()
            if s:
                sentences.append(s)
            buf = ''
    if buf.strip():
        sentences.append(buf.strip())

    if not sentences:
        return text[:target_chars]

    step = max(1, len(sentences) // max(8, math.ceil(target_chars / 80)))
    picked = []
    total = 0
    for idx in range(0, len(sentences), step):
        s = sentences[idx]
        if total + len(s) > target_chars:
            break
        picked.append(s)
        total += len(s)
    if not picked:
        picked = sentences[: min(10, len(sentences))]
    return ''.join(picked)


def llm_summarize(text: str, target_chars: int):
    if requests is None:
        return None
    prompt = f"""请将下面的字幕纯文本总结成适合中文语音朗读的摘要稿，要求严格遵守：
1. 总结长度不少于原文的三分之一，但总字数不要超过3000字。
2. 输出必须分成多个自然段。
3. 每段尽量控制在300到500字。
4. 不要写成一个大整段。
5. 不要加入原文没有的事实。
6. 保留核心观点、时间线、因果关系与重要细节。
7. 输出直接是中文总结正文，不要写“以下是总结”之类前言。

原文如下：
{text[:20000]}
"""
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=600,
        )
        resp.raise_for_status()
        data = resp.json() if resp.text else {}
        result = data.get('response', '').strip()
        return result or None
    except Exception:
        return None


def main():
    if len(sys.argv) < 3:
        print('用法: summarize_transcript.py <input_txt> <output_txt>', file=sys.stderr)
        sys.exit(1)

    inp = Path(sys.argv[1])
    out = Path(sys.argv[2])
    text = inp.read_text(encoding='utf-8', errors='ignore').strip()
    if not text:
        print('❌ 输入文本为空', file=sys.stderr)
        sys.exit(2)

    original_len = len(text)
    min_target = math.ceil(original_len / 3)
    target = min(3000, max(1200, min_target))

    summary = llm_summarize(text, target)
    if not summary:
        summary = naive_extract(text, target)

    if len(summary) > 3000:
        summary = summary[:3000]
    if len(summary) < min_target:
        # 如果模型总结太短，回退到抽取式补足
        fallback = naive_extract(text, target)
        summary = fallback[:3000]

    paragraphs = chunk_text(summary, target=450, min_len=300, max_len=500)
    final_text = '\n\n'.join(paragraphs).strip() + '\n'

    out.write_text(final_text, encoding='utf-8')
    print(f'✅ 总结完成: {out}')
    print(f'原文长度: {original_len} 字')
    print(f'总结长度: {len(final_text)} 字')
    print(f'段落数: {len(paragraphs)}')


if __name__ == '__main__':
    main()
