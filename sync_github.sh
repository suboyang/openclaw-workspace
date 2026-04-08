#!/bin/bash
set -e

MODE="${1:-push}"

find_repo() {
    # 1) 当前目录如果本身就在 git 仓库里，直接用当前仓库
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
        return 0
    fi

    # 2) Ubuntu / OpenClaw 路径
    if [ -d "/home/openclaw/.openclaw/workspace/.git" ]; then
        echo "/home/openclaw/.openclaw/workspace"
        return 0
    fi

    # 3) Mac 路径
    if [ -d "/Users/briansoo/sync/飞牛同步/openclaw-workspace/.git" ]; then
        echo "/Users/briansoo/sync/飞牛同步/openclaw-workspace"
        return 0
    fi

    echo ""
    return 1
}

REPO_DIR="$(find_repo)"
if [ -z "$REPO_DIR" ]; then
    echo "❌ 找不到 git 仓库"
    exit 1
fi

cd "$REPO_DIR"

echo "📂 当前仓库: $REPO_DIR"
echo "--- git status ---"
git status --short

case "$MODE" in
    pull)
        git pull
        echo "✅ 已同步最新内容"
        ;;

    push)
        git add -A

        if git diff --cached --quiet; then
            echo "✅ 没有新的改动需要提交"
            exit 0
        fi

        COMMIT_MSG="backup: $(date '+%Y-%m-%d %H:%M')"
        git commit -m "$COMMIT_MSG"
        git push
        echo "✅ 已同步到 GitHub"
        ;;

    *)
        echo "用法: bash sync_github.sh [pull|push]"
        exit 1
        ;;
esac
