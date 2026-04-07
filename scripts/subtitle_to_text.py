#!/usr/bin/env python3
import sys
import re
import json
import html
import xml.etree.ElementTree as ET
from pathlib import Path


def clean_line(s: str) -> str:
    s = html.unescape(s)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'\{[^}]*\}', ' ', s)
    s = re.sub(r'\[[^\]]*\]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def dedupe_keep_order(lines):
    out = []
    prev = None
    for line in lines:
        if not line:
            continue
        if line == prev:
            continue
        out.append(line)
        prev = line
    return out


def parse_vtt_like(text: str):
    lines = []
    for raw in text.splitlines():
        line = raw.strip('\ufeff').strip()
        if not line:
            continue
        if line.startswith('WEBVTT'):
            continue
        if re.match(r'^\d+$', line):
            continue
        if '-->' in line:
            continue
        if line.startswith('NOTE'):
            continue
        line = clean_line(line)
        if line:
            lines.append(line)
    return dedupe_keep_order(lines)


def parse_ttml(text: str):
    try:
        root = ET.fromstring(text)
    except Exception:
        return parse_vtt_like(text)
    lines = []
    for elem in root.iter():
        tag = elem.tag.lower()
        if tag.endswith('p') or tag.endswith('span'):
            content = ''.join(elem.itertext()).strip()
            content = clean_line(content)
            if content:
                lines.append(content)
    return dedupe_keep_order(lines)


def parse_json3(text: str):
    lines = []
    try:
        data = json.loads(text)
    except Exception:
        return parse_vtt_like(text)

    events = data.get('events', []) if isinstance(data, dict) else []
    for ev in events:
        segs = ev.get('segs') if isinstance(ev, dict) else None
        if not segs:
            continue
        content = ''.join(seg.get('utf8', '') for seg in segs if isinstance(seg, dict))
        content = clean_line(content)
        if content:
            lines.append(content)
    return dedupe_keep_order(lines)


def parse_file(path: Path):
    text = path.read_text(encoding='utf-8', errors='ignore')
    suffix = path.suffix.lower()
    if suffix in {'.vtt', '.srv1', '.srv2', '.srv3'}:
        return parse_vtt_like(text)
    if suffix == '.ttml':
        return parse_ttml(text)
    if suffix == '.json3' or suffix == '.json':
        return parse_json3(text)
    return parse_vtt_like(text)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('用法: subtitle_to_text.py <input_subtitle_file> <output_txt>', file=sys.stderr)
        sys.exit(1)

    in_file = Path(sys.argv[1])
    out_file = Path(sys.argv[2])
    lines = parse_file(in_file)
    out_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'✅ 轉換完成: {out_file}')
    print(f'📝 行數: {len(lines)}')
