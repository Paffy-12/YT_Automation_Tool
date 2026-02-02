import json
import os
import time
from intelligence.llm_client import LLM_Client
from core.schemas import FullScript, VisualPlan, VisualShot

class VisualDirector:
    def __init__(self):
        self.llm = LLM_Client()

    def plan_visuals(self, script: FullScript, output_path: str) -> list[VisualPlan]:
        print(f"🎬  Directing Visuals for: {script.title}...")
        
        # 1. LOAD PARTIAL PROGRESS (Smart Resume)
        final_plans = []
        if os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    final_plans = [VisualPlan(**item) for item in data]
                print(f"    👉 Found {len(final_plans)} segments already planned. Resuming...")
            except Exception as e:
                print(f"    ⚠️ Could not load existing plan: {e}. Starting fresh.")
                final_plans = []

        completed_ids = {p.segment_order for p in final_plans}

        # 2. LOOP THROUGH SEGMENTS
        for segment in script.segments:
            if segment.segment_order in completed_ids:
                continue

            print(f"    👉 Planning Segment {segment.segment_order}...")
            time.sleep(2.0) # Rate limit protection

            # Context Memory
            last_visual = "None"
            if final_plans and final_plans[-1].shots:
                last_visual = final_plans[-1].shots[-1].visual_query

            prompt = f"""
            ROLE:
You are a Senior Documentary Visual Director responsible for visual accuracy, emotional pacing, and viewer trust.

CONTEXT:
- The input is factual narration from a documentary.
- Viewers may assume visuals are real unless clearly symbolic.
- Visual misuse harms credibility.

PREVIOUS SHOT:
{last_visual}

INPUT NARRATION:
"{segment.narration_text}"

YOUR TASK (STRICT ORDER):

STEP 1 — SENTENCE ATOMIZATION
- Split the narration into atomic ideas.
- One idea = one shot.
- Never combine unrelated ideas.

STEP 2 — INTENT CLASSIFICATION (INTERNAL)
For each idea, determine ONE dominant intent:
- factual_event
- historical_reference
- personal_actor
- emotional_atmosphere
- abstract_system
- future_projection
- data_or_process

STEP 3 — REALITY REQUIREMENT
Decide:
- Must this visual be REAL and verifiable?
- Can it be SYMBOLIC without misleading?

STEP 4 — SOURCE SELECTION (STRICT)
Choose ONE source per shot:

- web:
  Use ONLY if the idea refers to a real-world event, protest, conflict, document, or incident.
- wikimedia:
  Use ONLY for recognizable people, institutions, or landmarks.
- pexels:
  Use ONLY for non-specific emotion, environment, or pacing shots.
- flux:
  Use ONLY for abstract concepts, data metaphors, or future scenarios.

NEVER:
- Use stock footage for named events.
- Use AI for real people or historical moments.
- Use literal imagery for abstract systems.

STEP 5 — QUERY DESIGN
- Queries must be concise, descriptive, and unambiguous.
- Include location only if contextually required.
- Prefer neutral, journalistic phrasing.

OUTPUT FORMAT (JSON ONLY):
[
  {{
    "visual_query": "...",
    "visual_type": "archive | emotional | scenic | data",
    "visual_source": "web | wikimedia | pexels | flux"
  }}
]

QUALITY RULES:
- Every shot must be defensible in an editorial review.
- If unsure, choose abstraction over misinformation.

            """
            
            try:
                response_text = self.llm.generate_json(prompt)
                clean_json = response_text.replace("```json", "").replace("```", "")
                shot_data = json.loads(clean_json)
                
                valid_shots = []
                for s in shot_data:
                    valid_shots.append(VisualShot(
                        visual_query=s.get("visual_query", "abstract background"),
                        visual_type=s.get("visual_type", "scenic"),
                        visual_source=s.get("visual_source", "pexels")
                    ))
                
                new_plan = VisualPlan(segment_order=segment.segment_order, shots=valid_shots)
                final_plans.append(new_plan)

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump([p.model_dump() for p in final_plans], f, indent=2)
                
            except Exception as e:
                print(f"    ❌ Error directing segment {segment.segment_order}: {e}")
                print("    ⚠️ Saving progress. Run pipeline again to resume.")
                raise e

        return final_plans