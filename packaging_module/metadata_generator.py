import sys
import os

# Fix path to allow importing from 'core'/ 'intelligence'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from intelligence.llm_client import LLM_Client
from core.schemas import FullScript

class MetadataGenerator:
    def __init__(self, output_dir="output/upload_ready"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.llm = LLM_Client()

    def generate_package(self, script: FullScript):
        print(f"📦 Generating YouTube Metadata for: {script.title}")
        
        # 1. Calculate Timestamps (Estimate: 15 chars = 1 second)
        timestamps = []
        current_time = 0
        for segment in script.segments:
            # Format seconds to MM:SS
            minutes = int(current_time // 60)
            seconds = int(current_time % 60)
            timestamp_str = f"{minutes:02d}:{seconds:02d}"
            
            # Use the first sentence as the chapter title
            chapter_title = segment.narration_text.split('.')[0][:40] + "..."
            timestamps.append(f"{timestamp_str} - {chapter_title}")
            
            # Add duration estimate (approx reading speed)
            current_time += len(segment.narration_text) / 15 

        timestamps_text = "\n".join(timestamps)

        # 2. Ask Gemini for the "Click Package" (Descriptions + Titles)
        # Note: We do NOT ask for sources here. We append them manually below to ensure accuracy.
        prompt = f"""
        You are a YouTube Expert. Create the metadata for this video script.
        
        SCRIPT TITLE: {script.title}
        TOPIC: {script.topic}
        
        TIMESTAMPS:
        {timestamps_text}
        
        OUTPUT REQUIREMENTS:
        1. Give me 3 options for a "Clickbait but Honest" Title.
        2. Write a YouTube Description that includes:
           - A compelling hook in the first 2 lines (crucial for CTR).
           - A brief summary of the argument.
           - The Timestamps provided above (COPY THEM EXACTLY).
        3. A comma-separated list of 30 high-volume SEO tags.
        
        Return ONLY valid JSON with keys: "titles" (list), "description" (string), "tags" (string).
        """
        
        response = self.llm.generate(prompt)
        
        # 3. Process Response & Manually Append Sources
        clean_json = response.replace("```json", "").replace("```", "")
        
        try:
            meta_data = json.loads(clean_json)
            
            # --- THE FIX: MANUALLY APPEND SOURCES ---
            # This ensures 100% accuracy and no LLM hallucination of links
            sources_text = "\n\n📚 SOURCES & CITATIONS:\n"
            
            if script.sources_bibliography:
                for idx, url in enumerate(script.sources_bibliography, 1):
                    sources_text += f"[{idx}] {url}\n"
            else:
                sources_text += "Research generated using Deep Research Pipeline.\n"
            
            # Append to the description
            meta_data["description"] += sources_text
            
            # 4. Save to File
            safe_title = script.title.replace(" ", "_").replace(":", "").replace("'", "")[:50]
            output_file = os.path.join(self.output_dir, f"metadata_{safe_title}.json")
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(meta_data, f, indent=2)
                
            print(f"✅ Metadata saved to: {output_file}")
            return output_file
            
        except json.JSONDecodeError:
            print("❌ Error parsing Metadata JSON.")
            return None