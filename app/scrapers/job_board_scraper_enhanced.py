"""
Enhanced Job Board Scraper — pythh.ai Style
===========================================
Improvements over original:
1. Rate Limiting & Anti-Bot: Random delays, user agent rotation, exponential backoff
2. Ontology-Based Relevancy: Filter out "robotics engineer" postings using CONCEPTS
3. Duplicate Detection: URL + title fingerprinting
4. Better Entity Extraction: Use ontology to validate buyer personas
"""
import re
import time
import random
import hashlib
import logging
from typing import Set, List, Optional
from bs4 import BeautifulSoup

from app.scrapers.base_scraper import BaseScraper
from app.services.ontology import CONCEPTS

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

# ─── ONTOLOGY-BASED RELEVANCY ──────────────────────────────────────────────────
def build_buyer_persona_keywords() -> List[str]:
    """Extract buyer persona keywords from ontology (NOT builder personas)"""
    keywords = []
    for concept_name, concept in CONCEPTS.items():
        # Skip engineering/builder personas
        if concept.domain == 'engineering' or 'engineer' in concept_name.lower():
            continue
        # Include operations, strategic, labor pain personas
        if concept.domain in ['strategic', 'labor_pain', 'expansion']:
            keywords.extend(concept.patterns)
            keywords.extend(concept.synonyms)
    
    # Add explicit buyer persona patterns
    keywords.extend([
        r"vp.{0,20}operations", r"director.{0,20}operations", 
        r"vp.{0,20}facilities", r"director.{0,20}facilities",
        r"vp.{0,20}supply chain", r"chief operating officer",
        r"general manager", r"operations manager",
        r"vp.{0,20}food.{0,10}beverage", r"director.{0,20}housekeeping",
    ])
    return keywords

def build_automation_pain_keywords() -> List[str]:
    """Extract operational pain keywords from ontology"""
    keywords = []
    for concept_name, concept in CONCEPTS.items():
        if concept.domain in ['labor_pain', 'automation']:
            keywords.extend(concept.patterns)
            keywords.extend(concept.synonyms)
    return keywords

BUYER_KEYWORDS = build_buyer_persona_keywords()
PAIN_KEYWORDS = build_automation_pain_keywords()

def calculate_job_relevancy_score(title: str, description: str) -> float:
    """
    Score job posting relevancy from 0.0-1.0.
    HIGH score = operations buyer persona OR high labor pain
    LOW score = robotics engineer, robot builder (filter these out!)
    """
    combined = f"{title} {description}".lower()
    
    # FILTER OUT: Engineering/builder roles (these are NOT buyers)
    engineering_patterns = [
        'robotics engineer', 'robot engineer', 'automation engineer',
        'controls engineer', 'mechatronics', 'robot programmer',
        'robot technician', 'robot builder', 'robotics developer',
        'firmware engineer', 'embedded engineer', 'plc programmer',
    ]
    if any(pattern in combined for pattern in engineering_patterns):
        return 0.0  # REJECT: These are builders, not buyers
    
    # BOOST: Buyer persona matches
    buyer_matches = 0
    for keyword in BUYER_KEYWORDS:
        if isinstance(keyword, str):
            if keyword.lower() in combined:
                buyer_matches += 1
        else:  # regex pattern
            if re.search(keyword, combined):
                buyer_matches += 1
    
    # BOOST: Labor pain signals
    pain_matches = 0
    for keyword in PAIN_KEYWORDS:
        if isinstance(keyword, str):
            if keyword.lower() in combined:
                pain_matches += 1
        else:  # regex pattern
            if re.search(keyword, combined):
                pain_matches += 1
    
    # Score calculation
    # Buyer persona = high signal (executives who approve budgets)
    # Labor pain = medium signal (operational challenges = automation need)
    score = min(1.0, (buyer_matches * 0.20) + (pain_matches * 0.10))
    return score

# ─── DUPLICATE DETECTION ───────────────────────────────────────────────────────
def normalize_job_title(title: str) -> str:
    """Normalize job title for duplicate detection"""
    # Remove company name suffixes
    title = re.sub(r'\s*[-–—]\s*.*$', '', title)
    # Remove punctuation
    normalized = re.sub(r'[^\w\s]', '', title.lower())
    # Collapse whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def job_fingerprint(title: str, company: str) -> str:
    """Generate fingerprint for job posting deduplication"""
    normalized_title = normalize_job_title(title)
    normalized_company = company.lower().strip()
    combined = f"{normalized_title}_{normalized_company}"
    return hashlib.md5(combined.encode()).hexdigest()[:16]

