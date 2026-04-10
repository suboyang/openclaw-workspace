#!/usr/bin/env python3
"""Read rsync --itemize-changes output from stdin and log to openclaw_tasks.db"""
import sys, sqlite3
from datetime import datetime

def main():
    if len(sys.argv) < 2:
        print("Usage: log_sync_history.py <direction>")
        sys.exit(1)

    direction = sys.argv[1]
    raw = sys.stdin.read().strip()

    db_path = '/home/openclaw/.openclaw/workspace/openclaw_tasks.db'
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sync_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_time TEXT NOT NULL,
            direction TEXT NOT NULL,
            file_path TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            size_bytes INTEGER,
            notes TEXT
        )
    ''')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    count = 0
    for line in raw.splitlines():
        line = line.strip()
        if not line or len(line) < 12:
            continue
        code = line[:11]
        path = line[12:].strip()
        if not path:
            continue

        first = code[0]
        if first == '>':
            action = 'sent'
        elif first == '<':
            action = 'received'
        elif first == 'c':
            action = 'created'
        elif first == 'd':
            action = 'deleted'
        elif first == 'h':
            action = 'hardlinked'
        elif first == '.':
            continue  # no change
        else:
            action = 'updated'

        conn.execute(
            'INSERT INTO sync_history (sync_time, direction, file_path, action, status) VALUES (?, ?, ?, ?, ?)',
            (now, direction, path, action, 'success')
        )
        count += 1

    conn.commit()
    conn.close()
    print(f"Logged {count} entries to sync_history ({direction})", file=sys.stderr)

if __name__ == '__main__':
    main()
