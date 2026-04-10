---
name: deepseek-summary-browser
description: Use the user's Chrome browser session to open chat.deepseek.com, paste transcript/plain text, and generate a structured Chinese summary for later TTS use. Use when subtitle/transcript text should be summarized online with DeepSeek instead of a local LLM.
modified: 2026-04-10T14:20:41+08:00
---

# DeepSeek Summary Browser

Use the user's Chrome browser via CDP to summarize transcript text with DeepSeek web chat.

## Workflow

1. Ensure Chrome remote debugging on port 9222 is available.
2. Open or connect to `https://chat.deepseek.com/` in the user's Chrome session.
3. Paste transcript/plain text into DeepSeek.
4. Ask for a Chinese summary with these rules:
   - Summary length should be at least one third of the original when practical.
   - Total summary should not exceed 3000 Chinese characters.
   - Output must be split into natural paragraphs.
   - Each paragraph should be roughly 300 to 500 characters when possible.
   - Keep key arguments, timeline, causality, and important details.
   - Do not add facts not present in the source.
5. Wait for the response to finish.
6. Copy/save the returned summary text for later Qwen3-TTS synthesis.

## Rules

- Prefer the user's already logged-in Chrome session.
- After pressing Enter in DeepSeek, wait before reading the response if the page is still streaming.
- Do not summarize from memory when the browser result is required.
- Keep the output in Chinese and suitable for audio narration.
- Use this skill for online summarization only; Qwen3-TTS is a separate downstream step.
- This is the preferred summarization path for subtitle/transcript text when the workflow is: subtitle_to_text.py → DeepSeek browser summary → Qwen3-TTS.
- The returned summary should be ready for later audio production without major cleanup.

## Suggested prompt template

```text
请把下面这份字幕纯文本总结成适合中文语音朗读的摘要稿，并严格遵守：
1. 总结长度尽量不少于原文的三分之一，但总字数不要超过3000字。
2. 输出必须分成多个自然段。
3. 每段尽量控制在300到500字。
4. 不要写成一个大整段。
5. 不要加入原文没有的事实。
6. 保留核心观点、时间线、因果关系与重要细节。
7. 直接输出中文总结正文，不要写额外前言或说明。

以下是原文：
[在此粘贴 transcript 文本]
```

## Notes

- This skill depends on browser automation through Chrome CDP.
- If the text is too long for one prompt, split it into chunks and ask DeepSeek to first summarize chunks, then merge them into one final summary.
