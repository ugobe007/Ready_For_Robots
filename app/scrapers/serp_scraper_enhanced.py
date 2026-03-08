"""
Enhanced SERP Scraper — pythh.ai Style
=======================================
Expansion & Automation Intent Hunter with pythh.ai improvements.

Improvements over original:
1. Rate Limiting & Anti-Bot: Random delays, user agent rotation, exponential backoff
2. Ontology-Based Relevancy: Use CONCEPTS to filter junk news
3. Duplicate Detection: URL + title fingerprinting
4. Better Entity Extraction: Use ontology to classify signal types

Uses Google News RSS to run targeted SERP-style searches for:
  - Specific city + industry expansion announcements
  - Automation pilot program launches
  - New warehouse/hotel/facility groundbreaking
  - Department head / C-suite appointments
  - CapEx announcements with dollar amounts
"""
import logging
import time
import random
import hashlib
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Optional, Set
import re

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.services.inference_engine import analyze
from app.services.ontology import CONCEPTS
from app.scrapers.news_scraper import KNOWN_COMPANIES, _COMPANY_ANNOUNCE_RE

logger = logging.getLogger(__name__)

# ─── RATE LIMITING & ANTI-BOT ──────────────────────────────────────────────────
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
]

MIN_DELAY = 2.0  # seconds between requests
MAX_DELAY = 5.0
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # exponential backoff multiplier

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

# ─── ONTOLOGY-BASED RELEVANCY ──────────────────────────────────────────────────
def build_serp_relevancy_keywords() -> List[str]:
    """Extract high-signal keywords from ontology for SERP filtering"""
    keywords = []
    for concept_name, concept in CONCEPTS.items():
        # Only buyer-intent domains (expansion, strategic hires, capex)
        if concept.domain in ['expansion', 'strategic', 'capex', 'automation', 'labor_pain']:
            keywords.extend(concept.patterns)
            keywords.extend(concept.synonyms)
    
    # Add explicit SERP-specific signals
    keywords.extend([
        'expansion', 'opening', 'groundbreaking', 'ribbon cutting',
        'capital investment', 'capex', 'funding round',
        'vp of operations', 'chief operating officer', 'director of',
        'labor shortage', 'staffing shortage', 'automation pilot',
        'new warehouse', 'new hotel', 'new facility',
    ])
    return keywords

SERP_KEYWORDS = build_serp_relevancy_keywords()

def calculate_serp_relevancy_score(text: str) -> float:
    """
    Score SERP result relevancy from 0.0-1.0 based on ontology keywords.
    SERP results are noisier than RSS feeds - need stricter filtering.
    """
    lower_text = text.lower()
    matches = 0
    
    for keyword in SERP_KEYWORDS:
        if isinstance(keyword, str):
            if keyword.lower() in lower_text:
                matches += 1
        else:  # regex pattern
            if re.search(keyword, lower_text):
                matches += 1
    
    # SERP needs higher threshold (more false positives than RSS)
    score = min(1.0, matches / 8.0)  # Need 8 matches for perfect score
    return score

