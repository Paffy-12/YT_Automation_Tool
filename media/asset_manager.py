import os
import json
import requests
import shutil
import time
from PIL import Image, UnidentifiedImageError
from media.visual_provider import VisualProvider
from media.wikimedia_provider import WikimediaProvider
from media.web_search_provider import WebSearchProvider # <--- NEW IMPORT

class AssetManager:
    def __init__(self, output_dir="output/assets"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Load all providers
        self.stock_provider = VisualProvider() # Pexels/Flux
        self.wiki_provider = WikimediaProvider()
        self.web_provider = WebSearchProvider() # DuckDuckGo
        
        self.cache_file = os.path.join(output_dir, "asset_cache.json")
        self.cache = self._load_cache()

    def _analyze_query_intent(self, query: str, v_type: str, v_source: str) -> list[str]:
        """
        Decides the BEST ORDER of sources based on the query content.
        Returns a list of strategies: ['wiki', 'web', 'pexels', 'flux']
        """
        query_lower = query.lower()
        
        # 1. DETECT SPECIFIC NEWS / HISTORY
        # Indicators: Years (2014, 1999), Specific Places (Kyiv, Kremlin), "War", "Treaty", "Protest"
        is_news_event = any(char.isdigit() for char in query) or \
                        any(x in query_lower for x in ["war", "treaty", "protest", "law", "president", "minister", "deal", "pipeline"]) or \
                        v_source == "wikimedia"

        if is_news_event:
            # STRATEGY: Facts First. Pexels is LAST resort (it has no news).
            return ["wiki", "web", "flux"]

        # 2. DETECT ABSTRACT / DATA
        if v_type == "data" or v_source == "flux" or "chart" in query_lower or "graph" in query_lower:
            # STRATEGY: AI First. Web second (real charts). Pexels last.
            return ["flux", "web", "pexels"]

        # 3. DETECT GENERIC / SCENIC
        # Default for "Sad face", "City skyline", "Money"
        # STRATEGY: High Quality Stock First.
        return ["pexels", "web", "flux"]

    def _download_file(self, url: str, filepath: str) -> bool:
        for attempt in range(2):
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                with requests.get(url, stream=True, headers=headers, timeout=60) as r:
                    r.raise_for_status()
                    with open(filepath, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                
                # Validate file size (must have content)
                if os.path.getsize(filepath) < 1024:
                    print(f"      ⚠️ File too small ({os.path.getsize(filepath)} bytes). Likely incomplete download.")
                    os.remove(filepath)
                    return False
                
                # Image Validation
                if filepath.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    try:
                        with Image.open(filepath) as img:
                            img.verify()
                    except:
                        print(f"      ⚠️ Invalid image. Deleting.")
                        os.remove(filepath)
                        return False
                
                # Video Validation (check for common MP4 signature and minimum size)
                if filepath.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
                    file_size = os.path.getsize(filepath)
                    if file_size < 100000:  # Videos should be at least 100KB
                        print(f"      ⚠️ Video too small ({file_size} bytes). Likely incomplete download.")
                        os.remove(filepath)
                        return False
                    # Check for MP4 file signature (starts with specific bytes or contains 'ftyp')
                    try:
                        with open(filepath, 'rb') as f:
                            header = f.read(512)
                            if b'ftyp' not in header and b'mdat' not in header:
                                print(f"      ⚠️ Invalid video format (missing MP4 signature).")
                                os.remove(filepath)
                                return False
                    except:
                        pass
                
                return True
            except Exception as e:
                print(f"      ⚠️ Download attempt {attempt + 1} failed: {str(e)[:50]}")
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass
        return False

    def fetch_assets(self, visual_plan: list):
        print(f"📦 Asset Manager: Context-Aware Gathering...")
        
        for segment in visual_plan:
            # Handle obj vs dict
            if isinstance(segment, dict):
                seg_order, shots = segment.get("segment_order"), segment.get("shots", [])
            else:
                seg_order, shots = segment.segment_order, segment.shots

            seg_dir = os.path.join(self.output_dir, f"segment_{seg_order:02d}")
            os.makedirs(seg_dir, exist_ok=True)
            
            for i, shot in enumerate(shots):
                # Unpack Shot
                if isinstance(shot, dict):
                    query, v_type, v_source = shot.get("visual_query"), shot.get("visual_type", "scenic"), shot.get("visual_source", "pexels")
                else:
                    query, v_type, v_source = shot.visual_query, shot.visual_type, getattr(shot, "visual_source", "pexels")

                # Determine file extension (Video only for Pexels usually)
                is_video = (v_source == "pexels") and (v_type != "data")
                ext = "mp4" if is_video else "jpg"
                filename = f"shot_{i:02d}.{ext}"
                filepath = os.path.join(seg_dir, filename)
                
                # Skip if valid exists
                if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:
                    continue

                # --- SMART STRATEGY SELECTION ---
                # Default strategies based on query analysis
                strategies = self._analyze_query_intent(query, v_type, v_source)
                
                # OVERRIDE: If the Visual Director EXPLICITLY asked for 'web' or 'wikimedia', 
                # put that at the top of the list.
                if v_source == "web" and "web" in strategies:
                    strategies.remove("web")
                    strategies.insert(0, "web")
                elif v_source == "wikimedia" and "wiki" in strategies:
                    strategies.remove("wiki")
                    strategies.insert(0, "wiki")
                elif v_source == "flux" and "flux" in strategies:
                    strategies.remove("flux")
                    strategies.insert(0, "flux")

                print(f"   🔍 Shot {i}: '{query}' -> Strategy: {strategies}")

                download_success = False

                for strat in strategies:
                    if download_success: break

                    # STRATEGY: WIKIMEDIA
                    if strat == "wiki":
                        url = self.wiki_provider.fetch_editorial_image(query)
                        if url:
                            final_path = filepath.replace(".mp4", ".jpg")
                            if self._download_file(url, final_path):
                                print(f"      ✅ Saved Editorial (Wiki): {filename}")
                                download_success = True

                    # STRATEGY: WEB SEARCH (DuckDuckGo)
                    elif strat == "web":
                        url = self.web_provider.fetch_web_image(query)
                        if url:
                            final_path = filepath.replace(".mp4", ".jpg")
                            if self._download_file(url, final_path):
                                print(f"      ✅ Saved Web Image (DDG): {filename}")
                                download_success = True

                    # STRATEGY: FLUX (AI)
                    elif strat == "flux":
                        url = self.stock_provider.generate_ai_image(query)
                        final_path = filepath.replace(".mp4", ".jpg")
                        if self._download_file(url, final_path):
                            print(f"      ✅ Saved AI Image (Flux): {filename}")
                            download_success = True

                    # STRATEGY: PEXELS (Stock)
                    elif strat == "pexels":
                        # Try Video first if requested
                        if is_video:
                            url = self.stock_provider.fetch_stock_asset(query, "video")
                            if url and self._download_file(url, filepath):
                                print(f"      ✅ Saved Stock Video: {filename}")
                                download_success = True
                        
                        # Fallback to Photo if video failed
                        if not download_success:
                            url = self.stock_provider.fetch_stock_asset(query, "photo")
                            if url:
                                final_path = filepath.replace(".mp4", ".jpg")
                                if self._download_file(url, final_path):
                                    print(f"      ✅ Saved Stock Photo: {filename}")
                                    download_success = True

                # FINAL FALLBACK (If everything failed)
                if not download_success:
                    print(f"      ⚠️ All strategies failed. Using Abstract Fallback.")
                    url = self.stock_provider.fetch_stock_asset("abstract dark background", "photo")
                    final_path = filepath.replace(".mp4", ".jpg")
                    self._download_file(url, final_path)

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f: return json.load(f)
        return {}