import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel

model_path = "/home/openclaw/.cache/models/qwen-tts-0.6B-CustomVoice"

print("Loading Qwen3-TTS model...")
model = Qwen3TTSModel.from_pretrained(
    model_path,
    device_map="cuda:0",
    dtype=torch.bfloat16,
)

# Test text - portion of the Lee Kuan Yew interview
text = """採訪者：你認為現在的世界秩序正在經歷什麼樣的變化？

李光耀：我認為伊拉克和阿富汗的亂局只是分散注意力，真正的重大變化是中國的復甦，以及印度的崛起。在西方殖民之前，光是中國和印度就佔了全球GDP的六成。現在中國正在快速增長，每年都比其他國家發展更快，這種勢頭可以持續二十到三十年。"""

output_path = "/home/openclaw/.openclaw/workspace/qwen3_tts_serena_test.wav"

print(f"Generating speech with Serena (温柔女声)...")
wavs, sr = model.generate_custom_voice(
    text=text,
    language="Chinese",
    speaker="Serena",  # Warm, gentle young female voice
    instruct="用特別溫柔親切的語氣說，節奏舒緩",
)

sf.write(output_path, wavs[0], sr)
print(f"Saved to: {output_path}")
print(f"Duration: {len(wavs[0])/sr:.1f} seconds")
