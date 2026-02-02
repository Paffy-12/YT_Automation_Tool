import argparse
import json
import sys
import os

# Core Modules
from core.schemas import EvidenceBundle, FullScript

from intelligence.script_writer import ScriptWriter
from research.deep_research import perform_research

from packaging_module.metadata_generator import MetadataGenerator

from media.tts_generator import run_tts
from intelligence.visual_director import VisualDirector
from media.asset_manager import AssetManager
from media.video_editor import run_video_assembly

def run_research_phase(topic: str):
    print(f"🚀 Starting DEEP Research Pipeline for: '{topic}'")
    
    try:
        bundle = perform_research(topic)
        
        print("\n---JSON_OUTPUT_START---")
        print(bundle.model_dump_json(indent=2)) 
        print("---JSON_OUTPUT_END---")
        
        os.makedirs("output", exist_ok=True)
        filename = f"output/evidence_{topic.replace(' ', '_')}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(bundle.model_dump_json(indent=2))
        print(f"\n💾 Saved evidence to {filename}")

    except Exception as e:
        print(f"❌ Critical Research Error: {e}")
        sys.exit(1)

def run_script_phase(evidence_path: str):
    print(f"🎬 Starting Script Generation Phase...")
    print(f"📂 Loading evidence from: {evidence_path}")
    
    # 1. Load and Validate Input
    if not os.path.exists(evidence_path):
        print(f"❌ Error: File not found: {evidence_path}")
        sys.exit(1)
        
    try:
        with open(evidence_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            # Re-hydrate into Pydantic model
            bundle = EvidenceBundle(**raw_data)
            print(f"✅ Loaded evidence bundle for topic: '{bundle.topic}'")
            print(f"   ({len(bundle.items)} verified facts available)")
            
    except Exception as e:
        print(f"❌ Error validating evidence file: {e}")
        sys.exit(1)

    # 2. Initialize Writer
    writer = ScriptWriter()
    
    # 3. Generate Script
    print(f"✍️  Drafting script with Gemini (this may take 10-20s)...")
    try:
        script_obj = writer.generate_script(bundle)
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        sys.exit(1)
        
    # 4. Save Output
    output_filename = f"script_{bundle.topic.replace(' ', '_')}.json"
    with open(output_filename, "w") as f:
        f.write(script_obj.model_dump_json(indent=2))
        
    print(f"\n✅ Script generated successfully!")
    print(f"📜 Title: {script_obj.title}")
    print(f"⏱️  Est Duration: {script_obj.target_duration_minutes} min")
    print(f"💾 Saved to: {output_filename}")

def run_audio_phase(script_path: str):
    print(f"🔊 Starting Audio Generation Phase...")
    
    if not os.path.exists(script_path):
        print(f"❌ Error: Script file not found: {script_path}")
        sys.exit(1)
        
    try:
        with open(script_path, "r") as f:
            data = json.load(f)
            script = FullScript(**data)
    except Exception as e:
        print(f"❌ Error parsing script: {e}")
        sys.exit(1)
        
    run_tts(script)

def run_image_phase(script_path: str):
    print(f"🎬 Starting Visual Directing & Gathering Phase...")

    # 1. Load Script
    if not os.path.exists(script_path):
        print(f"❌ Error: Script not found: {script_path}")
        sys.exit(1)
    with open(script_path, "r") as f:
        script = FullScript(**json.load(f))

    # 2. AI Visual Planning (The Director)
    director = VisualDirector()
    plan_path = script_path.replace("script_", "visual_plan_")
    visual_plan = director.plan_visuals(script, plan_path)
    
    # Save plan (ensure serializable objects)
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in visual_plan], f, indent=2)
    print(f"📝 Visual Plan saved to: {plan_path}")

    # 3. Asset Gathering (The Producer)
    manager = AssetManager()
    manager.fetch_assets(visual_plan)
    print("\n✅ All assets gathered. Ready for editing.")

def run_video_phase(script_path: str):
    print(f"🎞️ Starting Video Assembly Phase...")

    if not os.path.exists(script_path):
        print(f"❌ Error: Script not found: {script_path}")
        sys.exit(1)
    with open(script_path, "r") as f:
        script = FullScript(**json.load(f))

    run_video_assembly(script)

def run_metadata_phase(script_path: str):
    print(f"📝 Starting YouTube Metadata Generation Phase...")
    
    if not os.path.exists(script_path):
        print(f"❌ Error: Script not found: {script_path}")
        sys.exit(1)
        
    with open(script_path, "r", encoding="utf-8") as f:
        script = FullScript(**json.load(f))
        
    generator = MetadataGenerator()
    generator.generate_package(script)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Video Automation Pipeline")
    parser.add_argument("--action", choices=["research", "script", "audio", "images", "video", "package"], required=True)
    parser.add_argument("--topic", type=str, help="Topic to research (Action: research)")
    parser.add_argument("--evidence_path", type=str, help="Path to evidence JSON file (Action: script)")
    parser.add_argument("--script_path", type=str, help="Path to script JSON file (Action: audio, images, video)")

    args = parser.parse_args()
    
    if args.action == "research":
        if not args.topic:
            print("❌ Error: --topic is required for research action")
            sys.exit(1)
        run_research_phase(args.topic)
        
    elif args.action == "script":
        if not args.evidence_path:
            print("❌ Error: --evidence_path is required for script action")
            sys.exit(1)
        run_script_phase(args.evidence_path)
    
    elif args.action == "audio":
        if not args.script_path:
            print("❌ Error: --script_path is required for audio action")
            sys.exit(1)
        run_audio_phase(args.script_path)
        
    elif args.action == "images":
        if not args.script_path:
            print("❌ Error: --script_path is required for images action")
            sys.exit(1)
        run_image_phase(args.script_path)

    elif args.action == "video":
        if not args.script_path:
            print("❌ Error: --script_path is required for video action")
            sys.exit(1)
        run_video_phase(args.script_path)
    if args.action == "package":
        if not args.script_path:
            print("❌ Error: --script_path is required for packaging.")
            sys.exit(1)
        run_metadata_phase(args.script_path)
