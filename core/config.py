import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Model Settings
    # Use Flash Lite for high-volume extraction (15 RPM)
    MODEL_EXTRACTION = "gemini-2.5-flash-lite" 
    # Use Flash for higher reasoning script writing
    MODEL_SCRIPTING = "gemini-2.5-flash"
    
    # Research Constraints
    MAX_SEARCH_RESULTS = 15
    MIN_CONTENT_LENGTH = 500
    MAX_CONTENT_LENGTH = 15000

    # Domain Allow-lists (The "Trust Layer")
    TRUSTED_NEWS_DOMAINS = {
        # Major Wire Services / Global News Agencies
        "reuters.com", "apnews.com", "afp.com", "bbc.com", "bbc.co.uk",
        "aljazeera.com", "dw.com", "kyodoews.jp", "yonhapnews.kr",
        
        # US / North America
        "nytimes.com", "washingtonpost.com", "bloomberg.com", "wsj.com",
        "cnn.com", "cnbc.com", "npr.org", "pbs.org", "abc.com", "nbcnews.com",
        "cbsnews.com", "foxnews.com", "usatoday.com", "marketwatch.com",
        "politico.com", "axios.com", "thehill.com", "vox.com",
        "politicsusa.com", "breitbart.com", "huffpost.com",
        
        # UK / Ireland
        "theguardian.com", "bbc.co.uk", "telegraph.co.uk", "independent.co.uk",
        "timesonline.co.uk", "ft.com", "economist.com", "spectator.co.uk",
        "mirror.co.uk", "dailymail.co.uk", "express.co.uk",
        
        # Europe / International
        "france24.com", "euronews.com", "politico.eu", "rfi.fr",
        "spiegel.de", "3sat.de", "ard.de", "zdf.de", "rtl.de",
        "lemonde.fr", "lefigaro.fr", "liberation.fr", "20minutes.fr",
        "hispantv.com", "elmundo.es", "elpais.es", "abc.es",
        "corriere.it", "repubblica.it", "ansa.it", "lastampa.it",
        "nrc.nl", "telegraaf.nl", "ad.nl", "nu.nl",
        
        # Asia / Pacific
        "abc.net.au", "straitstimes.com", "thehindu.com", "indianexpress.com",
        "ndtv.com", "deccanherald.com", "thenewsminute.com", "theprint.in",
        "theeye.in", "firstpost.com", "scroll.in", "outlookindia.com",
        "chinadaily.com.cn", "xinhuanet.com", "globaltimes.cn",
        "scmp.com", "hongkongfp.com", "rappler.com", "coconuts.co",
        "sbs.com.au", "news.com.au", "theconversation.edu.au",
        "newshub.co.nz", "nzherald.co.nz", "nzdope.com",
        "bangkokpost.com", "nationthai.com", "thestar.com.my",
        "channelnewsasia.com", "today.sg", "8world.sg",
        
        # Middle East / Africa
        "dawn.com", "tribune.com.pk", "thenews.com.pk",
        "arabnews.com", "middleeasteye.net", "jpost.com",
        "elaph.com", "al-jazeera.net", "channelnewsasia.com",
        "dailynewsegypt.com", "ahram.org.eg", "youm7.com",
        "bbc.com/news", "allafrica.com", "pulse.com.gh",
        "iafrica.com", "ewn.co.za", "timeslive.co.za",
        "sowetanlive.co.za", "news24.com", "citizen.co.za"
    }

    TRUSTED_ENCYCLOPEDIAS = {
        # General Knowledge
        "wikipedia.org", "britannica.com", "scholarpedia.org",
        "encarta.msn.com", "encyclopedia.com", "infoplease.com",
        "reference.com", "wiktionary.org", "wikimedia.org",
        
        # Specialized & Academic
        "mw.org", "oed.com", "merriam-webster.com",
        "investopedia.com", "techopedia.com", "webopedia.com"
    }

    TRUSTED_TECH_SCIENCE = {
        # Academic / Peer-Reviewed Journals & Publishers
        "nature.com", "sciencemag.org", "pnas.org", "jama.com",
        "thelancet.com", "bmj.com", "ieee.org", "acm.org",
        "arxiv.org", "researchgate.net", "scholar.google.com",
        "pubmed.ncbi.nlm.nih.gov", "frontiersin.org", "elife.elifesciences.org",
        "plos.org", "mdpi.com", "springer.com", "elsevier.com",
        "wiley.com", "sage.com", "tandfonline.com",
        
        # Government & International Science Organizations
        "nasa.gov", "esa.int", "isro.gov.in", "jaxa.jp",
        "noaa.gov", "usgs.gov", "nist.gov", "energy.gov",
        "defense.gov", "navy.mil", "un.org", "unesco.org",
        "iaea.org", "ipcc.ch", "who.int", "fao.org",
        
        # Hard Science & Research
        "scientificamerican.com", "newscientist.com", "discover.com",
        "smithsonianmag.com", "astronomy.com", "skywatching.com",
        "popularmechanics.com", "popularsciencce.com", "twistedphysics.com",
        
        # Tech News & Analysis (Reputable)
        "arstechnica.com", "techcrunch.com", "wired.com", "theverge.com",
        "engadget.com", "venturebeat.com", "zdnet.com", "cnet.com",
        "neowin.net", "gizmodo.com", "slashgear.com", "gsmarena.com",
        "recode.net", "theemymail.com", "protocol.com",
        
        # Hardware & Components
        "tomshardware.com", "anandtech.com", "pcgamer.com", "techradar.com",
        "digitaltrends.com", "extremetech.com", "guru3d.com", "techspot.com",
        "notebookcheck.net", "gamersnexus.net", "hardwareluxx.de",
        "overclock.net", "tpu.org", "hardwaremax.net", "hwbot.org",
        "cpubenchmark.net", "videocardbenchmark.net", "ssd.userbenchmark.com",
        
        # Memory & Semiconductor Industry (Price/Supply Chain Critical)
        "trendforce.com", "dramexchange.com", "dramtimes.com",
        "idc.com", "gartner.com", "forrester.com", "counterpointresearch.com",
        "strategicsourcetech.com", "semiconportal.com", "semiengineering.com",
        "eesjournal.com", "eejournal.com", "chipsandcheese.com",
        "semiwiki.com", "mooreslaw.org", "semiconductors.org",
        
        # Supply Chain & Logistics
        "supplychainbrain.com", "supplychangainquarterly.com",
        "logisticsmanager.com", "mckinsey.com/industries/semiconductors",
        "bsn.asia", "semiconductor-manufacturing.org",
        
        # Business & Market Analysis
        "bloomberg.com", "reuters.com", "financial-times.com", "economist.com",
        "cnbc.com", "marketwatch.com", "seeking-alpha.com", "motleyfool.com",
        "yahoofinance.com", "nasdaq.com", "sec.gov", "crunchbase.com"
    }