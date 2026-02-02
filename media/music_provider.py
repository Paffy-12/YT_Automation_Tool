import os
import requests
import re
import random
import time

class MusicProvider:
    def __init__(self, output_dir="output/audio/music"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        # Switch to Mixkit (Easier to scrape, high quality)
        self.base_url = "https://mixkit.co/free-stock-music/"
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Referer": "https://mixkit.co/"
        }

    def fetch_music(self, mood: str) -> str | None:
        """
        Scrapes Mixkit.co for a track matching the mood.
        Moods: 'suspense', 'cinematic', 'corporate', 'technology', 'happy'
        """
        # Map our internal moods to Mixkit tags
        tag_map = {
            "suspense": "dramatic",
            "futuristic": "technology",
            "corporate": "business",
            "documentary": "cinematic",
            "happy": "happy"
        }
        
        search_tag = tag_map.get(mood, "cinematic")
        filename = f"bg_{search_tag}.mp3"
        filepath = os.path.join(self.output_dir, filename)

        # 1. CACHE CHECK
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100000:
            print(f"      🎵 Found cached music for '{mood}'")
            return filepath

        print(f"      🔍 Searching Mixkit for: '{search_tag}'...")
        
        try:
            url = f"{self.base_url}{search_tag}/"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                print(f"      ⚠️ Search failed ({response.status_code}).")
                return None
            
            mp3_urls = re.findall(r'https?://[a-zA-Z0-9./_-]+mixkit[a-zA-Z0-9./_-]+\.mp3', response.text)
            
            if not mp3_urls:
                print("      ⚠️ No MP3s found. Trying backup generic track...")
                backup_track = "https://assets.mixkit.co/music/preview/mixkit-cinematic-horror-950.mp3"
                mp3_urls = [backup_track]

            # Pick random
            selected_url = random.choice(list(set(mp3_urls)))
            
            # 4. Download
            print(f"      ⬇️ Downloading from Mixkit...")
            time.sleep(1.0) # Politeness
            
            with requests.get(selected_url, stream=True, headers=self.headers) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            # Verify file size (sometimes redirects to 0kb file)
            if os.path.getsize(filepath) < 50000:
                print("      ⚠️ Downloaded file too small. Deleting.")
                os.remove(filepath)
                return None
            
            print(f"      ✅ Saved: {filename}")
            return filepath
            
        except Exception as e:
            print(f"      ❌ Music Fetch Error: {e}")
            return None