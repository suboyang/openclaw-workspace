#!/bin/bash
# one-step-backup.sh
# 一键备份 workspace 配置到 GitHub
# 用法: bash one-step-backup.sh

set -e

cd /home/openclaw/.openclaw/workspace

echo "📦 检查 Git 状态..."
git status --short

echo "📝 添加所有已跟踪文件..."
git add -A

echo "⏳ 提交更改..."
git commit -m "backup: $(date '+%Y-%m-%d %H:%M')"

echo "🚀 推送到 GitHub..."
git push origin master

echo "✅ 备份完成！"
