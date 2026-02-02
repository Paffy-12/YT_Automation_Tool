import argparse
import os
import sys
import json
import time
import asyncio

# --- IMPORTS ---
from research.deep_research import DeepResearcher
from intelligence.script_writer import ScriptWriter
from intelligence.visual_director import VisualDirector
from media.tts_generator import run_tts
from media.asset_manager import AssetManager
from media.video_editor import run_video_assembly
from packaging_module.metadata_generator import MetadataGenerator
from core.schemas import FullScript, EvidenceBundle

# --- HELPER: CHECK IF FILE IS VALID ---
def is_valid_file(filepath):
    """Returns True if file exists and is NOT empty (0 bytes)."""
    if os.path.exists(filepath):
        if os.path.getsize(filepath) > 100: # Needs to be bigger than empty JSON {}
            return True
        else:
            print(f"      ⚠️ Found corrupt/empty file: {filepath}. Deleting...")
            try:
                os.remove(filepath)
            except OSError:
                print(f"      ❌ Could not delete {filepath}. Please delete manually.")
            return False
    return False

async def run_full_pipeline(topic: str, force: bool = False):
    start_time = time.time()
    # Sanitize filename: replace spaces and remove/replace invalid Windows filename chars
    safe_topic = topic.replace(' ', '_').replace(':', '-').replace('?', '').replace('/', '-').replace('\\', '-').replace('|', '-')
    print(f"\n🚀 STARTING PIPELINE: '{topic}'\n" + "="*50)

    # --- 1. RESEARCH PHASE (ASYNC) ---
    evidence_path = f"output/evidence_{safe_topic}.json"
    evidence = None

    if is_valid_file(evidence_path) and not force:
        print(f"\n🔍 PHASE 1: Research (SKIPPING - Found Valid Cache)")
        with open(evidence_path, "r", encoding="utf-8") as f:
            evidence = EvidenceBundle(**json.load(f))
    else:
        print("\n🔍 PHASE 1: Deep Research (GENERATING...)")
        researcher = DeepResearcher()
        
        # CRITICAL FIX: We MUST await this because deep_research.py is async
        evidence = await researcher.run_deep_research(topic) 
        
        # Safety check
        if not evidence or not evidence.items:
             raise ValueError("Research returned no evidence. Check API keys or internet connection.")

        json_data = evidence.model_dump_json(indent=2)
        with open(evidence_path, "w", encoding="utf-8") as f:
            f.write(json_data)
            f.flush()
            os.fsync(f.fileno())
        
        # Verify file was written correctly
        file_size = os.path.getsize(evidence_path)
        if file_size == 0:
            raise ValueError(f"Failed to write evidence file: {evidence_path} (file is empty after write)")
        print(f"      ✅ Evidence saved: {file_size} bytes")

    # --- 2. SCRIPT PHASE (SYNC) ---
    script_path = f"output/script_{safe_topic}.json"
    script = None

    if is_valid_file(script_path) and not force:
        print(f"\n✍️  PHASE 2: Script (SKIPPING - Found Valid Cache)")
        with open(script_path, "r", encoding="utf-8") as f:
            script = FullScript(**json.load(f))
    else:
        print("\n✍️  PHASE 2: Script Generation (GENERATING...)")
        writer = ScriptWriter()
        # ScriptWriter is synchronous, so NO await
        script = writer.generate_script(evidence)
        
        json_data = script.model_dump_json(indent=2)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(json_data)
            f.flush()
            os.fsync(f.fileno())
        
        # Verify file was written correctly
        file_size = os.path.getsize(script_path)
        if file_size == 0:
            raise ValueError(f"Failed to write script file: {script_path} (file is empty after write)")
        print(f"      ✅ Script saved: {file_size} bytes")

    # --- 3. VISUAL PLANNING (SYNC) ---
    plan_path = f"output/visual_plan_{safe_topic}.json"
    
    # If forcing, delete the file so Director starts fresh
    if force and os.path.exists(plan_path):
        os.remove(plan_path)

    print("\n🎬 PHASE 3: Visual Direction")
    director = VisualDirector()
    
    # FIX: Pass the path to the director so it can handle Resume/Saving internally
    visual_plan_objs = director.plan_visuals(script, plan_path)
    
    # Convert back to list of dicts for the Asset Manager
    visual_plan = [s.model_dump() for s in visual_plan_objs]

    # --- 4. AUDIO PRODUCTION (ASYNC) ---
    print("\n🎙️  PHASE 4: Audio Production (EdgeTTS)")
    # run_tts is async, so WE AWAIT
    await run_tts(script)

    # --- 5. ASSET GATHERING (SYNC) ---
    print("\n🎨 PHASE 5: Asset Gathering")
    asset_manager = AssetManager()
    asset_manager.fetch_assets(visual_plan)

    # --- 6. VIDEO ASSEMBLY (SYNC) ---
    print("\n🎞️  PHASE 6: GPU Video Assembly")
    run_video_assembly(script)

    # --- 7. PACKAGING (SYNC) ---
    print("\n📦 PHASE 7: Marketing Package")
    packager = MetadataGenerator()
    packager.generate_package(script)

    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"\n" + "="*50)
    print(f"✅ DONE! Total Time: {duration:.2f} minutes.")
    print(f"📁 Video: output/video/final_video_{safe_topic}.mp4")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the full Text-to-Video Pipeline")
    parser.add_argument("topic", type=str, help="The topic of the video")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_full_pipeline(args.topic, force=args.force))
    except KeyboardInterrupt:
        print("\n🛑 Pipeline stopped by user.")
    except Exception as e:
        print(f"\n❌ CRITICAL PIPELINE FAILURE: {e}")
        import traceback
        traceback.print_exc()