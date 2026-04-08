#!/bin/bash
set -e

cd /home/openclaw/.openclaw/workspace

echo "📂 当前仓库: $(pwd)"
echo "--- git status ---"
git status --short

git add -A

if git diff --cached --quiet; then
  echo "✅ 没有新的改动需要提交"
  exit 0
fi

COMMIT_MSG="backup: $(date '+%Y-%m-%d %H:%M')"
git commit -m "$COMMIT_MSG"
git push

echo "✅ 已同步到 GitHub"
