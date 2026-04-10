---
name: bloomberg-qwen-audio
description: Read Bloomberg articles in Chrome via CDP, translate them into a Chinese narration script, split the script to match the original English article's paragraph structure, synthesize each segment with Qwen3-TTS, merge the audio, and send a Discord-playable MP3 back to the channel. Use when the user wants a Bloomberg article turned into Chinese audio for listening.
modified: 2026-04-09T00:14:26+08:00
---

# Bloomberg Qwen Audio

Use Chrome CDP to read Bloomberg articles, then turn them into a Mandarin  Chinese audio.
Don't Summarize Anything !
## Workflow

1. Open the Bloomberg article in Chrome CDP.
2. Read the full article content.
3. Translate/adapt it into a： natural Chinese narration script.
4. Split the narration so the number of segments matches the English article's paragraph/content structure.
5. Use Qwen3-TTS (Serena) to synthesize each segment.
6. Merge all segment audio files into one MP3.
7. Send the final MP3 to Discord so it can be played inline.

## Rules

- Prefer the user's Chrome session via CDP on port 9222.
- Keep the Chinese script suitable for listening, not word-for-word translation.
- Default workflow is: read full article → Chinese narration script → split into segments that match the English article's paragraph/content structure → Qwen3-TTS each segment → merge → send Discord-playable MP3.
- Output audio filename should match the article title as closely as practical.
- Send the final merged MP3 to Discord with a clear title.
- If GPU is unstable, recover first or retry in smaller chunks while preserving the article-aligned segment structure.
- Treat this article-structure-aligned Qwen3-TTS flow as the standard production path for Bloomberg articles unless the user explicitly asks for a different mode.

## Scripts

- `scripts/read_translate_tts.sh` — end-to-end Bloomberg → Chinese script → article-structure-aligned Qwen3-TTS segmentation → merged MP3

## Notes

- Chrome remote debugging must be available at `127.0.0.1:9222`.
- Qwen3-TTS environment: `~/.openclaw/qwen-tts-env/`
- Default voice: Serena
- Discord target is the current working channel unless the user asks otherwise.
