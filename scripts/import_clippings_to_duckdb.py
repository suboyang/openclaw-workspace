#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

import duckdb
import requests

DB_PATH = Path('/home/openclaw/.openclaw/workspace/openclaw.duckdb')
CLIPPINGS_DIR = Path('/home/openclaw/.openclaw/workspace/Clippings')
TMP_DIR = Path('/home/openclaw/.openclaw/workspace/tmp')
AUDIO_DIR = Path('/home/openclaw/.openclaw/workspace/audio-news')
OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'minimax-m2.7:cloud'

SUMMARY_PROMPT = """You are summarizing a clipped English news article for a metadata database.

Task:
- Write a concise English summary in 100 words or fewer.
- Extract only the core point, key keywords, and the main takeaway.
- Do NOT add speculation.
- Do NOT use markdown.
- Output one short paragraph only.

Article:
{text}
"""

TITLE_ZH_PROMPT = """Translate the following English news headline into concise, natural Chinese.

Rules:
- Be faithful to the original meaning.
- Keep it headline-like and natural.
- Do not add commentary.
- Output only the Chinese title.

Headline:
{text}
"""

SUMMARY_ZH_PROMPT = """Translate the following English news summary into concise, natural Chinese for search and retrieval.

Rules:
- Be faithful to the original meaning.
- Keep it concise and natural.
- Do not add commentary.
- Output only the Chinese summary.

Summary:
{text}
"""


def ollama(prompt: str, timeout: int = 600) -> str:
    payload = {
        'model': OLLAMA_MODEL,
        'prompt': prompt,
        'stream': False,
        'options': {'temperature': 0.2},
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json().get('response', '').strip()


def parse_frontmatter(md_text: str) -> dict:
    data = {
        'article_title': None,
        'source_url': None,
        'author': None,
        'published_time': None,
        'created_time': None,
        'description': None,
        'tags': None,
    }
    if not md_text.startswith('---\n'):
        return data
    parts = md_text.split('---\n', 2)
    if len(parts) != 3:
        return data
    fm = parts[1]
    lines = fm.splitlines()
    i = 0
    authors = []
    tags = []
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith('title:'):
            data['article_title'] = stripped.split(':', 1)[1].strip().strip('"')
        elif stripped.startswith('source:'):
            data['source_url'] = stripped.split(':', 1)[1].strip().strip('"')
        elif stripped.startswith('published:'):
            data['published_time'] = stripped.split(':', 1)[1].strip().strip('"')
        elif stripped.startswith('created:'):
            data['created_time'] = stripped.split(':', 1)[1].strip().strip('"')
        elif stripped.startswith('description:'):
            data['description'] = stripped.split(':', 1)[1].strip().strip('"')
        elif stripped.startswith('author:'):
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith('- '):
                authors.append(lines[i].split('- ', 1)[1].strip().strip('"').replace('[[', '').replace(']]', ''))
                i += 1
            i -= 1
        elif stripped.startswith('tags:'):
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith('- '):
                tags.append(lines[i].split('- ', 1)[1].strip().strip('"'))
                i += 1
            i -= 1
        i += 1
    data['author'] = ', '.join(authors) if authors else None
    data['tags'] = ', '.join(tags) if tags else None
    return data


def article_body(md_text: str) -> str:
    if md_text.startswith('---\n'):
        parts = md_text.split('---\n', 2)
        if len(parts) == 3:
            return parts[2].strip()
    return md_text.strip()


def clean_summary_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def resolved_raw_text(src: Path, md_text: str) -> str:
    raw_path = TMP_DIR / f'{src.stem}.raw.txt'
    if raw_path.exists():
        return raw_path.read_text(encoding='utf-8', errors='ignore').strip()
    return article_body(md_text)


def ensure_table(con):
    con.execute('''
    CREATE TABLE IF NOT EXISTS clippings_articles (
        id BIGINT PRIMARY KEY,
        article_title TEXT,
        article_title_zh TEXT,
        source_url TEXT,
        source_file TEXT,
        author TEXT,
        published_time TIMESTAMP,
        created_time TIMESTAMP,
        description TEXT,
        summary TEXT,
        summary_zh TEXT,
        tags TEXT,
        audio_file TEXT,
        audio_duration DOUBLE,
        status TEXT
    )
    ''')


def choose_files(arg_file: str | None, all_files: bool) -> list[Path]:
    if arg_file:
        return [Path(arg_file)]
    files = sorted(CLIPPINGS_DIR.glob('*.md'), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f'No .md files found in {CLIPPINGS_DIR}')
    return files if all_files else [files[0]]


def resolve_audio_file(src: Path) -> str | None:
    audio_path = AUDIO_DIR / f'{src.stem}.final.mp3'
    return str(audio_path) if audio_path.exists() else None


def infer_status(audio_file: str | None) -> str:
    return 'audio_done' if audio_file else 'pending'


def get_audio_duration(audio_file: str | None) -> float | None:
    if not audio_file:
        return None
    try:
        out = subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', audio_file
        ], text=True).strip()
        return round(float(out), 1) if out else None
    except Exception:
        return None


