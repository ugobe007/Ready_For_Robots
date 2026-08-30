"""
Enhanced Job Board Scraper — pythh.ai Style
===========================================
Improvements over original:
1. Rate Limiting & Anti-Bot: Random delays, user agent rotation, exponential backoff
2. Ontology-Based Relevancy: Filter out "robotics engineer" postings using CONCEPTS
3. Duplicate Detection: URL + title fingerprinting
4. Better Entity Extraction: Use ontology to validate buyer personas
"""
import json
import re
import time
import random
import hashlib
import logging
from typing import Any, Dict, Iterable, List, Optional, Set
from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

from app.scrapers.base_scraper import BaseScraper
from app.services.ontology import CONCEPTS
from app.services.robot_job_extract import (
    extract_robot_job,
    format_robot_job_signal,
    is_job_employer_name,
)
from app.services.robot_job_lifecycle import (
    apply_closeout_to_job,
    status_from_evidence,
    status_from_posting_text,
    upsert_robot_job_from_extract,
)

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

BUILDER_ROLE_NEEDLES = (
    "robotics engineer",
    "robot engineer",
    "automation engineer",
    "controls engineer",
    "mechatronics",
    "robot programmer",
    "robot technician",
    "robot builder",
    "robotics developer",
    "firmware engineer",
    "embedded engineer",
    "plc programmer",
)

# Indeed titles are often stems ("Cook", "Server", "Warehouse Worker", "EVS")
# not the long phrases in LABOR_PAIN_KEYWORDS. Phrase AND stem must both count.
OPERATIONAL_TITLE_PATTERNS = [
    re.compile(r"\b((?:line|prep|fry|grill|sous|breakfast|am|pm)\s+)?cooks?\b", re.I),
    re.compile(r"\b(dish\s?washers?|kitchen (?:staff|helper|worker)|food service)\b", re.I),
    re.compile(r"\b(crew members?|team members?|baristas?|cashiers?)\b", re.I),
    re.compile(
        r"\b(food runners?|bussers?|servers?|host(?:ess|es)?|waitstaff|waiters?)\b",
        re.I,
    ),
    re.compile(
        r"\b(housekeep(?:er|ing)?|room attendants?|housepersons?|housemen)\b",
        re.I,
    ),
    re.compile(
        r"\b(laundry attendants?|linen|bell(?:man|hop|staff)?|valets?|porters?|"
        r"concierge|front desk|night audit(?:or)?)\b",
        re.I,
    ),
    re.compile(
        r"\b(warehouse (?:worker|associate|clerk|operator)|pickers?|packers?|"
        r"stockers?|material handlers?|forklift|dock workers?|freight handlers?|"
        r"fulfillment|receiving|shipping associate)\b",
        re.I,
    ),
    re.compile(
        r"\b(patient transporters?|evs|environmental services|dietary aides?|"
        r"pharmacy technicians?|sterile processing|hospital aides?)\b",
        re.I,
    ),
    re.compile(
        r"\b(palletiz(?:er|ing)|pack(?:aging|out|-out|in|-in)(?: line)? operators?)\b",
        re.I,
    ),
    re.compile(
        r"\b(farm workers?|farm laborers?|harvest workers?|field workers?|"
        r"tractor operators?|orchard workers?|vineyard workers?)\b",
        re.I,
    ),
    re.compile(
        r"\b(construction laborers?|drywall (?:finishers?|hangers?)|"
        r"framing carpenters?|bricklayers?|masons?)\b",
        re.I,
    ),
    re.compile(
        r"\b(haul truck (?:operators?|drivers?)|underground miners?|"
        r"mine (?:laborers?|operators?))\b",
        re.I,
    ),
    re.compile(
        r"\b(cnc (?:operators?|tenders?)|machine tenders?|"
        r"machine operators?|production (?:line )?operators?)\b",
        re.I,
    ),
]


def _is_builder_role(title: str, description: str = "") -> bool:
    combined = f"{title or ''} {description or ''}".lower()
    return any(needle in combined for needle in BUILDER_ROLE_NEEDLES)


