"""
Contact Scraper
===============
Discovers real executive contacts for companies using:
  1. Google News RSS searches for executive names in press releases / articles
  2. Google Web search for LinkedIn profile URLs (name extracted from slug)
  3. Byline extraction from already-stored Signal.signal_text

For each company it targets the role defined in strategy.CONTACT_MAP, plus
a secondary "C-Suite" pass for the COO / CTO / VP Operations.

Flow
----
  ContactScraper(db).run_company(company)   → list[ContactCandidate]
  ContactScraper(db).run_top25()            → runs against current top-25 HOT leads

Results are UPSERTED into the `contacts` table.
  confidence_score 90  = LinkedIn URL slug parsed (name is in the URL)
  confidence_score 70  = byline / press-release name extraction
  confidence_score 50  = snippet-level name extraction (heuristic)

No LinkedIn login is required — names are extracted only from public Google
search result URLs and snippets.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import quote_plus, urlparse

import requests
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.company import Company
from app.models.contact import Contact
from app.models.signal import Signal

logger = logging.getLogger(__name__)

# ── HTTP headers (mirrors news_scraper.py) ──────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Target titles per industry  ──────────────────────────────────────────────
# Maps to the same industry strings used in strategy.CONTACT_MAP.
# Each entry = (primary_title, secondary_title)

TITLE_MAP: dict[str, tuple[str, str]] = {
    "Automotive Dealerships":           ("Fixed Ops Director",         "VP of Operations"),
    "Automotive Manufacturing":         ("VP of Manufacturing",        "Plant Manager"),
    "Automotive Innovation & Ventures": ("Innovation Director",        "CTO"),
    "Aerospace & Defense":              ("VP Manufacturing Operations","Director of MRO"),
    "Hospitality":                      ("VP of Operations",           "Director of Guest Services"),
    "Logistics":                        ("VP of Logistics",            "Warehouse Operations Manager"),
    "Healthcare":                       ("VP of Operations",           "Director of Supply Chain"),
    "Food Service":                     ("Director of Operations",     "COO"),
    "Casinos & Gaming":                 ("VP of Hotel Operations",     "VP of F&B"),
    "Cruise Lines":                     ("VP of Hotel Operations",     "F&B Director"),
    "Theme Parks & Entertainment":      ("VP of Operations",           "Director of Guest Experience"),
    "Real Estate & Facilities":         ("Director of Facilities",     "VP of Property Operations"),
    "Manufacturing":                    ("VP of Manufacturing",        "Plant Manager"),
    "Distribution":                     ("Director of Distribution",   "VP of Operations"),
    "Senior Living":                    ("VP of Operations",           "Director of Resident Services"),
    "Retail":                           ("VP of Store Operations",     "Director of In-Store Experience"),
}

_DEFAULT_TITLES = ("VP of Operations", "COO")

# ── Name extraction utilities ────────────────────────────────────────────────

# Match "First Last" before/after a title keyword
_NAME_BEFORE_TITLE = re.compile(
    r"\b([A-Z][a-z]{1,20}(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]{1,25})"
    r"\s*,?\s*"
    r"(VP|Vice President|Director|Chief|Head|Manager|President|COO|CTO|SVP|EVP)",
    re.UNICODE,
)

_NAME_AFTER_TITLE = re.compile(
    r"(?:VP|Vice President|Director|Chief|Head|Manager|President|COO|CTO|SVP|EVP)"
    r"\s+(?:of\s+)?(?:\w+\s+){0,3}"
    r"([A-Z][a-z]{1,20}\s+[A-Z][a-z]{1,25})\b",
    re.UNICODE,
)

# "says/said/told/according to [Name]"
_QUOTE_RE = re.compile(
    r"(?:says?|said|told|according to)\s+([A-Z][a-z]{1,20}\s+[A-Z][a-z]{1,25})\b",
    re.UNICODE,
)

# LinkedIn URL slug: /in/john-smith-abc123  → "John Smith"
_LINKEDIN_SLUG_RE = re.compile(
    r"linkedin\.com/in/([a-z]+-[a-z]+(?:-[a-z0-9]+)*)",
    re.IGNORECASE,
)

# ── False-positive blocklists ────────────────────────────────────────────────

# Complete full-name phrases that are never a person
_JUNK_NAMES = {
    "New York", "Los Angeles", "San Francisco", "Las Vegas", "United States",
    "North America", "South America", "West Coast", "East Coast",
    "General Manager", "Press Release", "About Us", "Read More",
    "Contact Us", "Privacy Policy", "Terms Service", "Burger King",
    "Walt Disney", "Hard Rock", "Four Seasons", "Omni Hotels",
    "Fannie Mae", "Apple Pay", "Whole Foods", "Best Buy",
    "San Diego", "New Jersey", "New Mexico", "New Orleans",
}

# Words that look like a capitalised first name but are NOT given names.
# Headline verbs, role prefixes, division names, adjectives.
_JUNK_FIRST_WORDS = {
    # Headline verbs / past-tense
    "Names", "Named", "Appoints", "Appointed", "Promotes", "Promoted",
    "Hires", "Hired", "Joins", "Adds", "Added", "Leaves", "Left",
    "Announces", "Announced", "Selects", "Selected", "Expands", "Taps",
    "Introduces", "Welcomes", "Elevates", "Brings", "Returns", "Replaces",
    # Descriptors / prefixes used in headlines
    "Former", "New", "Next", "Interim", "Acting", "Incoming",
    "Veteran", "Unfilled", "Open", "Vacant",
    # Role/department fragment words
    "Senior", "Regional", "Global", "Executive", "Corporate",
    "Chief", "Vice", "Assistant", "Associate",
    "Digital", "Human", "Technology", "Financial", "Legal", "Marketing",
    "Operating", "Commercial", "Strategic", "Operational", "Technical",
    "Clinical", "Medical", "Supply", "Logistics", "Warehouse",
    "Customer", "Investor", "Public", "Sales", "Service", "Services",
    "Workflow", "Talent", "Diversity", "Information", "Business",
    # Geographic/division
    "Western", "Eastern", "Southern", "Northern", "Central",
    "Pacific", "Atlantic", "Midwest", "National", "International",
    "Asia", "America", "Europe", "Africa", "Middle",
    # Other
    "Living", "Fleet", "Unfilled", "Automation", "Innovation",
    "Integration", "Management", "Acquisition", "Sustainability",
    # Common false-positive lead words
    "Area", "As", "Capital", "Market", "About", "After", "All",
    "An", "At", "By", "During", "Following", "For", "From", "In",
    "Its", "Of", "On", "Over", "Per", "The", "This", "To", "Via",
    "Hospitality", "Hotel", "Healthcare", "Logistics", "Retail",
    "Entertainment", "Pharmaceutical", "Industrial", "Residential",
}

# Words that look like a capitalised last name but are NOT surnames.
_JUNK_LAST_WORDS = {
    "Management", "Resources", "Operations", "Officer", "Division",
    "Services", "Relations", "Affairs", "Solutions", "Strategy",
    "Innovation", "Integration", "Automation", "Technology", "Systems",
    "Positions", "Vacancy", "Chairman", "Council", "Named", "Appointed",
    "Promoted", "Hired", "Added", "Announced", "Joined", "Announced",
    "Group", "Team", "Unit", "Center", "Centre", "Office", "Foundation",
    "Institute", "Partners", "Networks", "Holdings", "Brands", "Ventures",
    "International", "National", "Regional", "Global", "Corporate",
    "Director", "Manager", "President", "Executive", "Senior",
    "Operations", "Officer",
    # Additional false-positive tail words
    "Names", "New", "Mae", "Markets", "Managing", "Vice",
    "Way", "Day", "Week", "News", "Post", "Times", "Wire",
    "Inc", "Ltd", "Corp", "LLC", "Co", "Plc", "Llc",
    # Prepositions / particles that end up as last-name slot
    "As", "To", "In", "At", "Of", "On", "By", "For", "An",
    # Headline verbs appearing in last-word position
    "Hires", "Hired", "Joins", "Joined", "Names", "Named",
    "Appoints", "Appointed", "Promotes", "Promoted", "Taps",
    "Selects", "Adds", "Added", "Leaves", "Left", "Returns",
    # Role descriptors used as last word
    "Legal", "Assistant", "Affairs", "Relations", "Compliance",
    "Planning", "Strategy", "Communications", "Development",
}


@dataclass
class ContactCandidate:
    first_name: str
    last_name: str
    title: str
    linkedin_url: Optional[str] = None
    source_url: Optional[str] = None
    confidence_score: int = 50


# ── Core scraper ─────────────────────────────────────────────────────────────

class ContactScraper:

    def __init__(self, db: Session, delay: float = 1.2):
        self.db = db
        self.delay = delay

    # ── Public API ───────────────────────────────────────────────────────────

    def run_company(self, company: Company) -> list[ContactCandidate]:
        """Discover contacts for a single company, upsert into DB."""
        industry = (company.industry or "").strip()
        primary_title, secondary_title = TITLE_MAP.get(industry, _DEFAULT_TITLES)

        candidates: list[ContactCandidate] = []

        # 1. Extract names from stored signal text (zero network cost)
        candidates += self._extract_from_signals(company, primary_title)

        # 2. Google News RSS — press release bylines
        candidates += self._search_news(company, primary_title)
        time.sleep(self.delay)

        # 3. Google web search — LinkedIn slug extraction
        candidates += self._search_linkedin(company, primary_title)
        time.sleep(self.delay)

        # 4. Secondary title pass (fewer network calls)
        if not candidates:
            candidates += self._search_linkedin(company, secondary_title)
            time.sleep(self.delay)

        # Deduplicate & save best per full-name — drop conf < 70 (Pattern-2 after-title matches are too noisy)
        qualified = [c for c in candidates if c.confidence_score >= 70]
        best = self._deduplicate(qualified)
        for c in best:
            self._upsert_contact(company.id, c)

        logger.info(
            "  [contacts] %s → %d candidates, %d saved",
            company.name, len(candidates), len(best),
        )
        return best

    def run_top25(self) -> int:
        """Run contact discovery for the current top-25 HOT leads."""
        from app.services.lead_filter import classify_lead

        companies = (
            self.db.query(Company)
            .options()
            .limit(2000)
            .all()
        )

        # Score & rank (same logic as strategy.py)
        ranked = []
        for c in companies:
            junk, _, pri = classify_lead(c, c.scores, c.signals)
            if junk:
                continue
            ranked.append((pri.score, c))

        ranked.sort(key=lambda x: -x[0])
        top25 = [c for _, c in ranked[:25]]

        saved_total = 0
        for company in top25:
            results = self.run_company(company)
            saved_total += len(results)

        logger.info("[contacts] run_top25 complete — %d contacts saved", saved_total)
        return saved_total

    # ── Signal-text extraction ────────────────────────────────────────────────

    def _extract_from_signals(
        self, company: Company, target_title: str
    ) -> list[ContactCandidate]:
        """Extract names mentioned in existing stored signal texts."""
        signals: list[Signal] = company.signals or []
        found = []
        for sig in signals:
            text = sig.signal_text or ""
            for name, title, conf in self._extract_names_from_text(text):
                found.append(ContactCandidate(
                    first_name=name.split()[0],
                    last_name=" ".join(name.split()[1:]),
                    title=title or target_title,
                    source_url=sig.source_url,
                    confidence_score=conf,
                ))
        return found

    # ── Google News RSS ───────────────────────────────────────────────────────

    def _search_news(
        self, company: Company, target_title: str
    ) -> list[ContactCandidate]:
        """Search Google News RSS for press releases mentioning the executive."""
        queries = [
            f'"{company.name}" "{target_title}"',
            f'"{company.name}" appoints OR names OR promotes OR hires',
        ]
        found = []
        for q in queries:
            url = (
                "https://news.google.com/rss/search?q="
                + quote_plus(q)
                + "&hl=en-US&gl=US&ceid=US:en"
            )
            try:
                resp = requests.get(url, headers=_HEADERS, timeout=12)
                if resp.status_code != 200:
                    continue
                # Parse title + description snippets
                import xml.etree.ElementTree as ET
                root = ET.fromstring(resp.content)
                ns = {"media": "http://search.yahoo.com/mrss/"}
                for item in root.iter("item"):
                    title_el = item.find("title")
                    desc_el = item.find("description")
                    link_el = item.find("link")
                    text = " ".join(filter(None, [
                        title_el.text if title_el is not None else "",
                        desc_el.text if desc_el is not None else "",
                    ]))
                    link = link_el.text if link_el is not None else ""
                    for name, title, conf in self._extract_names_from_text(text):
                        found.append(ContactCandidate(
                            first_name=name.split()[0],
                            last_name=" ".join(name.split()[1:]),
                            title=title or target_title,
                            source_url=link,
                            confidence_score=conf,
                        ))
                time.sleep(self.delay)
            except Exception as e:
                logger.debug("  [contacts] news search error for %s: %s", company.name, e)
        return found

    # ── Google Web / LinkedIn slug ────────────────────────────────────────────

    def _search_linkedin(
        self, company: Company, target_title: str
    ) -> list[ContactCandidate]:
        """
        Search Google for LinkedIn profiles and extract names from the URL slug.
        Uses Google's standard search endpoint (public HTML).
        """
        q = f'"{company.name}" site:linkedin.com/in "{target_title}"'
        url = "https://www.google.com/search?q=" + quote_plus(q) + "&num=5"
        found = []
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=14)
            if resp.status_code != 200:
                logger.debug(
                    "  [contacts] Google returned %d for %s", resp.status_code, company.name
                )
                return found

            html = resp.text

            # Extract LinkedIn URLs from href attributes
            href_re = re.compile(r'href="(https?://(?:www\.)?linkedin\.com/in/[^"]+)"')
            matches = href_re.findall(html)

            for li_url in matches[:3]:
                parsed = urlparse(li_url)
                slug = parsed.path.rstrip("/").split("/")[-1]  # e.g. "john-smith-12345"
                name = self._name_from_slug(slug)
                if name:
                    found.append(ContactCandidate(
                        first_name=name[0],
                        last_name=name[1],
                        title=target_title,
                        linkedin_url=li_url.split("?")[0],  # strip tracking params
                        confidence_score=90,
                    ))

            # Also extract from code blocks / data-ved text snippets
            for name, title, conf in self._extract_names_from_text(html[:8000]):
                if title:  # only if we matched a title context
                    found.append(ContactCandidate(
                        first_name=name.split()[0],
                        last_name=" ".join(name.split()[1:]),
                        title=title or target_title,
                        confidence_score=max(conf, 50),
                    ))

        except Exception as e:
            logger.debug("  [contacts] LinkedIn search error for %s: %s", company.name, e)

        return found

    # ── Text name extraction ──────────────────────────────────────────────────

    def _extract_names_from_text(
        self, text: str
    ) -> list[tuple[str, str, int]]:
        """
        Returns list of (full_name, title_context, confidence_score).
        confidence: 70 if title context present, 50 for quote attribution.
        """
        results = []

        # Pattern 1: "First Last, VP of Something"
        for m in _NAME_BEFORE_TITLE.finditer(text):
            name = m.group(1).strip()
            title_context = m.group(2)
            if self._valid_name(name):
                results.append((name, title_context, 70))

        # Pattern 2: "VP of Something First Last"
        for m in _NAME_AFTER_TITLE.finditer(text):
            name = m.group(1).strip()
            if self._valid_name(name):
                results.append((name, "", 65))

        # Pattern 3: quote attribution — "said John Smith"
        for m in _QUOTE_RE.finditer(text):
            name = m.group(1).strip()
            if self._valid_name(name):
                results.append((name, "", 50))

        return results

    # ── LinkedIn slug → name ──────────────────────────────────────────────────

    def _name_from_slug(self, slug: str) -> Optional[tuple[str, str]]:
        """
        Convert a LinkedIn path slug like 'john-smith-12345a' → ('John', 'Smith').
        Returns None if the slug doesn't look like a real name.
        """
        # Remove trailing numeric IDs: john-smith-12345 → ['john', 'smith']
        parts = re.sub(r"-[0-9a-f]{4,}$", "", slug).split("-")
        # Expect exactly 2 name parts (first + last)
        name_parts = [p.capitalize() for p in parts if re.match(r"^[a-z]{2,}$", p)]
        if len(name_parts) >= 2:
            return name_parts[0], name_parts[1]
        return None

    # ── Validation ────────────────────────────────────────────────────────────

    @staticmethod
    def _valid_name(name: str) -> bool:
        if name in _JUNK_NAMES:
            return False
        parts = name.split()
        if len(parts) < 2 or len(parts) > 4:
            return False
        # Both first and last part must start with uppercase
        if not (parts[0][0].isupper() and parts[-1][0].isupper()):
            return False
        # First word must not be a known junk first-word
        if parts[0] in _JUNK_FIRST_WORDS:
            return False
        # Last word must not be a known junk last-word
        if parts[-1] in _JUNK_LAST_WORDS:
            return False
        # Reject multi-word strings where any part is a title keyword itself
        title_words = {"VP", "COO", "CTO", "CFO", "CEO", "SVP", "EVP",
                       "President", "Director", "Manager", "Head",
                       "General", "Vice", "Managing", "Chief",
                       "Inc", "Ltd", "Corp", "LLC", "Hotel", "Hotels",
                       "Resort", "Resorts", "The", "And", "For", "Of"}
        if any(p in title_words for p in parts):
            return False
        # Each name part should be 2-20 chars, letters only (allow hyphen and apostrophe)
        import re as _re
        for p in parts:
            if not _re.match(r"^[A-Za-z][A-Za-z'\-]{1,19}$", p):
                return False
        return True

    # ── Deduplication ─────────────────────────────────────────────────────────

    @staticmethod
    def _deduplicate(candidates: list[ContactCandidate]) -> list[ContactCandidate]:
        """Keep the highest-confidence candidate per full name."""
        best: dict[str, ContactCandidate] = {}
        for c in candidates:
            key = f"{c.first_name.lower()} {c.last_name.lower()}"
            if key not in best or c.confidence_score > best[key].confidence_score:
                best[key] = c
        return list(best.values())

    # ── DB upsert ─────────────────────────────────────────────────────────────

    def _upsert_contact(self, company_id: int, c: ContactCandidate) -> None:
        """Insert or update a contact row, keeping highest confidence."""
        # Hard minimum — Pattern-2 (conf:65) and quote-attribution (conf:50) are too noisy
        if (c.confidence_score or 0) < 70:
            return
        existing = (
            self.db.query(Contact)
            .filter(
                Contact.company_id == company_id,
                Contact.first_name == c.first_name,
                Contact.last_name == c.last_name,
            )
            .first()
        )
        if existing:
            if c.confidence_score > (existing.confidence_score or 0):
                existing.title = c.title or existing.title
                existing.linkedin_url = c.linkedin_url or existing.linkedin_url
                existing.confidence_score = c.confidence_score
        else:
            self.db.add(Contact(
                company_id=company_id,
                first_name=c.first_name,
                last_name=c.last_name,
                title=c.title,
                linkedin_url=c.linkedin_url,
                confidence_score=c.confidence_score,
            ))
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.warning("  [contacts] upsert failed: %s", e)
