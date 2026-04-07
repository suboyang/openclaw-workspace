#!/bin/bash
# 一键备份 .openclaw 到 GitHub
# 用法: bash backup.sh
cd /home/openclaw/.openclaw
git add -A
git commit -m "backup: $(date '+%Y-%m-%d %H:%M')"
git push
echo "✅ 备份完成！"
