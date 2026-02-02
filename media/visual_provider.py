import os
import requests
import random
import time
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

class VisualProvider:
    def __init__(self):
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        self.headers = {"Authorization": self.pexels_key}
    
    def fetch_stock_asset(self, query: str, asset_type: str = "video") -> str | None:
        if not self.pexels_key:
            return None

        search_strategies = [
            query,
            query.split()[0] if query.split() else query,
            "abstract",
            "background",
        ]

        base_url = "https://api.pexels.com/videos/search" if asset_type == "video" else "https://api.pexels.com/v1/search"
        
        for search_query in search_strategies:
            time.sleep(0.5)
            try:
                params = {
                    "query": search_query,
                    "per_page": 10, 
                    "orientation": "landscape",
                    "size": "medium" 
                }
                
                response = requests.get(base_url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 429:
                    print(f"      ⚠️ Pexels Rate Limit Hit! Cooling down for 60s...")
                    time.sleep(60)
                    return self.fetch_stock_asset(query, asset_type)
                
                data = response.json()
                items = data.get("videos" if asset_type == "video" else "photos", [])
                
                if items:
                    item = random.choice(items)
                    if asset_type == "video":
                        video_files = item.get("video_files", [])
                        best_file = next((v for v in video_files if v["width"] == 1920), video_files[0] if video_files else None)
                        if best_file:
                            return best_file["link"]
                    else:
                        return item["src"]["large2x"]
            except Exception as e:
                print(f"      ⚠️ Pexels Error with '{search_query}': {e}")
                continue
        return None

    def generate_ai_image(self, prompt: str) -> str:
        """
        Generates the URL for an AI image.
        """
        time.sleep(0.5)
        
        # Clean and enhance the prompt
        safe_prompt = urllib.parse.quote(prompt)
        enhanced_prompt = f"{safe_prompt}%20cinematic%20lighting%20photorealistic%204k%20highly%20detailed"
        
        seed = random.randint(0, 99999)
        
        url = f"https://image.pollinations.ai/prompt/{enhanced_prompt}?width=1920&height=1080&seed={seed}&nologo=true"
        return url