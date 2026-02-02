import json
import hashlib
from typing import List
from .llm_client import GeminiClient
from core.schemas import EvidenceItem, SourceType

class FactExtractor:
    def __init__(self):
        self.client = GeminiClient(model_name="gemini-2.5-flash-lite")

    def _generate_id(self, text: str) -> str:
        """Creates a deterministic hash for the claim ID."""
        return hashlib.md5(text.encode()).hexdigest()[:12]

    def extract_from_text(self, raw_text: str, url: str, source_type: SourceType) -> List[EvidenceItem]:
        """
        Analyzes raw text and returns a list of validated EvidenceItems.
        """
        
        system_prompt = f"""
        ROLE: You are a strict Fact Extraction Engine.
        INPUT: A raw text snippet from a website ({url}).
        
        TASK:
        1. Extract specific, atomic factual claims.
        2. IGNORE opinions, marketing, emotional language, or vague statements.
        3. IGNORE navigation text, footers, or irrelevant web UI text.
        4. If a claim involves numbers (dates, statistics), extract them exactly.
        5. Assign a confidence score (0.0 to 1.0) based on how objective the claim is.
        
        OUTPUT FORMAT:
        Return a valid JSON list of objects. Each object must have:
        - "claim": string (The fact)
        - "confidence": float
        
        RAW TEXT TO PROCESS:
        {raw_text[:10000]}  # Truncate to avoid token limits if necessary
        """

        try:
            # 1. Call LLM
            response_json = self.client.generate_json(system_prompt)
            data = json.loads(response_json)
            
            # 2. Convert to Pydantic Models (Validation happens here)
            evidence_list = []
            
            # Handle case where LLM returns a dict instead of list
            if isinstance(data, dict):
                # Sometimes Gemini wraps list in a key like "claims"
                data = data.get("claims", [])

            for item in data:
                # We strictly validate against the schema you built earlier
                try:
                    ev = EvidenceItem(
                        id=self._generate_id(item['claim']),
                        claim=item['claim'],
                        source_url=url,
                        source_type=source_type,
                        confidence=item['confidence'],
                        source_count=1  # Default for single extraction
                    )
                    evidence_list.append(ev)
                except Exception as e:
                    print(f"Validation Error for claim '{item.get('claim')}': {e}")
                    continue

            return evidence_list

        except Exception as e:
            print(f"Extraction failed for {url}: {e}")
            return []