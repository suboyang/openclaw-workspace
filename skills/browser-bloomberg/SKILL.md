---
name: browser-bloomberg
description: "使用 Chrome CDP 讀取 Bloomberg 文章並總結。需先啟動 Chrome remote debugging (--remote-debugging-port=9222)。"
metadata: {"openclaw":{"emoji":"🌐","requires":{"bins":["curl","agent-browser"]}}}
---

# Browser Bloomberg Skill

使用 Chrome DevTools Protocol (CDP) 讀取 Bloomberg 付費文章內容。

## 前置需求

### 1. 啟動 Chrome Remote Debugging

在伺服器上啟動 Chrome：
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/home/openclaw/.config/google-chrome
```

或在 OpenClaw 設定中啟用 browser CDP attach mode。

### 2. 連接 Chrome CDP

```bash
agent-browser connect ws://127.0.0.1:9222/devtools/page/<PAGE_ID>
```

## 使用方式

```bash
# 讀取文章並總結
bash ~/.openclaw/workspace/skills/browser-bloomberg/scripts/read_article.sh "BLOOMBERG_URL"
```

## 工作流程

1. 使用 `agent-browser` 打開 Bloomberg URL
2. 等待頁面載入
3. 擷取文章內容（標題、作者、日期、內文）
4. 濃縮總結要點
5. 回覆給用戶

## 腳本列表

- `scripts/read_article.sh` - 主要閱讀腳本
- `scripts/snapshot.sh` - 快速截圖文章內容

## 範例輸出

```
標題：Trump Issues Iran Threats as Mediators Reportedly Seek Ceasefire
作者：Eltaf Najafizada, Sam Kim
日期：April 5, 2026

內容摘要：
1. 川普威脅要摧毀伊朗發電廠
2. 美軍成功救援飛行員
3. 伊朗拒絕讓步，繼續攻擊
...
```
