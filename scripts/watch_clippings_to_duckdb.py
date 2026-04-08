#!/usr/bin/env python3
import json
import subprocess
import time
from pathlib import Path

CLIPPINGS_DIR = Path('/home/openclaw/.openclaw/workspace/Clippings')
STATE_FILE = Path('/home/openclaw/.openclaw/workspace/tmp/clippings-watch-state.json')
IMPORT_PY = '/home/openclaw/.openclaw/workspace/scripts/import_clippings_to_duckdb.py'
DUCKDB_PY = '/home/openclaw/.openclaw/duckdb-env/bin/python'
POLL_SECONDS = 10
STABLE_WINDOW_SECONDS = 20
REQUIRED_STABLE_POLLS = max(1, STABLE_WINDOW_SECONDS // POLL_SECONDS)


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def current_snapshot() -> dict:
    snap = {}
    for p in CLIPPINGS_DIR.glob('*.md'):
        try:
            st = p.stat()
            snap[str(p)] = {
                'mtime_ns': st.st_mtime_ns,
                'size': st.st_size,
            }
        except FileNotFoundError:
            continue
    return snap


def import_file(path: str):
    print(f'📥 importing: {path}', flush=True)
    subprocess.run([DUCKDB_PY, IMPORT_PY, path], check=True)


def main():
    print('👀 watching Clippings for changes...', flush=True)
    persisted_state = load_state()
    current_meta = current_snapshot()
    stable_counts = {path: 0 for path in current_meta}

    while True:
        snap = current_snapshot()

        for path, meta in snap.items():
            if path not in current_meta:
                current_meta[path] = meta
                stable_counts[path] = 0
                continue

            if current_meta[path] == meta:
                stable_counts[path] = stable_counts.get(path, 0) + 1
            else:
                current_meta[path] = meta
                stable_counts[path] = 0

            if persisted_state.get(path) != meta and stable_counts.get(path, 0) >= REQUIRED_STABLE_POLLS:
                try:
                    import_file(path)
                    persisted_state[path] = meta
                    save_state(persisted_state)
                except Exception as e:
                    print(f'❌ import failed: {path} :: {e}', flush=True)

        removed = set(current_meta) - set(snap)
        for path in removed:
            current_meta.pop(path, None)
            stable_counts.pop(path, None)

        time.sleep(POLL_SECONDS)


if __name__ == '__main__':
    main()