# ─── DUPLICATE DETECTION ───────────────────────────────────────────────────────
def normalize_title(title: str) -> str:
    """Normalize article title for duplicate detection"""
    normalized = re.sub(r'[^\w\s]', '', title.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def serp_fingerprint(title: str, url: str) -> str:
    """Generate fingerprint for SERP result deduplication (title + domain)"""
    normalized_title = normalize_title(title)
    # Extract domain from URL
    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    domain = domain_match.group(1) if domain_match else url
    combined = f"{normalized_title}_{domain}"
    return hashlib.md5(combined.encode()).hexdigest()[:16]

# ─── EXPANSION-FOCUSED QUERIES (Original) ──────────────────────────────────────
EXPANSION_QUERIES = [
    # New warehouses / DCs
    "new distribution center groundbreaking 2025 2026",
    "new fulfillment center opens announces construction",
    "\"breaking ground\" warehouse distribution logistics 2026",
    "ribbon cutting new warehouse fulfillment operations 2026",
    "new cold storage facility logistics opens 2026",
    # New hotel openings
    "new hotel opens 2025 2026 grand opening ribbon cutting",
    "hotel renovation capital investment million upgrade 2026",
    "resort expansion new tower rooms construction 2026",
    # New restaurant / food service locations
    "restaurant chain opens new locations 2026 expansion",
    "fast food QSR new unit growth 2026 sites",
    # Hospital / healthcare new builds
    "new hospital campus opens construction 2026",
    "hospital expansion million new building wing",
    "senior living community opens new campus 2026",
    # Automation pilots
    "pilot program automation warehouse 2026 announces",
    "robot deployment pilot warehouse hotel restaurant 2026",
    "AGV AMR autonomous robot deployment 2026 facility",
    # Capital raise / capex announcements
    "\"capital investment\" million warehouse distribution 2026",
    "hotel chain capital investment technology upgrade 2026",
    "logistics company capital raise fund expansion 2026",
    # Exec / buyer-persona appointments
    "\"VP of Operations\" appointed logistics warehouse 2026",
    "\"Chief Operating Officer\" appointed hotel hospitality 2026",
    "\"Director of Facilities\" appointed hospital healthcare 2026",
    "\"VP Supply Chain\" joins named appointed 2026",
    # Labor pain + staffing
    "hotel staffing shortage housekeeping 2026 workers",
    "warehouse labor shortage workers hard to hire 2026",
    "restaurant staffing crisis labor shortage 2026",
    "hospital nursing aide shortage 2026 staffing",
    "\"minimum wage\" increase operations labor cost pressure 2026",
]

# ─── SIGNAL CLASSIFICATION (Enhanced with Ontology) ────────────────────────────
def _classify_signal_ontology(text: str) -> str:
    """Use ontology to classify signal type from article content"""
    lower = text.lower()
    
    # Check CONCEPTS for domain mapping
    for concept_name, concept in CONCEPTS.items():
        if concept.domain == 'expansion':
            for pattern in concept.patterns:
                if isinstance(pattern, str) and pattern.lower() in lower:
                    return 'expansion'
                elif re.search(pattern, lower, re.I):
                    return 'expansion'
        
        elif concept.domain == 'strategic':
            for pattern in concept.patterns:
                if isinstance(pattern, str) and pattern.lower() in lower:
                    return 'strategic_hire'
                elif re.search(pattern, lower, re.I):
                    return 'strategic_hire'
        
        elif concept.domain == 'labor_pain':
            for pattern in concept.patterns:
                if isinstance(pattern, str) and pattern.lower() in lower:
                    return 'labor_shortage'
                elif re.search(pattern, lower, re.I):
                    return 'labor_shortage'
        
        elif concept.domain == 'automation':
            for pattern in concept.patterns:
                if isinstance(pattern, str) and pattern.lower() in lower:
                    return 'automation_intent'
                elif re.search(pattern, lower, re.I):
                    return 'automation_intent'
    
    # Fallback keyword matching
    if any(kw in lower for kw in ['funding', 'series ', 'raised $', 'capital raise']):
        return 'funding_round'
    if any(kw in lower for kw in ['acqui', 'merger', 'buyout']):
        return 'ma_activity'
    if any(kw in lower for kw in ['capex', 'capital expenditure', 'capital investment']):
        return 'capex'
    
    return 'news'

def _infer_industry(text: str) -> str:
    """Infer industry from article text"""
    lower = text.lower()
    if any(w in lower for w in ["hotel", "resort", "hospitality", "lodging"]):
        return "Hospitality"
    if any(w in lower for w in ["restaurant", "food service", "kitchen", "qsr", "fast food"]):
        return "Food Service"
    if any(w in lower for w in ["hospital", "health system", "healthcare", "clinic", "senior living", "nursing"]):
        return "Healthcare"
    if any(w in lower for w in ["warehouse", "logistics", "fulfillment", "distribution", "supply chain", "3pl"]):
        return "Logistics"
    return "Unknown"


class EnhancedSerpScraper:
    """
    Enhanced SERP-style news scraper with pythh.ai improvements.
    
    Improvements:
    1. Rate Limiting: Random 2-5s delays, user agent rotation, exponential backoff
    2. Ontology Relevancy: Use CONCEPTS to filter junk news (stricter for SERP)
    3. Duplicate Detection: URL + title fingerprinting
    4. Better Entity Extraction: Use ontology to classify signal types
    
    Runs curated high-signal queries against Google News RSS for expansion + automation intent.
    """

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.session_seen_urls: Set[str] = set()
        self.session_seen_fingerprints: Set[str] = set()
        self.request_count = 0
        self.last_request_time = 0.0

    def _get_random_user_agent(self) -> str:
        """Return a random user agent for anti-bot protection"""
        return random.choice(USER_AGENTS)

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        now = time.time()
        elapsed = now - self.last_request_time
        
        if elapsed < MIN_DELAY:
            sleep_time = MIN_DELAY - elapsed + random.uniform(0, MAX_DELAY - MIN_DELAY)
            logger.debug(f"[SerpScraper] Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1

    def _is_duplicate(self, url: str, title: str) -> bool:
        """Check if we've already seen this SERP result"""
        # Check URL cache
        if url in self.session_seen_urls:
            return True
        
        # Check title fingerprint cache
        fingerprint = serp_fingerprint(title, url)
        if fingerprint in self.session_seen_fingerprints:
            logger.debug(f"[SerpScraper] Duplicate filtered (title): {title[:60]}...")
            return True
        
        # Check database
        existing_signal = self.db.query(Signal).filter(
            Signal.source_url == url
        ).first()
        if existing_signal:
            self.session_seen_urls.add(url)
            return True
        
        # Mark as seen
        self.session_seen_urls.add(url)
        self.session_seen_fingerprints.add(fingerprint)
        return False

    def _is_relevant(self, text: str, threshold: float = 0.40) -> bool:
        """
        Filter out irrelevant SERP results using ontology-based scoring.
        SERP threshold is higher (0.40 vs 0.30 for RSS) because search results are noisier.
        """
        score = calculate_serp_relevancy_score(text)
        is_relevant = score >= threshold
        
        if not is_relevant:
            logger.debug(f"[SerpScraper] Filtered (score={score:.2f}): {text[:60]}...")
        
        return is_relevant

    def _fetch_rss(self, query: str) -> List[dict]:
        """Fetch RSS with rate limiting, retries, and anti-bot measures"""
        encoded = urllib.parse.quote(query)
        url = GOOGLE_NEWS_RSS.format(query=encoded)
        articles = []
        
        for attempt in range(MAX_RETRIES):
            try:
                self._rate_limit()
                
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': self._get_random_user_agent()}
                )
                
                with urllib.request.urlopen(req, timeout=15) as resp:
                    xml_bytes = resp.read()
                
                root = ET.fromstring(xml_bytes)
                channel = root.find("channel")
                
                if channel is None:
                    return []
                
                for item in channel.findall("item"):
                    title = (item.findtext("title") or "").strip()
                    desc  = (item.findtext("description") or "").strip()
                    link  = (item.findtext("link") or "").strip()
                    
                    articles.append({
                        "title": title,
                        "text": f"{title}. {desc}",
                        "url": link,
                        "query": query,
                    })
                
                return articles
                
            except urllib.error.HTTPError as e:
                if e.code == 429:  # Too many requests
                    backoff = RETRY_BACKOFF ** attempt
                    logger.warning(f"[SerpScraper] Rate limited (429), backing off {backoff}s")
                    time.sleep(backoff)
                else:
                    logger.warning(f"[SerpScraper] HTTP {e.code} error for '{query}'")
                    break
            
            except ET.ParseError as e:
                logger.warning(f"[SerpScraper] XML parse error '{query}': {e}")
                break
            
            except Exception as e:
                logger.warning(f"[SerpScraper] Fetch failed '{query}': {e}")
                if attempt < MAX_RETRIES - 1:
                    backoff = RETRY_BACKOFF ** attempt
                    time.sleep(backoff)
        
        return []

    def _extract_company(self, text: str):
        """Extract company name from article text"""
        lower = text.lower()
        
        # Check KNOWN_COMPANIES first
        for key in sorted(KNOWN_COMPANIES.keys(), key=len, reverse=True):
            if key in lower:
                return KNOWN_COMPANIES[key]
        
        # Use regex to extract company name
        match = _COMPANY_ANNOUNCE_RE.search(text)
        if match:
            extracted = match.group(1).strip()
            if 2 < len(extracted) <= 60 and extracted.lower() not in ("the", "a", "an", "this", "our"):
                return extracted, _infer_industry(text)
        
        return None, None

    def _get_or_create_company(self, name: str, industry: str) -> Optional[Company]:
        """Get existing company or create new one"""
        if not name:
            return None
        
        existing = self.db.query(Company).filter(Company.name == name).first()
        if existing:
            return existing
        
        company = Company(name=name, industry=industry, source="serp_scraper_enhanced")
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company

    def _save_signal(self, article: dict, company_name: str, industry: str) -> bool:
        """Save signal with duplicate checking and relevancy filtering"""
        # Duplicate check
        if self._is_duplicate(article["url"], article["title"]):
            return False
        
        # Relevancy check
        if not self._is_relevant(article["text"]):
            return False
        
        company = self._get_or_create_company(company_name, industry)
        if not company:
            return False
        
        signal_text = article["text"][:600]
        
        # Use inference engine for strength scoring
        result = analyze(f"{company_name} {industry} {article['text']}", industry=industry)
        strength = round(min(result.overall_intent, 1.0), 4)
        
        if strength < 0.05:
            return False
        
        # Use ontology for signal type classification
        signal_type = _classify_signal_ontology(article["text"])
        
        signal = Signal(
            company_id=company.id,
            signal_type=signal_type,
            signal_text=signal_text,
            signal_strength=strength,
            source_url=article.get("url", ""),
        )
        self.db.add(signal)
        self.db.commit()
        
        logger.debug(f"[SerpScraper] Saved [{signal.signal_type}] for {company_name} (strength={strength:.2f})")
        return True

    def run(self, queries: List[str] = None, max_results_per_query: int = 6):
        """
        Run all queries and save signals with enhanced filtering.
        
        Args:
            queries: List of search queries (defaults to EXPANSION_QUERIES)
            max_results_per_query: Max results to process per query
        """
        active_queries = queries or EXPANSION_QUERIES
        total_saved = 0
        
        logger.info(f"[SerpScraper] Starting — {len(active_queries)} queries")
        
        for query in active_queries:
            articles = self._fetch_rss(query)
            logger.debug(f"[SerpScraper] Query '{query[:50]}...' returned {len(articles)} results")
            
            for article in articles[:max_results_per_query]:
                company_name, industry = self._extract_company(article["text"])
                
                if company_name:
                    saved = self._save_signal(article, company_name, industry or "Unknown")
                    if saved:
                        total_saved += 1
        
        logger.info(f"[SerpScraper] Done — {total_saved} new signals saved")
        logger.info(f"[SerpScraper] Session stats: {self.request_count} requests, "
                   f"{len(self.session_seen_urls)} unique URLs, "
                   f"{len(self.session_seen_fingerprints)} unique fingerprints")
