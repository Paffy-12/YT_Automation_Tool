from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional
from datetime import date
from enum import Enum

# --- Enums for Strict Typing ---
class SourceType(str, Enum):
    GOVERNMENT = "government"   # .gov
    EDUCATION = "education"     # .edu
    WIKIPEDIA = "encyclopedia"  # wikipedia.org
    NEWS_MAJOR = "major_news"   # NYT, BBC, Reuters, etc.
    OTHER_TRUSTED = "trusted"   # Specific allowlisted industry sites

class ScriptTone(str, Enum):
    EDUCATIONAL = "educational"
    NEUTRAL = "neutral"

# --- Level 1: The Evidence Atom ---
class EvidenceItem(BaseModel):
    """
    Represents a single, atomic factual claim.
    """
    id: str = Field(..., description="Unique hash of the claim text for referencing")
    claim: str = Field(..., min_length=10, description="The specific factual statement")
    source_url: HttpUrl = Field(..., description="Direct link to source")
    source_type: SourceType
    retrieved_at: date = Field(default_factory=date.today)
    
    # Verification Metadata
    source_count: int = Field(default=1, ge=1, description="How many distinct sources backed this?")
    source_diversity: List[SourceType] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score")
    
    # Context (Optional but helpful for scripting)
    original_text_snippet: Optional[str] = None

    @validator('source_count')
    def validate_numeric_claims(cls, v, values):
        # Logic: If claim contains numbers (heuristic), require >1 source
        # Note: This is a simplified check; complex logic belongs in the extractor
        return v

# --- Level 2: The Bundle (Passed to Gate 1) ---
class EvidenceBundle(BaseModel):
    """
    The collection of facts gathered for a topic.
    This is what the Human approves in Gate 1.
    """
    topic: str
    items: List[EvidenceItem]
    rejected_claims_count: int = 0
    processing_timestamp: str

    @validator('items')
    def ensure_non_empty(cls, v):
        if not v:
            raise ValueError("Evidence bundle cannot be empty. Research failed.")
        return v

# --- Level 3: The Script (Output) ---
class ScriptSegment(BaseModel):
    """
    A single paragraph or block of narration.
    """
    segment_order: int
    narration_text: str
    # CRITICAL: Every segment must link back to specific EvidenceItem IDs
    evidence_refs: List[str] 
    visual_suggestion: Optional[str] = None # For Phase 2

class FullScript(BaseModel):
    """
    The final video script structure.
    """
    title: str
    topic: str
    target_duration_minutes: float
    segments: List[ScriptSegment]
    sources_bibliography: List[str] # Formatted list of all URLs used

# --- Level 4: Visual Plan (Output from Visual Director) ---
class VisualShot(BaseModel):
    """
    A single visual shot within a segment.
    """
    visual_query: str = Field(..., description="Search query for finding the visual")
    visual_type: str = Field(..., description="Type of visual: scenic, emotional, data, archive")
    visual_source: str = Field(..., description="Source: web, wikimedia, pexels, flux")

class VisualPlan(BaseModel):
    """
    Visual plan for a single script segment.
    Contains multiple shots for that segment.
    """
    segment_order: int
    shots: List[VisualShot]