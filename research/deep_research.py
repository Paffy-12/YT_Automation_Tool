import asyncio
import json
import hashlib
from typing import List, Set
from datetime import datetime
from core.schemas import EvidenceBundle, EvidenceItem, SourceType
from research.search_client import SearchClient
from research.source_filter import assess_source_credibility
from intelligence.fact_extractor import FactExtractor
from intelligence.llm_client import GeminiClient

class DeepResearcher:
    def __init__(self):
        # Using Flash for planning/reasoning
        self.llm = GeminiClient(model_name="gemini-2.0-flash")
        self.search_client = SearchClient()
        self.extractor = FactExtractor()

    def _generate_research_plan(self, topic: str) -> List[str]:
        """
        Uses strict JSON mode to safely generate search queries.
        """
        prompt = f"""
        TOPIC: "{topic}"
        
        TASK:
        Generate 4 distinct, specific search queries to fully cover this topic for a documentary.
        1. Context/History
        2. Technical/Deep-Dive
        3. Economic/Political impact
        4. Future outlook
        
        OUTPUT FORMAT:
        Return a JSON object with a key "queries" containing a list of strings.
        Example: {{ "queries": ["query 1", "query 2"] }}
        """
        try:
            # Enforce JSON output via the client wrapper (if supported) or parsing
            response_json = self.llm.generate_json(prompt)
            data = json.loads(response_json)
            queries = data.get("queries", [])
            
            # Guardrail: Ensure list format
            if not isinstance(queries, list) or not queries:
                raise ValueError("LLM returned invalid query format")
                
            return queries[:5] # Limit to 5 max
            
        except Exception as e:
            print(f"⚠️ Plan generation failed: {e}. Falling back to default.")
            return [f"{topic} history", f"{topic} analysis", f"{topic} statistics"]

    async def _process_url(self, url: str, source_type: SourceType) -> List[EvidenceItem]:
        """
        Fetches and extracts facts from a single URL.
        Runs in a thread to avoid blocking the async event loop.
        """
        try:
            # 1. Fetch Text (Blocking I/O wrapped in thread)
            # We assume fetch_page_text handles its own requests.get timeout
            raw_text = await asyncio.to_thread(self.search_client.fetch_page_text, url)
            
            if not raw_text or len(raw_text) < 200:
                return []

            # 2. Extract Facts (Blocking CPU/Network wrapped in thread)
            # FactExtractor uses LLM calls which are sync in your current client
            evidence = await asyncio.to_thread(
                self.extractor.extract_from_text, 
                raw_text, 
                url, 
                source_type
            )
            return evidence

        except Exception as e:
            print(f"      ❌ Failed to process {url}: {e}")
            return []

    async def _investigate_query(self, query: str) -> List[EvidenceItem]:
        """
        Executes search and processing for a single query angle.
        """
        print(f"   🕵️ Investigating: '{query}'...")
        items = []
        
        try:
            # 1. Search (Blocking I/O wrapped in thread)
            results = await asyncio.to_thread(self.search_client.search, query)
            
            # 2. Process Top 3 Results concurrently
            tasks = []
            for res in results[:3]:
                url = res.get('href')
                if not url: continue
                
                # Dynamic Source Typing
                source_type = assess_source_credibility(url) or SourceType.OTHER_TRUSTED
                
                tasks.append(self._process_url(url, source_type))
            
            # Gather results for this query
            results_lists = await asyncio.gather(*tasks)
            
            # Flatten list of lists
            for res_list in results_lists:
                items.extend(res_list)
                
        except Exception as e:
            print(f"   ⚠️ Query failed '{query}': {e}")
            
        return items

    async def run_deep_research(self, topic: str) -> EvidenceBundle:
        print(f"🧠 Deep Research initiated for: {topic}")
        
        # 1. Plan
        queries = self._generate_research_plan(topic)
        print(f"   📋 Research Plan: {queries}")
        
        # 2. Execute All Queries in Parallel
        # This creates a task for every query in the plan
        tasks = [self._investigate_query(q) for q in queries]
        results_lists = await asyncio.gather(*tasks)
        
        # 3. Aggregation & Deduplication
        all_items = []
        seen_claims = set()
        
        for result_list in results_lists:
            for item in result_list:
                # Dedupe based on a normalized hash of the claim text
                # Normalize: lowercase, remove simple punctuation
                clean_claim = item.claim.lower().strip()
                claim_hash = hashlib.md5(clean_claim.encode()).hexdigest()
                
                if claim_hash not in seen_claims:
                    seen_claims.add(claim_hash)
                    all_items.append(item)
        
        print(f"✅ Deep Research Complete. Gathered {len(all_items)} unique facts.")
        
        return EvidenceBundle(
            topic=topic,
            items=all_items,
            processing_timestamp=datetime.now().isoformat(),
            rejected_claims_count=0
        )

# Integration helper
def perform_research(topic: str):
    researcher = DeepResearcher()
    return asyncio.run(researcher.run_deep_research(topic))