#!/bin/bash
set -euo pipefail

SRC_A="/mnt/nas_data/WorkSpace/openclaw-workspace/Clippings"
SRC_B="/home/openclaw/.openclaw/workspace/Clippings"
LOG_FILE="/home/openclaw/.openclaw/workspace/tmp/sync_clippings.log"

mkdir -p "$SRC_A" "$SRC_B" "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%F %T')] $*" | tee -a "$LOG_FILE"
}

log "Starting bidirectional Clippings sync"
RSYNC_FILTERS=(--include='*/' --include='*.md' --exclude='*')

log "NAS -> workspace (.md only)"
rsync -rltvu "${RSYNC_FILTERS[@]}" "$SRC_A/" "$SRC_B/" | tee -a "$LOG_FILE"

log "workspace -> NAS (sudo, .md only)"
sudo rsync -rltvu "${RSYNC_FILTERS[@]}" "$SRC_B/" "$SRC_A/" | tee -a "$LOG_FILE"

log "Clippings sync completed"