def import_one(con, src: Path):
    md_text = src.read_text(encoding='utf-8', errors='ignore')
    meta = parse_frontmatter(md_text)
    raw_text = resolved_raw_text(src, md_text)
    summary = clean_summary_text(ollama(SUMMARY_PROMPT.format(text=raw_text)))
    summary_zh = ollama(SUMMARY_ZH_PROMPT.format(text=summary))

    created_time = meta['created_time'] or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    published_time = meta['published_time']
    article_title = meta['article_title'] or src.stem
    article_title_zh = ollama(TITLE_ZH_PROMPT.format(text=article_title))
    audio_file = resolve_audio_file(src)
    audio_duration = get_audio_duration(audio_file)
    status = infer_status(audio_file)
    row_id = int(src.stat().st_mtime_ns)

    con.execute('DELETE FROM clippings_articles WHERE article_title = ? AND source_file = ?', [article_title, str(src)])
    con.execute(
        '''
        INSERT INTO clippings_articles (
            id, article_title, article_title_zh, source_url, source_file, author, published_time, created_time,
            description, summary, summary_zh, tags, audio_file, audio_duration, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        [
            row_id,
            article_title,
            article_title_zh,
            meta['source_url'],
            str(src),
            meta['author'],
            published_time,
            created_time,
            meta['description'],
            summary,
            summary_zh,
            meta['tags'],
            audio_file,
            audio_duration,
            status,
        ]
    )
    row = con.execute(
        'SELECT article_title, article_title_zh, source_url, source_file, author, published_time, created_time, description, summary, summary_zh, tags, audio_file, audio_duration, status FROM clippings_articles WHERE id = ?',
        [row_id]
    ).fetchone()
    return {
        'article_title': row[0],
        'article_title_zh': row[1],
        'source_url': row[2],
        'source_file': row[3],
        'author': row[4],
        'published_time': str(row[5]) if row[5] else None,
        'created_time': str(row[6]) if row[6] else None,
        'description': row[7],
        'summary': row[8],
        'summary_zh': row[9],
        'tags': row[10],
        'audio_file': row[11],
        'audio_duration': row[12],
        'status': row[13],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file', nargs='?', help='specific clipping markdown file')
    ap.add_argument('--all', action='store_true', help='import all clipping markdown files')
    args = ap.parse_args()

    files = choose_files(args.file, args.all)
    con = duckdb.connect(str(DB_PATH))
    ensure_table(con)
    con.execute('ALTER TABLE clippings_articles ADD COLUMN IF NOT EXISTS article_title_zh TEXT')
    con.execute('ALTER TABLE clippings_articles ADD COLUMN IF NOT EXISTS source_url TEXT')
    con.execute('ALTER TABLE clippings_articles ADD COLUMN IF NOT EXISTS summary_zh TEXT')
    con.execute('ALTER TABLE clippings_articles ADD COLUMN IF NOT EXISTS audio_file TEXT')
    con.execute('ALTER TABLE clippings_articles ADD COLUMN IF NOT EXISTS audio_duration DOUBLE')
    con.execute('ALTER TABLE clippings_articles ADD COLUMN IF NOT EXISTS status TEXT')
    con.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_clippings_articles_title_source_file ON clippings_articles(article_title, source_file)')

    inserted = []
    for src in files:
        inserted.append(import_one(con, src))
    con.close()

    print(json.dumps({
        'db': str(DB_PATH),
        'imported_count': len(inserted),
        'items': inserted,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