def operational_labor_hits(title: str, description: str = "") -> int:
    """Phrase keywords plus title stems. Cook / Server / EVS must count."""
    combined = f"{title or ''} {description or ''}".lower()
    phrase = sum(1 for kw in LABOR_PAIN_KEYWORDS if kw in combined)
    stems = sum(1 for pattern in OPERATIONAL_TITLE_PATTERNS if pattern.search(combined))
    return phrase + stems


def is_operational_robot_job(title: str, description: str = "") -> bool:
    if _is_builder_role(title, description):
        return False
    return operational_labor_hits(title, description) > 0


def calculate_job_relevancy_score(title: str, description: str) -> float:
    """
    Score job posting relevancy from 0.0-1.0.
    HIGH score = operations buyer persona OR high labor pain
    LOW score = robotics engineer, robot builder (filter these out!)
    """
    combined = f"{title} {description}".lower()

    if _is_builder_role(title, description):
        return 0.0

    # BOOST: Buyer persona matches
    buyer_matches = 0
    for keyword in BUYER_KEYWORDS:
        if isinstance(keyword, str) and any(ch in keyword for ch in ".{?*+"):
            if re.search(keyword, combined, re.I):
                buyer_matches += 1
        elif isinstance(keyword, str):
            if keyword.lower() in combined:
                buyer_matches += 1
        elif re.search(keyword, combined):
            buyer_matches += 1
    if any(p.search(title or "") for p in BUYER_PERSONA_PATTERNS):
        buyer_matches = max(buyer_matches, 1)
    if any(p.search(title or "") for p in AUTOMATION_INTENT_PATTERNS):
        buyer_matches = max(buyer_matches, 1)

    # BOOST: Labor pain signals (ontology)
    pain_matches = 0
    for keyword in PAIN_KEYWORDS:
        if isinstance(keyword, str):
            if keyword.lower() in combined:
                pain_matches += 1
        else:  # regex pattern
            if re.search(keyword, combined):
                pain_matches += 1

    # BOOST: Operational Robot Job titles — phrases and stems (Cook, EVS, …)
    labor_matches = operational_labor_hits(title, description)

    # Buyer persona = high signal; operational title = Robot Job; ontology pain = extra
    score = min(
        1.0,
        (buyer_matches * 0.20) + (pain_matches * 0.10) + (labor_matches * 0.25),
    )
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
    "barista", "cashier", "janitor", "custodian", "restroom attendant",
    "floor cleaner", "banquet cook",
    # Healthcare
    "patient transport", "environmental services", "sterile processing",
    "pharmacy technician", "dietary aide", "hospital aide", "EVS tech",
    "linen service", "supply chain tech",
    "picker", "stocker", "housekeeping", "food service worker",
    "patient transporter",
    "warehouse worker", "night auditor", "houseperson",
    "palletizer", "packaging line",
    "farm worker", "harvest worker", "tractor operator", "farm laborer",
    "construction laborer", "drywall finisher", "framing carpenter",
    "haul truck operator", "haul truck driver", "underground miner",
    "cnc operator", "machine tender", "machine operator",
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


CHALLENGE_MARKERS = (
    "just a moment",
    "unusual traffic",
    "enable javascript",
    "captcha",
    "verify you are human",
    "blocked",
)

JOB_CARD_SELECTORS = (
    "div.job_seen_beacon, "
    "div.base-card, "
    "article.jobsearch-result, "
    ".SerpJob-jobCard, "
    "div.SerpJob, "
    "[data-testid='searchSerpJob'], "
    "[data-testid='jobCard'], "
    ".job-listing, "
    "article.posting"
)


def _text(el) -> str:
    if el is None:
        return ""
    attr = (el.get("title") or el.get("aria-label") or "").strip()
    body = el.get_text(" ", strip=True)
    return attr or body


def _jsonld_locality(location: Any) -> str:
    if isinstance(location, list) and location:
        location = location[0]
    if not isinstance(location, dict):
        return ""
    address = location.get("address") or location
    if isinstance(address, list) and address:
        address = address[0]
    if not isinstance(address, dict):
        return str(location.get("name") or "")
    city = (address.get("addressLocality") or "").strip()
    region = (address.get("addressRegion") or "").strip()
    return ", ".join(part for part in (city, region) if part)


