import requests
import random
import time

class WikimediaProvider:
    def __init__(self):
        self.api_url = "https://commons.wikimedia.org/w/api.php"
        self.headers = {
            "User-Agent": "EvidencePipelineBot/1.0 (context_video_project)"
        }

    def fetch_editorial_image(self, query: str) -> str | None:
        """
        Searches Wikimedia Commons for public domain/CC editorial images.
        Great for: Politicians, Places, Historical Events.
        """
        # 1. Clean query for better search (e.g., "Donald Trump" instead of "Trump looking angry")
        clean_query = query.split(',')[0].strip()
        print(f"      🏛️  Searching Wikimedia for: '{clean_query}'...")
        
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrnamespace": 6, # Namespace 6 = Files/Images
            "gsrsearch": f"File:{clean_query} filetype:bitmap", # Prefer jpg/png
            "gsrlimit": 5,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
        }

        try:
            r = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
            data = r.json()
            
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return None
            
            # Extract URLs
            image_urls = []
            for page_id, page_data in pages.items():
                image_info = page_data.get("imageinfo", [])
                if image_info:
                    url = image_info[0]["url"]
                    # Filter out tiny icons or SVGs if possible
                    if not url.endswith(".svg") and not "icon" in url.lower():
                        image_urls.append(url)
            
            if image_urls:
                return random.choice(image_urls)
            
        except Exception as e:
            print(f"      ⚠️ Wikimedia Error: {e}")
            return None
        
        return None