import json
from .llm_client import GeminiClient
from core.schemas import EvidenceBundle, FullScript

class ScriptWriter:
    def __init__(self):
        # We use the standard Flash model (not Lite) for better reasoning
        self.client = GeminiClient(model_name="gemini-2.5-flash")

    def generate_script(self, evidence_bundle: EvidenceBundle) -> FullScript:
        """
        Generates a video script based strictly on the provided EvidenceBundle.
        """
        # Dump the Pydantic model to JSON to feed it to the LLM
        evidence_json = evidence_bundle.model_dump_json()

        system_prompt = f"""
ROLE: You are an elite YouTube documentarian (think Vox, Johnny Harris, Veritasium).
Your job isn't to summarize facts. It's to TELL A STORY that compels people to keep watching.

TOPIC: "{evidence_bundle.topic}"

CORE STORYTELLING RULES:

1. CONVERSATIONAL FIRST
   - Write like you speak. Use contractions ("It's", "Can't", "Don't").
   - GOOD: "But here's the thing…" or "That's where it gets interesting."

2. RHYTHM & CADENCE
   - Mix short punchy sentences with longer explanations.
   - Vary paragraph lengths intentionally.
   - If it sounds like it's being READ aloud, rewrite it.

3. INTRODUCTION (Segment 1 - MUST ALWAYS INCLUDE)
   - Start with a compelling hook or question that makes viewers want to keep watching.
   - Briefly introduce the topic in an intriguing way WITHOUT diving into details.
   - Set up the stakes or curiosity. Make viewers care.
   - This is NOT a summary. It's a threshold to pull people in.

4. NARRATIVE INTENT
   - Every segment should build toward a point.
   - Setup → tension → release → new mystery.

5. EMOTIONAL FRAMING (Without Emotion Words)
   - Imply stakes and tension.
   - Use contrast and urgency.

6. DATA INTEGRATION (Critical)
   - Never list raw data.
   - Translate numbers into human impact.

7. REDUNDANCY FOR IMPACT
   - Repeat key ideas with variation for emphasis.

8. PERSPECTIVE ANCHORING
   - Use phrases like "Most people don’t realize…"

9. PAYOFF AWARENESS
   - Resolve setups later in the script.
   - Circular endings are encouraged.

10. CONCLUSION (Final Segment - MUST ALWAYS INCLUDE)
    - Circle back to the hook or opening question.
    - Summarize the key insight or "so what" of the story.
    - Leave viewers with a thought, implication, or call-to-action.
    - End on a strong, memorable note.
    - This is NOT a summary list. It's a closing statement.

11. SPOKEN AUTHORITY
    - Confident, declarative tone.
    - Not academic.


STRUCTURE (REQUIRED):
- Segment 1: INTRODUCTION - Hook, set stakes, intrigue
- Segment 2–(N-1): DEEP DIVE - Main story, evidence, narrative
- Segment N: CONCLUSION - Circle back, key insight, memorable ending

CITATION RULES:
- Cite EVERY factual claim using Evidence IDs.
- Use ONLY provided evidence.
- Do NOT invent IDs.
- Bibliography must include actual source_url values.
- ONLY cite evidence IDs that directly support the specific factual claim being made in that sentence.
- Introduction and Conclusion may have fewer citations (they're framing, not data-heavy).

OUTPUT FORMAT (JSON ONLY):
{{
    "topic": "{evidence_bundle.topic}",
    "title": "A viral, specific title",
    "segments": [
        {{
            "segment_order": 1,
            "narration_text": "INTRODUCTION: Conversational hook that draws viewers in...",
            "evidence_refs": [],
            "visual_suggestion": "Suggested visuals"
        }},
        {{
            "segment_order": 2,
            "narration_text": "Main narrative with evidence...",
            "evidence_refs": ["id_1", "id_2"],
            "visual_suggestion": "Suggested visuals"
        }},
        {{
            "segment_order": N,
            "narration_text": "CONCLUSION: Circle back to the hook and leave a memorable final thought...",
            "evidence_refs": [],
            "visual_suggestion": "Suggested visuals"
        }}
    ],
    "sources_bibliography": ["url1", "url2"]
}}

REMEMBER:
- Sound human.
- Tell a story.
- No filler.
- Always include a strong introduction AND conclusion.
"""

        try:
            full_prompt = f"{system_prompt}\n\nEVIDENCE DATA:\n{evidence_json}"
            raw_json = self.client.generate_json(full_prompt)
            data = json.loads(raw_json)

            # Ensure topic consistency
            if "topic" not in data:
                data["topic"] = evidence_bundle.topic

            # Ensure target duration is present (LLM may omit it). Estimate
            # a reasonable length: 0.5 minute per evidence item, with a
            # minimum of 2 minutes.
            if "target_duration_minutes" not in data:
                estimated = max(2.0, len(evidence_bundle.items) * 0.5)
                data["target_duration_minutes"] = float(estimated)

            # Validate structure
            script_obj = FullScript(**data)
            return script_obj

        except json.JSONDecodeError as e:
            print(f"Script generation failed: Invalid JSON response from LLM: {e}")
            raise
        except Exception as e:
            print(f"Script generation failed: {e}")
            raise