def iter_jsonld_job_postings(soup: BeautifulSoup) -> Iterable[dict]:
    for script in soup.select("script[type='application/ld+json']"):
        raw = script.string or script.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        items: List[Any]
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "@graph" in data:
            graph = data.get("@graph")
            items = graph if isinstance(graph, list) else [graph]
        else:
            items = [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            types = item.get("@type")
            type_list = types if isinstance(types, list) else [types]
            if "JobPosting" not in type_list:
                continue
            yield item


def jsonld_card(item: dict) -> Optional[Dict[str, str]]:
    title = (item.get("title") or "").strip()
    if not title:
        return None
    org = item.get("hiringOrganization") or {}
    if isinstance(org, list):
        org = org[0] if org else {}
    company = ""
    if isinstance(org, dict):
        company = (org.get("name") or "").strip()
    elif isinstance(org, str):
        company = org.strip()
    desc_html = item.get("description") or ""
    desc = BeautifulSoup(str(desc_html), "html.parser").get_text(" ", strip=True)
    return {
        "title": title,
        "company": company,
        "location": _jsonld_locality(item.get("jobLocation")),
        "desc": desc,
        "url": (item.get("url") or "").strip(),
        "html": str(desc_html) if desc_html else "",
        "jsonld": item,
    }


def card_fields_from_element(post) -> Dict[str, str]:
    title_el = post.select_one(
        "h2.jobTitle span[title], a.jcs-JobTitle span[title], a.jcs-JobTitle, "
        ".jobposting-title, [data-testid='jobTitle'], h2.jobTitle, "
        "h2, h3, .jobTitle, .job-title"
    )
    company_el = post.select_one(
        "[data-testid='company-name'], [data-testid='companyName'], "
        "[data-testid='searchSerpJob-companyName'], "
        ".companyName, span.companyName, .jobposting-company, .company, .org"
    )
    location_el = post.select_one(
        "[data-testid='text-location'], .companyLocation, "
        ".jobposting-location, .location"
    )
    desc_el = post.select_one(
        "[data-testid='job-snippet'], .job-snippet, .jobposting-snippet, .description"
    )
    return {
        "title": _text(title_el),
        "company": _text(company_el),
        "location": _text(location_el),
        "desc": _text(desc_el),
        "url": "",
        "html": str(post) if post is not None else "",
    }


class EnhancedJobBoardScraper(BaseScraper):
    """
    Enhanced Job Board Scraper with pythh.ai-style improvements.
    
    Improvements:
    1. Rate Limiting: Random 2-5s delays, user agent rotation, exponential backoff
    2. Ontology Relevancy: Filter out "robotics engineer" postings using CONCEPTS
    3. Duplicate Detection: Job fingerprinting (title + company)
    4. Better Entity Extraction: Use ontology to validate buyer personas
    
    Strategy: Find Robot Jobs — human work a robot could be hired to do:
      1. Operational titles (picker, housekeeper, EVS) with pay/specs when evidenced
      2. Re-check evidence later so jobs fill (robot deployed) or withdraw
      3. Ops VP hires remain SIGNAL leftovers (strategic_hire), not Robot Jobs

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
        """Keep operational Robot Jobs and buyer hires; drop robot-builder roles."""
        score = calculate_job_relevancy_score(title, description)
        is_relevant = score >= threshold
        if not is_relevant:
            logger.debug(f"[JobBoardScraper] Filtered (score={score:.2f}): {title[:60]}...")
        return is_relevant

    def _run_bare(self, start_urls: list):
        """Wait for mosaic cards / JSON-LD so Indeed SPA HTML is actually present."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(user_agent=self._random_user_agent())
            for url in start_urls:
                try:
                    def visit():
                        page = context.new_page()
                        page.goto(url, timeout=45000)
                        try:
                            page.wait_for_selector(
                                "div.job_seen_beacon, .SerpJob-jobCard, "
                                "script[type='application/ld+json']",
                                timeout=8000,
                            )
                        except PWTimeout:
                            logger.warning(
                                "[JobBoardScraper] no job cards/jsonld within 8s url=%s",
                                url,
                            )
                        content = page.content()
                        page.close()
                        return content

                    html = self._retry(visit)
                    self.parse(html, url)
                except PWTimeout:
                    logger.error("Timeout visiting %s", url)
                except Exception as e:
                    logger.exception("Error scraping %s: %s", url, e)
            browser.close()

    def _collect_cards(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, str]]:
        postings = soup.select(JOB_CARD_SELECTORS)
        if not postings:
            postings = soup.select(".result, .posting")
        css_cards = [card_fields_from_element(post) for post in postings]
        jsonld_cards = [
            card for card in (jsonld_card(item) for item in iter_jsonld_job_postings(soup)) if card
        ]
        by_title = {
            normalize_job_title(card["title"]): card
            for card in jsonld_cards
            if card.get("title")
        }
        for card in css_cards:
            match = by_title.get(normalize_job_title(card.get("title") or ""))
            if not match:
                continue
            if not card.get("company") and match.get("company"):
                card["company"] = match["company"]
            if not card.get("location"):
                card["location"] = match.get("location") or ""
            if not card.get("desc"):
                card["desc"] = match.get("desc") or ""
            if match.get("jsonld") and not card.get("jsonld"):
                card["jsonld"] = match["jsonld"]
            if match.get("html") and "mailto:" not in (card.get("html") or "").lower():
                card["html"] = (card.get("html") or "") + "\n" + (match.get("html") or "")
        cards = css_cards
        if not cards:
            cards = jsonld_cards
            for card in cards:
                if not card.get("url"):
                    card["url"] = page_url
        if not cards:
            blob = soup.get_text(" ", strip=True).lower()
            if any(marker in blob for marker in CHALLENGE_MARKERS):
                logger.warning("[JobBoardScraper] challenge/empty page url=%s", page_url)
        return cards

    def _persist_robot_job(
        self,
        *,
        extract: dict,
        company_id: Optional[int],
        company_name: str,
        title: str,
        desc: str,
        source_url: str,
    ) -> bool:
        try:
            row = upsert_robot_job_from_extract(
                self.db,
                company_id=company_id,
                extract=extract,
                source_url=source_url,
            )
            if row is None:
                logger.warning(
                    "[JobBoardScraper] robot_jobs upsert returned none for %s",
                    title[:80],
                )
                return False
            close = status_from_evidence(
                employer=company_name,
                job_title=title,
                job_function=extract.get("job_function"),
                evidence_text=desc,
            )
            apply_closeout_to_job(row, close)
            self.db.commit()
            return True
        except Exception:
            logger.exception("[JobBoardScraper] robot_jobs persist skipped for %s", title[:80])
            try:
                self.db.rollback()
            except Exception:
                pass
            return False

    def parse(self, html: str, url: str):
        """
        Enhanced parsing with relevancy filtering and duplicate detection.
        """
        self._rate_limit()

        soup = BeautifulSoup(html, "html.parser")
        cards = self._collect_cards(soup, url)

        logger.info(f"[JobBoardScraper] Found {len(cards)} job postings from {url}")
        skipped_no_company = skipped_relevancy = skipped_no_pain = 0
        kept_robot_job = kept_hire = 0

        for card in cards:
            title = card.get("title") or ""
            company_name = (card.get("company") or "").strip() or None
            location = card.get("location") or ""
            desc = card.get("desc") or ""
            source_url = card.get("url") or url

            if not company_name or not is_job_employer_name(company_name, title=title):
                skipped_no_company += 1
                continue

            if self._is_duplicate(title, company_name):
                continue

            if not self._is_relevant(title, desc):
                skipped_relevancy += 1
                continue

            robot_job_extract = None
            if _is_buyer_persona(title):
                strength = 0.80
                sig_type = "strategic_hire"
                summary_text = f"Buyer persona hire: {title}"
            elif _is_automation_intent(title):
                strength = 0.72
                sig_type = "automation_intent"
                summary_text = f"Automation intent hire: {title}"
            elif is_operational_robot_job(title, desc):
                pain_score = operational_labor_hits(title, desc)
                urgency_score = sum(1 for p in PAIN_SIGNALS if p in f"{title} {desc}".lower())
                job = extract_robot_job(
                    title=title,
                    description=desc,
                    company=company_name,
                    locality=location,
                    source_url=source_url,
                    html=card.get("html") or "",
                    jsonld=card.get("jsonld"),
                )
                posting_state = status_from_posting_text(desc)
                job["status"] = posting_state["status"]
                strength = min(1.0, round(0.20 + pain_score * 0.15 + urgency_score * 0.10, 2))
                sig_type = "robot_job"
                summary_text = format_robot_job_signal(job)
                robot_job_extract = job
            else:
                # Relevancy passed via ontology/buyer keywords, but this is not
                # operational work (e.g. generic GM). Do not invent a Robot Job.
                skipped_no_pain += 1
                continue

            parts = location.split(",")
            city = parts[0].strip() if parts else location
            state = parts[1].strip() if len(parts) > 1 else ""

            industry = "Unknown"
            url_lower = source_url.lower()
            if any(w in url_lower for w in ["restaurant", "food", "kitchen", "cook", "dishwash", "crew", "qsr", "make+line", "make%20line", "bowl+assembly", "bowl%20assembly", "tortilla", "prep+cook", "fast+casual", "fast%20casual", "banquet+cook", "dining", "server", "busser"]):
                industry = "Food Service"
            elif any(w in url_lower for w in ["janitor", "custodian", "restroom", "cleaning", "commercial+cleaning"]):
                industry = "Cleaning"
            elif any(w in url_lower for w in ["hotel", "hospitality", "resort", "housekeep", "valet", "bell"]):
                industry = "Hospitality"
            elif any(w in url_lower for w in ["farm", "harvest", "orchard", "vineyard", "tractor", "agricultural"]):
                industry = "Agriculture"
            elif any(w in url_lower for w in ["construction", "drywall", "jobsite", "bricklay"]):
                industry = "Construction"
            elif any(w in url_lower for w in ["mining", "haul+truck", "haul%20truck", "underground+miner"]):
                industry = "Mining"
            elif any(w in url_lower for w in ["cnc", "machine+tend", "palletizer", "manufacturing", "factory"]):
                industry = "Factory"
            elif any(w in url_lower for w in ["warehouse", "fulfillment", "logistics", "supply", "distribution", "dock"]):
                industry = "Logistics"
            elif any(w in url_lower for w in ["janitor", "custodian", "restroom", "data+center", "data%20center"]):
                industry = "Hospitality"
            elif any(w in url_lower for w in ["hospital", "health", "medical", "pharmacy", "sterile", "dietary"]):
                industry = "Healthcare"

            company = self.save_company({
                "name": company_name,
                "website": None,
                "industry": industry,
                "location_city": city,
                "location_state": state,
                "location_country": "US",
                "source": source_url,
            })
            if company is None:
                skipped_no_company += 1
                if robot_job_extract is not None and self._persist_robot_job(
                    extract=robot_job_extract,
                    company_id=None,
                    company_name=company_name,
                    title=title,
                    desc=desc,
                    source_url=source_url,
                ):
                    kept_robot_job += 1
                continue

            self.save_signal(company.id, {
                "signal_type": sig_type,
                "signal_text": summary_text,
                "signal_strength": strength,
                "source_url": source_url,
            })
            if robot_job_extract is None:
                kept_hire += 1
            elif self._persist_robot_job(
                extract=robot_job_extract,
                company_id=company.id,
                company_name=company_name,
                title=title,
                desc=desc,
                source_url=source_url,
            ):
                kept_robot_job += 1

        logger.info(
            "[JobBoardScraper] page yield found=%d robot_jobs=%d hires=%d "
            "skipped_relevancy=%d skipped_no_company=%d skipped_no_pain=%d url=%s",
            len(cards),
            kept_robot_job,
            kept_hire,
            skipped_relevancy,
            skipped_no_company,
            skipped_no_pain,
            url,
        )
        logger.info(
            "[JobBoardScraper] Session stats: %s requests, %s unique jobs seen",
            self.request_count,
            len(self.session_seen_fingerprints),
        )
