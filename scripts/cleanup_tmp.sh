#!/bin/bash
set -e

TARGET_DIR="/home/openclaw/.openclaw/workspace/tmp"

if [ ! -d "$TARGET_DIR" ]; then
    echo "[$(date '+%F %T')] tmp directory not found: $TARGET_DIR"
    exit 0
fi

echo "[$(date '+%F %T')] Cleaning files older than 10 days in $TARGET_DIR"

find "$TARGET_DIR" -type f -mtime +5 -print -delete
find "$TARGET_DIR" -type d -empty -delete

echo "[$(date '+%F %T')] Cleanup complete"
