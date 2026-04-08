---
name: clipping-to-audio
description: Read Markdown article  from /home/openclaw/.openclaw/workspace/Clippings, clean them into a TTS-ready English news script using Ollama MiniMax, translate faithfully into Chinese without summarizing or embellishing, split the Chinese script into manageable segments for Qwen3-TTS, merge the audio, and send the final voice message back to Discord.
---

# clipping-to-audio

Turn saved article clippings into Chinese audio.

## Input

- Default source directory: `/home/openclaw/.openclaw/workspace/Clippings`
- Supports either:
  - the newest clipping in the folder, or
  - a specific `.md` clipping file path

## Workflow

1. Read the clipping markdown file.
2. Strip frontmatter and remove non-article noise, including:
   - title
   - source
   - author
   - published
   - created
   - description
   - tags
   - `[Contact us:]`
   - all links
   - markdown link formatting
3. Send the cleaned English article body to Ollama `minimax-m2.7:cloud`.
4. Ask Ollama to rewrite it into a pure TTS-ready English news script:
   - no summary
   - no added opinions
   - no embellishment
   - preserve factual structure
5. Ask Ollama to translate that English script into faithful Chinese:
   - no summary
   - no added content
   - no interpretation drift
   - suitable for listening
6. Split the Chinese script into safe TTS segments.
7. Before TTS work:
   - switch to `performance`
   - stop `gdm3`
8. Generate each segment with Qwen3-TTS.
9. Merge all segments into one MP3.
10. Restore environment:
    - start `gdm3`
    - switch back to `power-saver` (or original power profile)
11. Send the final MP3 to Discord.

## Rules

- Use Ollama model: `minimax-m2.7:cloud`
- Translation must be faithful, not summarized.
- Preserve article meaning and structure.
- Segment conservatively to reduce GPU crashes.
- Default voice: Serena
- Keep output filenames aligned to the source article title.

## Scripts

- `scripts/process_clipping.py` — clean markdown → Ollama English TTS script → Chinese faithful translation
- `scripts/tts_segments.py` — split Chinese text, run Qwen3-TTS per segment, merge MP3
- `scripts/run_latest.sh` — process newest clipping and send final audio
