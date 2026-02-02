from urllib.parse import urlparse
from typing import Optional
from core.schemas import SourceType
from core.config import Config

def extract_domain(url: str) -> str:
    """
    Extracts the base domain from a URL, stripping 'www.'
    Example: 'https://news.bbc.co.uk/story' -> 'bbc.co.uk'
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove port number if present (e.g., :8080)
        if ':' in domain:
            domain = domain.split(':')[0]
            
        # Remove 'www.' prefix
        if domain.startswith("www."):
            domain = domain[4:]
            
        return domain
    except Exception:
        return ""

def assess_source_credibility(url: str) -> Optional[SourceType]:
    """
    Determines if a URL is a trusted source based on TLDs and Config allow-lists.
    Returns the SourceType if trusted, otherwise None.
    """
    # 1. Automatic Trust: Government & Education TLDs
    # We trust these regardless of the specific domain name
    if any(url.endswith(tld) for tld in ['.gov', '.edu', '.mil', '.gov.in', '.ac.uk']):
        if '.edu' in url or '.ac.' in url:
            return SourceType.EDUCATION
        return SourceType.GOVERNMENT
    
    # 2. Extract Domain for list matching
    domain = extract_domain(url)
    if not domain:
        return None
    
    # 3. Check Config Allow-lists
    
    # Check Encyclopedia
    if domain in Config.TRUSTED_ENCYCLOPEDIAS:
        return SourceType.WIKIPEDIA
        
    # Check Major News
    if domain in Config.TRUSTED_NEWS_DOMAINS:
        return SourceType.NEWS_MAJOR
        
    # Check Tech/Science (Mapped to 'trusted' or 'news' depending on your preference)
    # Here we map them to NEWS_MAJOR or create a new OTHER_TRUSTED type if you prefer
    if domain in Config.TRUSTED_TECH_SCIENCE:
        return SourceType.OTHER_TRUSTED

    # 4. Strict Rejection
    # If it's not on the list, it's out. 
    # (This prevents blogs, social media, and content farms from entering)
    return None