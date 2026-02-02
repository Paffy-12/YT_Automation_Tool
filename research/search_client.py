import time
from ddgs import DDGS
import requests
from bs4 import BeautifulSoup

class SearchClient:
    def __init__(self, max_results=5):
        self.max_results = max_results
        self.ddgs = DDGS()

    def search(self, query: str):
        """
        Searches DDG and returns a list of results with metadata.
        """
        print(f"🔍 Searching for: {query}...")
        results = []
        # DDGS.text() returns an iterator
        ddg_gen = self.ddgs.text(query, max_results=self.max_results)
        
        for r in ddg_gen:
            results.append({
                "title": r.get("title"),
                "href": r.get("href"),
                "body": r.get("body") # The snippet
            })
        return results

    def fetch_page_text(self, url: str) -> str:
        """
        Visits the URL and extracts the main text content.
        Includes a user-agent to avoid being blocked by simple firewalls.
        Includes rate limiting to prevent 429 errors.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            # Rate limiting: wait 2 seconds between requests
            time.sleep(2)
            
            print(f"🌐 Fetching content from: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts, styles, and navigation to clean up text
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
                
            text = soup.get_text(separator=' ')
            
            # Simple whitespace cleanup
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return clean_text[:15000] # Cap at 15k chars to save tokens
            
        except Exception as e:
            print(f"⚠️ Failed to fetch {url}: {e}")
            return ""