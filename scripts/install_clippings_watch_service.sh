#!/bin/bash
set -e

SCRIPT_DIR="/home/openclaw/.openclaw/workspace/scripts"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

mkdir -p "$SYSTEMD_USER_DIR"
cp "$SCRIPT_DIR/clippings-watch.service" "$SYSTEMD_USER_DIR/"

systemctl --user daemon-reload
systemctl --user enable --now clippings-watch.service

echo "✅ clippings-watch.service 已部署并启动"
echo "---"
systemctl --user status clippings-watch.service --no-pager -l | sed -n '1,20p'
