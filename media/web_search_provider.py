from ddgs import DDGS
import random
import time

class WebSearchProvider:
    def __init__(self):
        self.ddgs = DDGS()

    def fetch_web_image(self, query: str) -> str | None:
        """
        Searches DuckDuckGo Images for specific news/events.
        Includes SAFE SEARCH to prevent inappropriate results.
        """
        print(f"      🌐 Searching Web for: '{query}'...")
        try:
            # wait a bit to be polite
            time.sleep(1.0)
            
            # Run Search
            # safesearch='strict' is CRITICAL to avoid the "suggestive" issues you saw.
            results = self.ddgs.images(
                query, 
                region="wt-wt", 
                safesearch="on", 
                max_results=10
            )
            
            # Convert generator to list
            results_list = list(results)
            
            if not results_list:
                return None

            # Filter for good aspect ratios (Landscape preferred)
            # We look for images where width > height
            landscape_images = [
                r for r in results_list 
                if r.get("width", 0) > r.get("height", 0)
            ]
            
            if landscape_images:
                # Pick top 3 to ensure relevance, then random to vary
                selection = random.choice(landscape_images[:3])
                return selection["image"]
            
            # Fallback to any image if no landscape found
            return results_list[0]["image"]

        except Exception as e:
            print(f"      ⚠️ Web Search Error: {e}")
            return None