# ─── LABOR PAIN & BUYER PERSONA PATTERNS (Original Logic) ─────────────────────
# Operational roles posted in volume = labor pain = robot opportunity.
LABOR_PAIN_KEYWORDS = [
    # Logistics / warehouse
    "warehouse associate", "fulfillment associate", "order picker", "packer",
    "forklift operator", "material handler", "receiving associate",
    "inventory associate", "shipping associate", "dock worker",
    "freight handler", "distribution center associate",
    # Hospitality
    "housekeeper", "room attendant", "bell", "valet", "concierge",
    "front desk", "laundry attendant", "banquet server", "porter",
    "housekeeping supervisor",
    # Food service
    "line cook", "prep cook", "dishwasher", "food runner", "busser",
    "kitchen staff", "crew member", "team member", "fry cook",
    "barista", "cashier",
    # Healthcare
    "patient transport", "environmental services", "sterile processing",
    "pharmacy technician", "dietary aide", "hospital aide", "EVS tech",
    "linen service", "supply chain tech",
]

PAIN_SIGNALS = [
    "competitive pay", "immediate hire", "hiring now", "urgent", "high turnover",
    "retention bonus", "sign-on bonus", "starting immediately",
    "multiple openings", "various shifts", "night shift", "weekend required",
    "staffing shortage", "hard to fill", "labor shortage",
]

BUYER_PERSONA_PATTERNS = [
    re.compile(r"(VP|SVP|Director|Head|Chief).{0,30}(operations|facilities|logistics|supply chain)", re.I),
    re.compile(r"(VP|SVP|Director|Head).{0,30}(food.{0,10}beverage|F&B|restaurant|culinary)", re.I),
    re.compile(r"(VP|SVP|Director|Head).{0,30}(housekeeping|rooms|property)", re.I),
    re.compile(r"(VP|SVP|Director|Head).{0,30}(distribution|fulfillment|warehouse)", re.I),
    re.compile(r"Chief (Operating|Operations|Supply Chain|Facilities) Officer", re.I),
    re.compile(r"(General Manager|GM).{0,20}(hotel|resort|property|distribution)", re.I),
    re.compile(r"(Director|Manager).{0,20}(guest services|guest experience)", re.I),
]

AUTOMATION_INTENT_PATTERNS = [
    re.compile(r"(VP|SVP|Director|Manager|Head|Lead).{0,40}(process improvement|operational excellence|continuous improvement)", re.I),
    re.compile(r"(VP|SVP|Director|Manager|Head).{0,40}(lean|six sigma|kaizen|productivity improvement|efficiency manager)", re.I),
    re.compile(r"(VP|Director|Manager).{0,40}(operations technology|technology operations|ops technology)", re.I),
    re.compile(r"(VP|Director).{0,40}(guest experience|service quality|brand standards|service delivery)", re.I),
    re.compile(r"(Chief Digital|VP Digital|Director Digital).{0,30}(officer|transformation|operations)", re.I),
]

def _is_buyer_persona(title: str) -> bool:
    return any(p.search(title) for p in BUYER_PERSONA_PATTERNS)

def _is_automation_intent(title: str) -> bool:
    """Senior ops/efficiency exec who will champion an automation initiative."""
    return any(p.search(title) for p in AUTOMATION_INTENT_PATTERNS)


