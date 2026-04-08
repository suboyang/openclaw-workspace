#!/bin/bash
set -e

SCRIPT_DIR="/home/openclaw/.openclaw/workspace/scripts"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

mkdir -p "$SYSTEMD_USER_DIR"

cp "$SCRIPT_DIR/cleanup-tmp.service" "$SYSTEMD_USER_DIR/"
cp "$SCRIPT_DIR/cleanup-tmp.timer" "$SYSTEMD_USER_DIR/"

systemctl --user daemon-reload
systemctl --user enable --now cleanup-tmp.timer

echo "✅ cleanup-tmp.timer 已部署并启动"
echo "---"
systemctl --user list-timers | grep cleanup-tmp || true
