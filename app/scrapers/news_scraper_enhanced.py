"""
Enhanced News Scraper with Ontology-Based Relevancy
===================================================
Improvements over original:
1. Rate limiting & anti-bot (user agent rotation, delays, retries)
2. Ontology-based relevancy scoring
3. Duplicate detection (URLs + title normalization)
4. Better error handling with exponential backoff

To use: Replace imports of NewsScraper with this version
"""
import logging
import re
import time
import random
import hashlib
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional, Set, Dict
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.services.inference_engine import analyze
from app.services.ontology import CONCEPTS

logger = logging.getLogger(__name__)


# ── Rate Limiting & Anti-Bot ──────────────────────────────────────────────────
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]
MIN_DELAY = 2.0  # seconds between requests
MAX_DELAY = 5.0
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # exponential backoff multiplier


# ── Ontology-Based Relevancy Scoring ──────────────────────────────────────────
def build_relevancy_keywords() -> List[str]:
    """Extract high-value keywords from ontology for relevancy filtering"""
    keywords = []
    
    # Extract from ontology concepts (buyer-intent domains only)
    for concept_name, concept in CONCEPTS.items():
        if concept.domain in ['automation', 'labor_pain', 'expansion', 'capex', 'strategic']:
            keywords.extend(concept.patterns)
            keywords.extend(concept.synonyms)
    
    # Fallback if ontology is empty
    if not keywords:
        keywords = [
            "automat", "robot", "AGV", "AMR", "warehouse", "logistics", "fulfillment",
            "funding", "series", "raised", "invest", "acqui", "merger",
            "expansion", "opening", "new facilit", "new propert",
            "labor shortage", "staffing", "workforce", "turnover",
            "capex", "capital expenditure", "growth plan", "strategic hire",
            "VP of", "Director of", "Head of", "Chief", "appoint",
            "supply chain", "distribution center", "hospitality", "hotel",
        ]
    
    return keywords


RELEVANCE_KEYWORDS = build_relevancy_keywords()