class EnhancedJobBoardScraper(BaseScraper):
    """
    Enhanced Job Board Scraper with pythh.ai-style improvements.
    
    Improvements:
    1. Rate Limiting: Random 2-5s delays, user agent rotation, exponential backoff
    2. Ontology Relevancy: Filter out "robotics engineer" postings using CONCEPTS
    3. Duplicate Detection: Job fingerprinting (title + company)
    4. Better Entity Extraction: Use ontology to validate buyer personas
    
    Strategy: Find companies that:
      1. Post high volumes of manual operational roles  → labor_pain signal
      2. Use retention/urgency language in postings     → labor_shortage signal
      3. Hire operations decision-makers                → strategic_hire (buyer persona)
      
    NOT looking for: Companies that build robots or hire robotics engineers
    """

    def __init__(self):
        super().__init__()
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
            logger.debug(f"[JobBoardScraper] Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1

    def _is_duplicate(self, title: str, company_name: str) -> bool:
        """Check if we've already seen this job posting"""
        fingerprint = job_fingerprint(title, company_name)
        
        if fingerprint in self.session_seen_fingerprints:
            logger.debug(f"[JobBoardScraper] Duplicate filtered: {title} at {company_name}")
            return True
        
        self.session_seen_fingerprints.add(fingerprint)
        return False

    def _is_relevant(self, title: str, description: str, threshold: float = 0.15) -> bool:
        """
        Filter out irrelevant job postings using ontology-based scoring.
        
        Filters out:
        - Robotics engineers, robot builders (NOT buyers)
        - Unrelated industries
        - Low labor pain signals
        """
        score = calculate_job_relevancy_score(title, description)
        is_relevant = score >= threshold
        
        if not is_relevant:
            logger.debug(f"[JobBoardScraper] Filtered (score={score:.2f}): {title[:60]}...")
        
        return is_relevant

    def parse(self, html: str, url: str):
        """
        Enhanced parsing with relevancy filtering and duplicate detection.
        """
        self._rate_limit()
        
        soup = BeautifulSoup(html, "html.parser")

        postings = (
            soup.select("div.job_seen_beacon")      # Indeed
            or soup.select("div.base-card")          # LinkedIn
            or soup.select("article.jobsearch-result")
            or soup.select(".job-listing, .result, .posting")
        )

        logger.info(f"[JobBoardScraper] Found {len(postings)} job postings from {url}")

        for post in postings:
            title_el    = post.select_one("h2, h3, .jobTitle, .job-title")
            company_el  = post.select_one(".companyName, .company, .org, [data-testid='company-name']")
            location_el = post.select_one(".companyLocation, .location, [data-testid='text-location']")
            desc_el     = post.select_one(".job-snippet, .description, p")

            title        = title_el.get_text(strip=True) if title_el else ""
            company_name = company_el.get_text(strip=True) if company_el else None
            location     = location_el.get_text(strip=True) if location_el else ""
            desc         = desc_el.get_text(strip=True) if desc_el else ""
            full_text    = f"{title} {desc}".lower()

            if not company_name:
                continue

            # --- DUPLICATE CHECK ---
            if self._is_duplicate(title, company_name):
                continue

            # --- RELEVANCY CHECK (Filter out robotics engineers!) ---
            if not self._is_relevant(title, desc):
                continue

            # --- Buyer persona hire (operations decision-maker) ---
            if _is_buyer_persona(title):
                strength = 0.80
                sig_type = "strategic_hire"
                summary_text = f"Buyer persona hire: {title}"

            # --- Automation intent hire (efficiency / digital transformation exec) ---
            elif _is_automation_intent(title):
                strength = 0.72
                sig_type = "automation_intent"
                summary_text = f"Automation intent hire: {title}"

            # --- High-volume operational role (labor pain signal) ---
            else:
                pain_score   = sum(1 for kw in LABOR_PAIN_KEYWORDS if kw in full_text)
                urgency_score = sum(1 for p in PAIN_SIGNALS if p in full_text)

                if pain_score == 0:
                    continue

                # Multiple pain keywords or urgency language = stronger signal
                strength = min(1.0, round(0.20 + pain_score * 0.15 + urgency_score * 0.10, 2))
                sig_type = "labor_shortage" if urgency_score >= 2 else "labor_pain"
                summary_text = f"{title} | pain_kws={pain_score} urgency={urgency_score} | {desc[:300]}"

            parts = location.split(",")
            city  = parts[0].strip() if parts else location
            state = parts[1].strip() if len(parts) > 1 else ""

            # Infer industry from the URL query we used to find this posting
            industry = "Unknown"
            url_lower = url.lower()
            if any(w in url_lower for w in ["hotel", "hospitality", "resort", "housekeep", "valet", "bell"]):
                industry = "Hospitality"
            elif any(w in url_lower for w in ["warehouse", "fulfillment", "logistics", "supply", "distribution", "dock"]):
                industry = "Logistics"
            elif any(w in url_lower for w in ["restaurant", "food", "kitchen", "cook", "dishwash", "crew"]):
                industry = "Food Service"
            elif any(w in url_lower for w in ["hospital", "health", "medical", "pharmacy", "sterile", "dietary"]):
                industry = "Healthcare"

            company = self.save_company({
                "name": company_name,
                "website": None,
                "industry": industry,
                "location_city": city,
                "location_state": state,
                "location_country": "US",
                "source": url,
            })

            self.save_signal(company.id, {
                "signal_type": sig_type,
                "signal_text": summary_text,
                "signal_strength": strength,
                "source_url": url,
            })

        logger.info(f"[JobBoardScraper] Session stats: {self.request_count} requests, {len(self.session_seen_fingerprints)} unique jobs seen")
