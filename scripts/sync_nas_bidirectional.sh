#!/bin/bash
set -uo pipefail

SRC_A="/mnt/nas_data/WorkSpace/openclaw-workspace/"   # NAS
SRC_B="/home/openclaw/.openclaw/workspace/"            # local
DB="/home/openclaw/.openclaw/workspace/openclaw_tasks.db"
LOG_FILE="/home/openclaw/.openclaw/workspace/tmp/sync_nas_watch.log"
PID_FILE="/home/openclaw/.openclaw/workspace/tmp/sync_nas_watch.pid"
POLL_INTERVAL=10

EXCLUDE=(
    --exclude='venv/'
    --exclude='.venv/'
    --exclude='__pycache__/'
    --exclude='*.pyc'
    --exclude='.cache/'
    --exclude='tmp/'
    --exclude='*.log'
    --exclude='.git/'
    --exclude='.gitignore'
    --exclude='skills/qwen-tts/'
    --exclude='skills/rapid-ocr/'
    --exclude='skills/ocr-local/'
    --exclude='qwen-tts-env/'
    --exclude='sd-env/'
    --exclude='ytdlp-env/'
    --exclude='brew-install/'
    --exclude='node_modules/'
    --exclude='audio-news/'
    --exclude='*.wav'
    --exclude='*.mp3'
    --exclude='*.mp4'
    --exclude='*.pdf'
    --exclude='*.jpg'
    --exclude='*.png'
    --exclude='*.zip'
    --exclude='*.tar.gz'
    --exclude='*.gz'
    --exclude='eng.traineddata'
    --exclude='Test/'
    --exclude='openclaw_tasks.db'
    --exclude='openclaw.duckdb'
)

mkdir -p "$SRC_A" "$SRC_B" "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%F %T')] $*" | tee -a "$LOG_FILE"
}

LOG_SCRIPT="/home/openclaw/.openclaw/workspace/scripts/log_sync_history.py"

sync_workspace_to_nas() {
    log "=== Syncing workspace -> NAS ==="
    output=$(sudo rsync -av --itemize-changes --omit-dir-times \
        "${EXCLUDE[@]}" \
        "$SRC_B" "$SRC_A" 2>&1)
    echo "$output" | grep -E '^[><cdh]' | tee -a "$LOG_FILE" || true
    echo "$output" | grep -E '^[><cdh]' | python3 "$LOG_SCRIPT" "workspace->nas" || true
}

sync_nas_to_workspace() {
    log "=== Syncing NAS -> workspace ==="
    output=$(rsync -av --update --itemize-changes --omit-dir-times \
        "${EXCLUDE[@]}" \
        "$SRC_A" "$SRC_B" 2>&1)
    echo "$output" | grep -E '^[><cdh]' | tee -a "$LOG_FILE" || true
    echo "$output" | grep -E '^[><cdh]' | python3 "$LOG_SCRIPT" "nas->workspace" || true
}

# Initial sync
log "=== Initial workspace -> NAS sync ==="
sync_workspace_to_nas

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    log "Already running with PID $(cat "$PID_FILE"), exiting."
    exit 1
fi

echo $$ > "$PID_FILE"
log "=== Starting continuous workspace sync watch ==="
log "NAS:      $SRC_A"
log "Workspace: $SRC_B"
log "Poll interval: ${POLL_INTERVAL}s"

last_nas_check=0

while true; do
    now=$(date +%s)

    if (( now - last_nas_check >= POLL_INTERVAL )); then
        log "Polling NAS..."
        sync_nas_to_workspace
        last_nas_check=$now
    fi

    inotifywait -t 1 -e create,modify,move,delete --recursive "$SRC_B" 2>/dev/null && {
        log "Local change detected, syncing to NAS..."
        sync_workspace_to_nas
    }

    sleep 1
done
