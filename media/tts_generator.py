import os
import asyncio
import edge_tts
from core.schemas import FullScript

# FIX: Added 'async' keyword here so it can be awaited in run_pipeline.py
async def run_tts(script: FullScript, output_dir="output/audio", max_retries: int = 3):
    print(f"🎙️  Generating Neural Voiceover (EdgeTTS)...")
    os.makedirs(output_dir, exist_ok=True)
    
    # VOICE SELECTION:
    # "en-US-ChristopherNeural" -> Deep, Documentary
    voice = "en-US-ChristopherNeural"

    for seg in script.segments:
        filename = f"segment_{seg.segment_order:02d}.mp3"
        filepath = os.path.join(output_dir, filename)
        
        # Smart Resume
        if os.path.exists(filepath):
            continue

        print(f"   🗣️  Speaking Segment {seg.segment_order}...")
        
        # Retry loop with exponential backoff
        for attempt in range(1, max_retries + 1):
            try:
                # FIX: Using the Python library directly prevents quote/character errors
                communicate = edge_tts.Communicate(seg.narration_text, voice)
                await communicate.save(filepath)
                break  # Success: exit retry loop
                
            except Exception as e:
                if attempt == max_retries:
                    # Final attempt failed
                    print(f"      ❌ Error generating audio for segment {seg.segment_order} (attempt {attempt}/{max_retries}): {e}")
                    raise
                else:
                    # Retry with exponential backoff
                    wait_time = 2 ** (attempt - 1)  # 1s, 2s, 4s
                    print(f"      ⚠️ Attempt {attempt}/{max_retries} failed. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)

    print(f"   ✅ Audio generation complete.")