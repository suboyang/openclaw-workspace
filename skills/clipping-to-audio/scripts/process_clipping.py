#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "minimax-m2.7:cloud"
CLIPPINGS_DIR = Path("/home/openclaw/.openclaw/workspace/Clippings")
TMP_DIR = Path("/home/openclaw/.openclaw/workspace/tmp")

CLEAN_PROMPT = """You are cleaning a clipped English news article for text-to-speech.

Task:
- Remove metadata, boilerplate, captions, contact prompts, feedback prompts, subscription prompts, tag remnants, markdown clutter, and link artifacts.
- Preserve only the article body.
- Do NOT summarize.
- Do NOT add any information.
- Do NOT rewrite the facts.
- Keep it as a clean, natural English article script suitable for TTS listening.
- Output only the cleaned English article body.

Article:

{text}
"""

TRANSLATE_PROMPT = """Translate the following English news script into natural Chinese for listening.

Rules:
- Be faithful.
- Do NOT summarize.
- Do NOT add information.
- Do NOT embellish.
- Preserve the article's logic and factual meaning.
- Make the Chinese smooth enough for TTS reading.
- Output only the Chinese translation.

English script:

{text}
"""


def latest_clipping() -> Path:
    files = sorted(CLIPPINGS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError(f"No .md files found in {CLIPPINGS_DIR}")
    return files[0]


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) == 3:
            return parts[2]
    return text


def basic_clean(text: str) -> str:
    text = strip_frontmatter(text)
    lines = text.splitlines()
    cleaned = []
    skip_prefixes = (
        "[Contact us:",
        "[Provide news feedback",
        "## Takeaways",
        "source:",
        "author:",
        "published:",
        "created:",
        "description:",
        "tags:",
        "title:",
    )
    for line in lines:
        s = line.strip()
        if not s:
            cleaned.append("")
            continue
        if any(s.startswith(p) for p in skip_prefixes):
            continue
        if re.match(r"^\- \w", s) and "Bloomberg AI" in text:
            # keep article bullets only if still article-like; otherwise ollama will clean final output
            cleaned.append(s)
            continue
        # remove pure markdown link lines
        if s.startswith("[") and "](" in s and s.endswith(")"):
            continue
        # convert markdown links to anchor text
        s = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", s)
        cleaned.append(s)
    # collapse blank lines
    out = []
    prev_blank = True
    for line in cleaned:
        if not line.strip():
            if not prev_blank:
                out.append("")
            prev_blank = True
        else:
            out.append(line)
            prev_blank = False
    return "\n".join(out).strip() + "\n"


def ollama(prompt: str, timeout: int = 600) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json().get("response", "").strip()


def write_outputs(src: Path, raw_text: str, en_tts: str, zh_tts: str):
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    stem = src.stem
    raw_path = TMP_DIR / f"{stem}.raw.txt"
    en_path = TMP_DIR / f"{stem}.tts.en.txt"
    zh_path = TMP_DIR / f"{stem}.tts.zh.txt"
    raw_path.write_text(raw_text + "\n", encoding="utf-8")
    en_path.write_text(en_tts + "\n", encoding="utf-8")
    zh_path.write_text(zh_tts + "\n", encoding="utf-8")
    return raw_path, en_path, zh_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="specific clipping markdown file")
    args = ap.parse_args()

    src = Path(args.file) if args.file else latest_clipping()
    text = src.read_text(encoding="utf-8", errors="ignore")
    raw_text = basic_clean(text)
    en_tts = ollama(CLEAN_PROMPT.format(text=raw_text))
    zh_tts = ollama(TRANSLATE_PROMPT.format(text=en_tts))
    raw_path, en_path, zh_path = write_outputs(src, raw_text, en_tts, zh_tts)
    print(json.dumps({
        "source": str(src),
        "raw": str(raw_path),
        "english_tts": str(en_path),
        "chinese_tts": str(zh_path)
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