# ── Duplicate Detection ───────────────────────────────────────────────────────
def normalize_title(title: str) -> str:
    """Normalize article title for duplicate detection"""
    # Remove punctuation, lowercase, collapse whitespace
    normalized = re.sub(r'[^\w\s]', '', title.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def title_fingerprint(title: str) -> str:
    """Generate fingerprint for title-based deduplication"""
    normalized = normalize_title(title)
    return hashlib.md5(normalized.encode()).hexdigest()[:16]


# ── Relevancy Scoring ──────────────────────────────────────────────────────────
def calculate_relevancy_score(text: str) -> float:
    """
    Score relevancy from 0.0-1.0 based on keyword matches
    Uses ontology concepts for sophisticated matching
    """
    text_lower = text.lower()
    matches = 0
    
    # Count keyword matches
    for keyword in RELEVANCE_KEYWORDS:
        if isinstance(keyword, str):
            if keyword.lower() in text_lower:
                matches += 1
        else:
            # It's a regex pattern
            try:
                if re.search(keyword, text_lower):
                    matches += 1
            except:
                pass
    
    # Score: 0.0 (no matches) → 1.0 (5+ matches)
    score = min(1.0, matches / 5.0)
    return score


# ── Known Companies (from original scraper) ───────────────────────────────────
KNOWN_COMPANIES: Dict[str, tuple] = {
    # Logistics
    "xpo logistics": ("XPO Logistics", "Logistics"),
    "dhl": ("DHL Supply Chain", "Logistics"),
    "prologis": ("Prologis", "Logistics"),
    "amazon": ("Amazon Fulfillment", "Logistics"),
    "ryder": ("Ryder System", "Logistics"),
    "fedex": ("FedEx Ground", "Logistics"),
    "ups": ("UPS Supply Chain Solutions", "Logistics"),
    
    # Hospitality
    "marriott": ("Marriott International", "Hospitality"),
    "hilton": ("Hilton Worldwide Holdings", "Hospitality"),
    "hyatt": ("Hyatt Hotels Corporation", "Hospitality"),
    "ihg": ("IHG Hotels & Resorts", "Hospitality"),
    "wyndham": ("Wyndham Hotels & Resorts", "Hospitality"),
    "mgm": ("MGM Resorts International", "Hospitality"),
    
    # Food Service
    "mcdonald's": ("McDonald's Corporation", "Food Service"),
    "starbucks": ("Starbucks Corporation", "Food Service"),
    "chipotle": ("Chipotle Mexican Grill", "Food Service"),
    "yum! brands": ("Yum! Brands", "Food Service"),
    
    # Healthcare
    "hca healthcare": ("HCA Healthcare", "Healthcare"),
    "kaiser": ("Kaiser Permanente", "Healthcare"),
    "mayo clinic": ("Mayo Clinic", "Healthcare"),
    # ... add more as needed
}


class EnhancedNewsScraper:
    """
    Enhanced news scraper with:
    - Rate limiting & anti-bot protection
    - Ontology-based relevancy filtering
    - Duplicate detection
    - Better error handling
    """
    
    GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.session_seen_urls: Set[str] = set()
        self.session_seen_fingerprints: Set[str] = set()
        self.request_count = 0
        self.last_request_time = 0.0
        
        logger.info("EnhancedNewsScraper initialized with ontology-based relevancy")
    
    # ── Rate Limiting ─────────────────────────────────────────────────────────
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        now = time.time()
        elapsed = now - self.last_request_time
        
        if elapsed < MIN_DELAY:
            sleep_time = MIN_DELAY - elapsed + random.uniform(0, MAX_DELAY - MIN_DELAY)
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _get_random_user_agent(self) -> str:
        """Return random user agent for anti-bot"""
        return random.choice(USER_AGENTS)
    
    def _fetch_rss(self, url: str) -> Optional[str]:
        """
        Fetch RSS feed with rate limiting, retries, and anti-bot measures
        """
        for attempt in range(MAX_RETRIES):
            try:
                # Rate limit
                self._rate_limit()
                
                # Build request with random user agent
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': self._get_random_user_agent()}
                )
                
                logger.debug(f"Fetching RSS (attempt {attempt + 1}/{MAX_RETRIES}): {url[:80]}...")
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    content = response.read().decode('utf-8', errors='ignore')
                    return content
                
            except urllib.error.HTTPError as e:
                if e.code == 429:  # Too many requests
                    backoff = RETRY_BACKOFF ** attempt
                    logger.warning(f"HTTP 429 (rate limited), backing off {backoff}s")
                    time.sleep(backoff)
                elif e.code >= 500:  # Server error
                    backoff = RETRY_BACKOFF ** attempt
                    logger.warning(f"HTTP {e.code} (server error), retrying in {backoff}s")
                    time.sleep(backoff)
                else:
                    logger.error(f"HTTP {e.code}: {e.reason}")
                    return None
            
            except urllib.error.URLError as e:
                logger.error(f"URL error: {e.reason}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF ** attempt)
            
            except Exception as e:
                logger.error(f"Unexpected error fetching RSS: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF ** attempt)
        
        return None
    
    # ── Duplicate Detection ───────────────────────────────────────────────────
    
    def _is_duplicate(self, url: str, title: str) -> bool:
        """Check if we've already seen this article (by URL or title fingerprint)"""
        # Check URL
        if url in self.session_seen_urls:
            logger.debug(f"Duplicate URL: {url[:60]}...")
            return True
        
        # Check title fingerprint
        fingerprint = title_fingerprint(title)
        if fingerprint in self.session_seen_fingerprints:
            logger.debug(f"Duplicate title: {title[:60]}...")
            return True
        
        # Check database (expensive, only for valid signals)
        existing_signal = self.db.query(Signal).filter(
            Signal.source_url == url
        ).first()
        
        if existing_signal:
            logger.debug(f"Duplicate in DB: {url[:60]}...")
            # Add to session cache
            self.session_seen_urls.add(url)
            return True
        
        return False
    
    def _mark_seen(self, url: str, title: str):
        """Mark article as seen to prevent duplicates"""
        self.session_seen_urls.add(url)
        self.session_seen_fingerprints.add(title_fingerprint(title))
    
    # ── Relevancy Filtering ───────────────────────────────────────────────────
    
    def _is_relevant(self, title: str, description: str, threshold: float = 0.3) -> bool:
        """
        Filter out irrelevant articles using ontology-based scoring
        
        Returns True if article meets relevancy threshold
        """
        combined_text = f"{title} {description}"
        score = calculate_relevancy_score(combined_text)
        
        is_relevant = score >= threshold
        
        if not is_relevant:
            logger.debug(f"Filtered (score={score:.2f}): {title[:60]}...")
        
        return is_relevant
    
    # ── Main Scraping Logic ───────────────────────────────────────────────────
    
    def run_intent_queries(self, queries: List[str] = None, max_articles: int = 100) -> List[Dict]:
        """
        Run open-market intent queries (no specific company)
        
        Returns list of signals created
        """
        if not queries:
            # Default high-value queries
            queries = [
                "warehouse automation investment 2026",
                "logistics robotics funding 2026",
                "hotel labor shortage automation 2026",
                "fulfillment center expansion 2026",
                "supply chain automation merger 2026",
            ]
        
        logger.info(f"Running {len(queries)} intent queries with ontology relevancy filtering")
        
        all_results = []
        articles_processed = 0
        
        for query in queries:
            if articles_processed >= max_articles:
                logger.info(f"Reached max articles limit ({max_articles})")
                break
            
            # Fetch RSS feed
            url = self.GOOGLE_NEWS_RSS.format(query=urllib.parse.quote(query))
            rss_content = self._fetch_rss(url)
            
            if not rss_content:
                continue
            
            # Parse RSS XML
            try:
                root = ET.fromstring(rss_content)
                items = root.findall('.//item')
                
                logger.info(f"Query '{query}': found {len(items)} articles")
                
                for item in items:
                    if articles_processed >= max_articles:
                        break
                    
                    title = item.findtext('title', '')
                    link = item.findtext('link', '')
                    pub_date = item.findtext('pubDate', '')
                    description = item.findtext('description', '')
                    
                    if not title or not link:
                        continue
                    
                    articles_processed += 1
                    
                    # Duplicate check
                    if self._is_duplicate(link, title):
                        continue
                    
                    # Relevancy check
                    if not self._is_relevant(title, description):
                        continue
                    
                    # Extract company and create signal
                    signal_data = self._create_signal_from_article(
                        title=title,
                        url=link,
                        pub_date=pub_date,
                        description=description,
                        query=query
                    )
                    
                    if signal_data:
                        all_results.append(signal_data)
                        self._mark_seen(link, title)
                
            except ET.ParseError as e:
                logger.error(f"XML parse error for query '{query}': {e}")
            
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
        
        logger.info(f"Completed scraping: {len(all_results)} relevant signals from {articles_processed} articles")
        return all_results
    
    def _create_signal_from_article(self, title: str, url: str, pub_date: str, description: str, query: str) -> Optional[Dict]:
        """
        Extract company name and create signal from article
        
        Uses ontology-based entity extraction
        """
        # Try to extract company from title
        company_name = None
        industry = "Unknown"
        
        # Check against known companies
        title_lower = title.lower()
        for company_key, (canonical_name, company_industry) in KNOWN_COMPANIES.items():
            if company_key in title_lower:
                company_name = canonical_name
                industry = company_industry
                break
        
        # Fallback: extract first capitalized phrase
        if not company_name:
            match = re.search(r'\b([A-Z][A-Za-z0-9&\.\' ]{2,40}?)\b', title)
            if match:
                company_name = match.group(1).strip()
        
        if not company_name:
            logger.debug(f"No company extracted from: {title[:60]}...")
            return None
        
        # Get or create company
        company = self.db.query(Company).filter(
            Company.name == company_name
        ).first()
        
        if not company:
            company = Company(
                name=company_name,
                industry=industry,
                website=None
            )
            self.db.add(company)
            self.db.flush()  # Get company ID
        
        # Determine signal type from content
        combined_text = f"{title} {description}".lower()
        signal_type = self._infer_signal_type(combined_text)
        
        # Create signal
        signal = Signal(
            company_id=company.id,
            signal_type=signal_type,
            summary=title,
            source_url=url,
            source_type="news",
            detected_date=datetime.now(timezone.utc),
            strength=calculate_relevancy_score(combined_text)
        )
        
        self.db.add(signal)
        self.db.commit()
        
        logger.info(f"✓ Signal created: {company_name} | {signal_type} | {title[:50]}...")
        
        return {
            'company': company_name,
            'signal_type': signal_type,
            'title': title,
            'url': url
        }
    
    def _infer_signal_type(self, text: str) -> str:
        """Use ontology to infer signal type from article content"""
        # Check ontology concepts
        for concept_name, concept in CONCEPTS.items():
            # Map concept domain to signal type
            if concept.domain == 'automation':
                for pattern in concept.patterns:
                    if re.search(pattern, text, re.I):
                        return 'automation_intent'
            
            elif concept.domain == 'labor_pain':
                for pattern in concept.patterns:
                    if re.search(pattern, text, re.I):
                        return 'labor_shortage'
            
            elif concept.domain == 'expansion':
                for pattern in concept.patterns:
                    if re.search(pattern, text, re.I):
                        return 'expansion'
        
        # Fallback keyword matching
        if any(kw in text for kw in ['fund', 'series', 'capital', 'invest']):
            return 'funding_round'
        elif any(kw in text for kw in ['acqui', 'merger', 'deal', 'purchase']):
            return 'ma_activity'
        elif any(kw in text for kw in ['appoint', 'joins', 'names', 'vp', 'director', 'coo']):
            return 'strategic_hire'
        elif any(kw in text for kw in ['capex', 'investment', 'facility', 'expansion']):
            return 'capex'
        else:
            return 'news'
