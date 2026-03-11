"""
Intelligence News Scraper — Company Discovery & Signal Correlation
===================================================================
FREE alternative to LinkedIn, Pitchbook, CB Insights by correlating:
- Google News RSS (expansion, funding, hiring, labor issues)
- Company entity extraction (NLP + pattern matching)
- Cross-reference with existing DB to enrich or create leads
- Signal correlation (news keywords → buying intent signals)

KEY ADVANTAGES:
- $0 cost vs. $20K-$50K/year for paid services
- Real-time discovery (not quarterly reports)
- Unbiased coverage (not limited to VC-backed companies)
- Automated enrichment of existing leads

STRATEGY:
1. Search news for industry-specific keywords (warehouse automation, hotel labor shortage, etc)
2. Extract company names from articles using NLP + regex patterns
3. Cross-reference: if company exists → add signal, if new → create lead
4. Score based on signal strength and keyword relevance
5. Auto-classify signal type (funding, expansion, hiring, labor_shortage, etc)

Usage:
    scraper = IntelligenceNewsScraper(db=db)
    scraper.discover_leads(max_articles=50)  # Run daily to find new leads
    scraper.enrich_existing_companies()  # Enrich companies already in DB
"""
import logging
import re
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.services.inference_engine import analyze
from app.services.signal_classifier import classify_signals_with_fallback

logger = logging.getLogger(__name__)

# ── High-Intent Industry Keywords (expansion, automation, labor pain) ─────────
DISCOVERY_QUERIES = [
    # Logistics & Warehousing
    "warehouse automation investment 2026",
    "logistics robotics deployment funding 2026",
    "distribution center expansion construction 2026",
    "3PL warehouse labor shortage staffing 2026",
    "fulfillment center AMR AGV robot deployment",
    "cold storage automation expansion facility",
    "supply chain automation capex investment 2026",
    "warehouse worker shortage overtime costs 2026",
    
    # Hospitality
    "hotel labor shortage housekeeping staffing 2026",
    "hotel chain expansion opening properties 2026",
    "resort automation service robot pilot 2026",
    "hotel minimum wage labor cost operations 2026",
    "hospitality technology investment funding 2026",
    "hotel EVS cleaning staffing shortage crisis",
    
    # Food Service
    "restaurant automation kitchen robot deployment 2026",
    "restaurant chain expansion new locations 2026",
    "QSR labor shortage staffing turnover 2026",
    "fast food automation investment technology 2026",
    "restaurant delivery robot pilot program 2026",
    "food service worker shortage wage pressure 2026",
    
    # Healthcare & Senior Living
    "hospital EVS housekeeping staffing shortage 2026",
    "senior living facility expansion construction 2026",
    "hospital disinfection robot UV-C deployment 2026",
    "nursing home caregiver shortage staffing crisis",
    "healthcare automation investment technology 2026",
    "hospital labor costs wage pressure overtime",
    
    # Casinos & Gaming
    "casino labor shortage F&B beverage service 2026",
    "casino resort expansion opening properties 2026",
    "casino robotics automation technology pilot",
    "integrated resort staffing shortage operations",
    
    # Theme Parks & Entertainment
    "theme park labor shortage seasonal staffing 2026",
    "amusement park automation custodial operations",
    "theme park food service technology investment",
    
    # Executive Hiring (Strategic Signal)
    "VP operations hired logistics warehouse 2026",
    "Chief Operations Officer appointed hospitality hotel",
    "Director automation robotics technology hired",
    "VP supply chain logistics hired appointed 2026",
    "COO restaurant chain food service hired 2026",
    
    # M&A & Funding (High Intent)
    "logistics company acquisition merger warehouse 2026",
    "hospitality hotel funding round investment 2026",
    "warehouse automation startup series A B C 2026",
    "restaurant chain private equity acquisition 2026",
    "healthcare technology funding round investment",
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🤖 ROBOT DEPLOYMENT & USE CASE INTELLIGENCE (New - March 2026)
    # ═══════════════════════════════════════════════════════════════════════
    
    # Actual Robot Installations (TIER 1 - Highest Value)
    "hotel deploys housekeeping robot 2026",
    "warehouse implements AMR fleet 2026",
    "hospital installs disinfection robot 2026",
    "restaurant introduces service robot 2026",
    "airport deploys cleaning robot 2026",
    "manufacturing implements cobot production 2026",
    "facility installs autonomous floor scrubber 2026",
    
    # ROI & Economics (Buyer Perspective)
    "robot automation ROI case study 2026",
    "warehouse automation payback period",
    "labor cost savings robot deployment",
    "automation reduces headcount",
    "service robot saves money",
    "robot investment return hospitality",
    
    # Success Stories & Pilot Expansions (Proof Points)
    "successful robot pilot program 2026",
    "automation pilot expands deployment",
    "robot trial becomes permanent",
    "automated warehouse success story 2026",
    "robot deployment exceeds expectations",
    
    # Specific Vendor Deployments (Market Intelligence)
    "Savioke Relay robot hotel deployment",
    "MiR robot warehouse installation 2026",
    "Universal Robots cobot manufacturing",
    "Fetch Robotics warehouse automation",
    "Bear Robotics restaurant robot deployed",
    "Diligent Robotics Moxi hospital",
    "Knightscope security robot patrol",
    "Brain Corp autonomous floor scrubber",
    "Locus Robotics warehouse picking",
    "GreyOrange warehouse automation 2026",
    
    # Problem → Solution Narratives
    "labor shortage solved by robots 2026",
    "automation addresses staffing crisis",
    "robots fill open positions",
    "warehouse turnover reduced automation",
    "24/7 operations enabled robots",
    "robot eliminates repetitive tasks",
    
    # Technology Trends (Analyst Perspective)
    "AI-powered warehouse robotics 2026",
    "collaborative robots hospitality",
    "autonomous mobile robot fleet management",
    "computer vision warehouse picking 2026",
    "LiDAR navigation service robots",
    "robotics-as-a-service model 2026",
    
    # Competitive Pressure (Market Dynamics)
    "competitor automates forces response",
    "automation competitive advantage 2026",
    "rivals deploy robots market pressure",
    "industry peers adopt automation",
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🏥 MEDICAL TECHNOLOGY AUTOMATION (New Categories - March 2026)
    # ═══════════════════════════════════════════════════════════════════════
    
    # Laboratory Automation
    "lab automation robot deployment 2026",
    "laboratory automation investment funding 2026",
    "clinical lab automation system installation",
    "diagnostics lab automation expansion 2026",
    "automated specimen processing lab 2026",
    "lab technician shortage automation solution",
    "pathology lab automation investment 2026",
    "liquid handling robot lab deployment",
    "automated sample testing laboratory 2026",
    
    # Pharmacy Automation
    "pharmacy automation robot deployment 2026",
    "hospital pharmacy automation investment 2026",
    "automated dispensing system pharmacy 2026",
    "retail pharmacy automation technology 2026",
    "pharmacy robot medication dispensing 2026",
    "pharmacy technician shortage automation 2026",
    "automated prescription filling system 2026",
    "IV compounding robot pharmacy 2026",
    
    # Surgical Robotics
    "surgical robot deployment hospital 2026",
    "robotic surgery program expansion 2026",
    "surgical robotics investment funding 2026",
    "da Vinci robot installation hospital 2026",
    "robotic assisted surgery program launch 2026",
    "surgical suite automation investment 2026",
    
    # Patient Care Automation
    "patient care robot hospital deployment 2026",
    "hospital automation patient monitoring 2026",
    "nursing assistant robot healthcare 2026",
    "patient transport automation hospital 2026",
    "automated patient room cleaning 2026",
    "telepresence robot patient care 2026",
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🍔 FOOD AUTOMATION (Production & Service)
    # ═══════════════════════════════════════════════════════════════════════
    
    # Food Preparation Automation
    "robotic kitchen automation deployment 2026",
    "automated food prep robot restaurant 2026",
    "cooking robot installation kitchen 2026",
    "food preparation automation investment 2026",
    "robotic chef deployment restaurant 2026",
    "automated fryer robot kitchen 2026",
    "robotic pizza making deployment 2026",
    "automated burger grill restaurant 2026",
    
    # Food Serving Automation
    "restaurant service robot deployment 2026",
    "automated food delivery robot restaurant 2026",
    "server robot dining room deployment 2026",
    "restaurant automation server shortage 2026",
    "food runner robot deployment 2026",
    
    # Food Processing & Manufacturing
    "food processing automation investment 2026",
    "food manufacturing robot deployment 2026",
    "meat processing automation system 2026",
    "bakery automation robot deployment 2026",
    "food packaging automation investment 2026",
    "produce processing automation 2026",
    "food safety automation inspection 2026",
    "automated food sorting system 2026",
    
    # ═══════════════════════════════════════════════════════════════════════
    # 💾 DATACENTER AUTOMATION
    # ═══════════════════════════════════════════════════════════════════════
    
    "datacenter automation robot deployment 2026",
    "data center robotics investment 2026",
    "automated server maintenance datacenter 2026",
    "datacenter infrastructure automation 2026",
    "robotic datacenter operations 2026",
    "automated cooling system datacenter 2026",
    "datacenter technician shortage automation",
    "lights-out datacenter automation 2026",
    "AI datacenter automation investment 2026",
    "hyperscale datacenter automation 2026",
    
    # ═══════════════════════════════════════════════════════════════════════
    # ✈️ AIRPORT AUTOMATION
    # ═══════════════════════════════════════════════════════════════════════
    
    "airport automation robot deployment 2026",
    "airport cleaning robot deployment 2026",
    "airport baggage handling automation 2026",
    "airport security automation technology 2026",
    "automated shuttle airport transportation 2026",
    "airport terminal cleaning automation 2026",
    "airport operations automation investment 2026",
    "airport labor shortage automation solution",
    "automated boarding gate system airport 2026",
    "airport disinfection robot deployment 2026",
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🛍️ RETAIL AUTOMATION
    # ═══════════════════════════════════════════════════════════════════════
    
    "retail store automation robot deployment 2026",
    "retail automation investment technology 2026",
    "automated inventory robot retail 2026",
    "retail shelf scanning robot deployment 2026",
    "grocery store automation robot 2026",
    "retail cashier automation checkout 2026",
    "retail fulfillment automation 2026",
    "retail worker shortage automation solution",
    "automated retail cleaning robot 2026",
    "retail stockroom automation robot 2026",
    "click-and-collect automation retail 2026",
    "micro-fulfillment center retail automation",
    
    # ═══════════════════════════════════════════════════════════════════════
    # 👕 CLOTHING & APPAREL AUTOMATION
    # ═══════════════════════════════════════════════════════════════════════
    
    # Apparel Manufacturing
    "garment manufacturing automation robot 2026",
    "apparel factory automation investment 2026",
    "automated sewing robot clothing 2026",
    "textile automation manufacturing 2026",
    "clothing production automation robot 2026",
    "fabric cutting automation apparel 2026",
    "fashion manufacturing automation 2026",
    
    # Apparel Logistics & Distribution
    "apparel warehouse automation robot 2026",
    "clothing distribution automation 2026",
    "fashion logistics automation investment 2026",
    "automated garment sorting system 2026",
    "apparel fulfillment automation robot 2026",
    "clothing e-commerce automation 2026",
    "automated apparel picking system 2026",
]

# ── Company Entity Extraction Patterns ────────────────────────────────────────
# Pattern: "Company X announces/says/opens/invests/hires/raises..."
COMPANY_PATTERN = re.compile(
    r'\b([A-Z][A-Za-z0-9&\.\'\-\, ]{2,50}?)\s+'
    r'(?:announce[ds]?|say[s]?|report[s]?|invest[s]?|open[s]?|launch[es]?|'
    r'deploy[s]?|hire[s]?|appoint[s]?|raise[s]?|acquire[s]?|pilot[s]?|'
    r'expand[s]?|build[s]?|commit[s]?|plan[s]?|struggle[s]?|face[s]?)\b',
    re.IGNORECASE
)

# Pattern: "at Company X" or "Company X's CEO" or "Company X is"
COMPANY_CONTEXT = re.compile(
    r'(?:at|for|with|from)\s+([A-Z][A-Za-z0-9&\.\'\-\, ]{2,50}?)'
    r'(?:\s+(?:is|said|says|has|will|plans|faces|struggles)|\'s|\,)',
    re.IGNORECASE
)

# ── Signal Classification Keywords ────────────────────────────────────────────
SIGNAL_PATTERNS = {
    "funding_round": [
        "series a", "series b", "series c", "funding round", "raised $", 
        "investment", "venture capital", "vc funding", "private equity", 
        "capital raise", "financing", "investors"
    ],
    "expansion": [
        "expansion", "new facility", "new warehouse", "new distribution center",
        "new hotel", "new property", "opening", "construction", "breaking ground",
        "square feet", "sf facility", "development", "build"
    ],
    "strategic_hire": [
        "vp ", "svp ", "coo", "chief operating", "vice president", "director of",
        "head of", "appointed", "hired", "joins as", "new executive",
        "chief ", "executive vice president", "evp "
    ],
    "labor_shortage": [
        "labor shortage", "worker shortage", "staffing shortage", "can't find workers",
        "difficulty hiring", "turnover", "retention", "wage pressure",
        "overtime costs", "understaffed", "hiring challenges"
    ],
    "ma_activity": [
        "acquisition", "acquires", "merger", "merges with", "buyout",
        "joint venture", "strategic partnership", "acquired by",
        "purchased", "consolidation"
    ],
    "capex": [
        "capex", "capital expenditure", "capital investment", "investing $",
        "allocated $", "budget", "spending $", "deployment"
    ],
    "automation_interest": [
        "automation", "robotics", "robot", "agv", "amr", "autonomous",
        "automated", "ai ", "artificial intelligence", "machine learning",
        "technology investment", "digital transformation"
    ],
    "news": [
        "announced", "reports", "statement", "press release"
    ],
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🤖 DEPLOYMENT-FOCUSED SIGNALS (New - March 2026)
    # ═══════════════════════════════════════════════════════════════════════
    
    "robot_installation": [
        "deployed robot", "installed robot", "implements robot", "robot deployment",
        "fleet of robots", "robotic system", "automation system installed",
        "robot went live", "robot operational", "robot in production"
    ],
    "pilot_success": [
        "successful pilot", "pilot exceeded", "trial success", "pilot expands",
        "pilot to production", "trial becomes permanent", "proof of concept success",
        "pilot program positive results"
    ],
    "roi_documented": [
        "roi", "return on investment", "payback period", "payback in",
        "saves $", "cost savings", "reduced costs by", "labor savings",
        "efficiency gains", "productivity increase", "% faster", "% reduction"
    ],
    "vendor_selection": [
        "selected", "chose", "partnered with", "contracted with",
        "working with vendor", "supplier chosen", "provider selected",
        "signed agreement", "multi-year deal"
    ],
    "scale_expansion": [
        "expanding from", "scaling to", "increasing fleet", "adding more robots",
        "rollout to", "deploying across", "fleet expansion", "pilot to full deployment"
    ],
    "competitive_response": [
        "following competitor", "in response to", "after rival", "matching competitor",
        "keeping pace with", "competitive pressure", "industry peers adopting"
    ],
    "economics_driven": [
        "labor cost", "cost per unit", "economics favor", "financially viable",
        "business case", "justified by", "driven by costs", "return exceeds",
        "cheaper than labor", "vs human cost"
    ],
    "problem_solution": [
        "solves", "addresses", "eliminates", "fixes", "resolves",
        "overcomes challenge", "tackles issue", "solution to", "fills gap"
    ],
}

# ── Industry Detection Keywords ───────────────────────────────────────────────
INDUSTRY_KEYWORDS = {
    "Logistics": [
        "warehouse", "logistics", "fulfillment", "distribution", "supply chain",
        "3pl", "cold storage", "freight", "shipping", "delivery"
    ],
    "Hospitality": [
        "hotel", "resort", "hospitality", "lodging", "motel", "inn",
        "housekeeping", "guest services", "property management"
    ],
    "Food Service": [
        "restaurant", "food service", "kitchen", "dining", "qsr",
        "fast food", "cafe", "chain restaurant", "franchise"
    ],
    "Healthcare": [
        "hospital", "healthcare", "health system", "clinic", "patient",
        "senior living", "nursing home", "assisted living", "medical center"
    ],
    "Medical Technology": [
        "laboratory", "lab automation", "clinical lab", "diagnostics lab",
        "pharmacy", "hospital pharmacy", "surgical robot", "surgical suite",
        "patient care", "specimen processing", "pathology", "iv compounding",
        "medication dispensing", "robotic surgery", "da vinci", "telepresence"
    ],
    "Food Processing & Manufacturing": [
        "food processing", "food manufacturing", "meat processing",
        "bakery", "produce processing", "food packaging", "food safety",
        "food sorting", "food preparation", "cooking automation",
        "robotic chef", "robotic kitchen"
    ],
    "Datacenters": [
        "datacenter", "data center", "server", "hyperscale", "cloud infrastructure",
        "colocation", "server farm", "datacenter operations", "datacenter maintenance"
    ],
    "Airports & Aviation": [
        "airport", "terminal", "aviation", "baggage handling", "boarding gate",
        "airport operations", "airport security", "airport shuttle"
    ],
    "Retail": [
        "retail", "store", "shopping", "e-commerce", "grocery", "supermarket",
        "shelf scanning", "inventory robot", "click-and-collect", "micro-fulfillment",
        "retail fulfillment", "retail automation", "cashier", "checkout"
    ],
    "Apparel & Textiles": [
        "garment", "apparel", "clothing", "fashion", "textile",
        "sewing", "fabric cutting", "apparel factory", "apparel warehouse",
        "clothing distribution", "fashion logistics", "garment sorting"
    ],
    "Casinos & Gaming": [
        "casino", "gaming", "resort casino", "slot", "table games",
        "integrated resort", "tribal gaming"
    ],
    "Cruise Lines": [
        "cruise", "cruise line", "cruise ship", "vessel", "onboard"
    ],
    "Theme Parks & Entertainment": [
        "theme park", "amusement park", "roller coaster", "attractions",
        "entertainment venue", "water park"
    ],
    "Real Estate & Facilities": [
        "facilities management", "property management", "commercial real estate",
        "building services", "janitorial", "facility services"
    ],
    "Automotive Dealerships": [
        "dealership", "auto dealer", "car dealer", "automotive retail"
    ],
}

# ── Noise Filter (exclude generic terms, headline fragments, news orgs) ───────
NOISE_WORDS = {
    "the", "a", "an", "this", "that", "these", "those", "said", "says",
    "according to", "new york", "los angeles", "san francisco", "united states",
    "north america", "wall street", "main street", "industry", "company",
    "corporation", "inc", "llc", "ltd", "group", "international",
    # News publishers & headline fragments
    "u.s. news", "world report", "& world", "& report", "criticize ",
    "discusses", "what ", "how ", "trends", "know about", "pleas for",
    "leaves door", "receives approval", "in stages", "in funding",
    # Generic categories (not company names)
    "chicken restaurant chain", "fast food industry", "restaurant chain",
    "hotel group executive", "logistics park", "national park",
    # Headline verbs & fragments (March 2026 - reduce false positives)
    "alumni", "reportedly", "predicts", "nixes", "cancels", "kicks", "amid",
    "women", "retailers", "nurses", "market", "outlook", "progress", "smoothies",
    "police", "start-ups", "experts", "robots", "momentum",
    "wildfires", "neuropsychology", "psychology",
}


class IntelligenceNewsScraper:
    """
    Discovers new companies from news and enriches existing companies with signals.
    Acts as free alternative to expensive paid services.
    """
    
    GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    DELAY = 2.0  # Be polite to Google
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.stats = {
            "articles_processed": 0,
            "companies_discovered": 0,
            "companies_enriched": 0,
            "signals_created": 0,
            "queries_run": 0,
        }
    
    # ══════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ══════════════════════════════════════════════════════════════════════════
    
    def discover_leads(self, max_articles_per_query: int = 10) -> Dict:
        """
        Main discovery mode: search news for buying intent signals,
        extract company names, create new leads or enrich existing.
        
        Returns: stats dict with discoveries
        """
        logger.info("🎣 Starting lead discovery from news...")
        
        for query in DISCOVERY_QUERIES:
            self.stats["queries_run"] += 1
            logger.info(f"Query {self.stats['queries_run']}/{len(DISCOVERY_QUERIES)}: {query}")
            
            articles = self._fetch_google_news(query)
            for article in articles[:max_articles_per_query]:
                self._process_article(article, query)
            
            time.sleep(self.DELAY)
        
        self._print_stats()
        return self.stats
    
    def enrich_existing_companies(self, limit: int = 50) -> Dict:
        """
        Enrich companies already in DB by searching news for their names.
        Finds recent signals we may have missed.
        """
        logger.info("🔍 Enriching existing companies...")
        
        # Get companies with fewest signals (most stale)
        companies = (
            self.db.query(Company)
            .outerjoin(Signal)
            .group_by(Company.id)
            .order_by(func.count(Signal.id).asc())
            .limit(limit)
            .all()
        )
        
        for company in companies:
            logger.info(f"Enriching: {company.name}")
            self._enrich_company(company)
            time.sleep(self.DELAY)
        
        self._print_stats()
        return self.stats
    
    # ══════════════════════════════════════════════════════════════════════════
    # NEWS FETCHING
    # ══════════════════════════════════════════════════════════════════════════
    
    def _fetch_google_news(self, query: str) -> List[Dict]:
        """Fetch Google News RSS for query."""
        articles = []
        try:
            encoded = urllib.parse.quote(query)
            url = self.GOOGLE_NEWS_RSS.format(query=encoded)
            
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; ReadyForRobots/1.0)"
            })
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_data = resp.read()
            
            root = ET.fromstring(xml_data)
            channel = root.find("channel")
            if not channel:
                return []
            
            for item in channel.findall("item"):
                title = (item.findtext("title") or "").strip()
                desc = (item.findtext("description") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub = (item.findtext("pubDate") or "").strip()
                
                source_el = item.find("source")
                source = source_el.text.strip() if source_el is not None else ""
                
                articles.append({
                    "title": title,
                    "description": desc,
                    "text": f"{title}. {desc}",
                    "url": link,
                    "published": pub,
                    "source": source,
                    "query": query,
                })
        
        except Exception as e:
            logger.warning(f"News fetch failed for '{query}': {e}")
        
        return articles
    
    # ══════════════════════════════════════════════════════════════════════════
    # ARTICLE PROCESSING
    # ══════════════════════════════════════════════════════════════════════════
    
    def _process_article(self, article: Dict, query: str):
        """Extract company, classify signals, save to DB."""
        self.stats["articles_processed"] += 1
        
        # Extract company name(s) from article
        companies = self._extract_companies(article["text"])
        if not companies:
            return
        
        # Process each detected company
        for company_name, confidence in companies:
            # Get or create company
            company = self._get_or_create_company(company_name, article["text"])
            if not company:
                continue
            
            # Detect signal type(s)
            signal_types = self._detect_signal_types(article["text"])
            
            # Create signal for each type detected
            for signal_type in signal_types:
                self._create_signal(
                    company=company,
                    signal_type=signal_type,
                    text=article["text"][:600],
                    url=article["url"],
                    query=query
                )
    
    def _enrich_company(self, company: Company):
        """Search news for specific company and add new signals."""
        queries = [
            f"{company.name} automation investment",
            f"{company.name} expansion facility",
            f"{company.name} funding round",
            f"{company.name} labor shortage staffing",
        ]
        
        for query in queries:
            articles = self._fetch_google_news(query)
            for article in articles[:5]:  # Top 5 per query
                if company.name.lower() in article["text"].lower():
                    signal_types = self._detect_signal_types(article["text"])
                    for signal_type in signal_types:
                        self._create_signal(
                            company=company,
                            signal_type=signal_type,
                            text=article["text"][:600],
                            url=article["url"],
                            query=query
                        )
    
    # ══════════════════════════════════════════════════════════════════════════
    # ENTITY EXTRACTION
    # ══════════════════════════════════════════════════════════════════════════
    
    def _extract_companies(self, text: str) -> List[Tuple[str, float]]:
        """
        Extract company names from text using multiple patterns.
        Returns: [(company_name, confidence), ...]
        """
        companies = []
        seen = set()
        
        # Pattern 1: "Company X announces/invests/opens..."
        for match in COMPANY_PATTERN.finditer(text):
            name = match.group(1).strip()
            if self._is_valid_company_name(name) and name not in seen:
                companies.append((name, 0.9))
                seen.add(name)
        
        # Pattern 2: "at/for/with Company X"
        for match in COMPANY_CONTEXT.finditer(text):
            name = match.group(1).strip()
            if self._is_valid_company_name(name) and name not in seen:
                companies.append((name, 0.7))
                seen.add(name)
        
        # Filter by confidence (prioritize high confidence)
        companies.sort(key=lambda x: x[1], reverse=True)
        return companies[:5]  # Top 5 companies per article (tuned for 30-50 leads/run)
    
    def _is_valid_company_name(self, name: str) -> bool:
        """Filter out noise from extracted company names (headline fragments, etc.)."""
        name_lower = name.lower().strip()
        words = name_lower.split()
        
        # Too short or too long
        if len(name) < 5 or len(name) > 50:
            return False
        
        # Must contain at least one uppercase letter (proper noun)
        if not any(c.isupper() for c in name):
            return False
        
        # Starts with noise word
        if any(name_lower.startswith(word.strip()) for word in NOISE_WORDS):
            return False
        
        # Contains specific noise phrases (news orgs, headline fragments)
        noise_phrases = {"& world", "& report", "u.s. news", "world report",
                        "criticize", "discusses", " in funding", "receives approval",
                        "in stages", "leaves door", "chicken restaurant chain",
                        "fast food industry", "logistics park", "national park",
                        "market research", "market outlook", "market size",
                        "labor shortage", "predicts a profit", "can you", "now it",
                        "replacement route", "route 95", "route 9517",
                        "launches ai and robotic", "launches ai and robot",
                        "wildfires", "neuropsychology"}
        if any(phrase in name_lower for phrase in noise_phrases):
            return False
        
        # Is just a noise word
        if name_lower in NOISE_WORDS:
            return False
        
        # Truncated / sentence fragments: ends with " to", " -", " in", " for"
        if re.search(r'\s(to|-\s|in|for)$', name_lower):
            return False
        
        # News org pattern: "X & World", "X Report", "X - U.S."
        if re.search(r'& (world|report)$|\s-\s*(u\.?s\.?|the)\b', name_lower):
            return False
        
        # Contains verbs/prepositions/sentence fragments (whole-word match)
        sentence_words = {"to", "for", "in", "on", "at", "with", "from", "but",
                         "receives", "approval", "stages", "funding", "staffing",
                         "cuts", "leaves", "pleas", "trends", "know", "about",
                         "criticize", "discusses", "what", "how", "through",
                         "will", "nixes", "cancels", "kicks", "amid", "alumni",
                         "reportedly", "predicts", "some", "it"}
        if any(re.search(r'\b' + re.escape(w) + r'\b', " " + name_lower + " ") for w in sentence_words):
            return False
        
        # Headline structure: "Company verb" captured wrong → "X will", "X nixes", "X cancels"
        if re.search(r'\s(will|nixes|cancels|kicks\s|kicks off|predicts)\s*$', name_lower):
            return False
        
        # "New [number]" or "New [product descriptor]" (New 82, New surgical robot)
        if name_lower.startswith("new "):
            if len(words) >= 2 and (words[1].isdigit() or words[1] in {
                    "surgical", "robot", "82", "mir", "software"}):
                return False
        
        # Ends with " CEO", " robot" (product), " Market" (report title)
        if re.search(r'\s(ceo|robot|market|market research|market outlook)\s*$', name_lower):
            return False
        
        # Generic plural roles/categories as whole name
        if name_lower in {"retailers", "nurses", "women", "robots", "experts"}:
            return False
        
        # Starts with "Some " (Some cloud experts)
        if name_lower.startswith("some "):
            return False
        
        # Contains comma (sentence fragment: "Clover predicts a profit,")
        if "," in name:
            return False
        
        # "X and CTA" / "City and CTA" style headline fragments
        if " and " in name_lower and any(w in name_lower for w in ("cta", " and robot", " and robotic")):
            return False
        
        # Contains only common words
        if all(word in NOISE_WORDS for word in words):
            return False
        
        # Too many words (likely sentence)
        if len(words) > 5:
            return False
        
        # Starts with lowercase (likely mid-sentence)
        if name[0].islower():
            return False
        
        # Location pattern: "N.J. X", "State X"
        if re.match(r'^[a-z]{2}\.\s', name_lower) or name_lower.startswith("state "):
            return False
        
        return True
    
    # ══════════════════════════════════════════════════════════════════════════
    # SIGNAL DETECTION
    # ══════════════════════════════════════════════════════════════════════════
    
    def _detect_signal_types(self, text: str) -> List[str]:
        """Detect signal types using ontology (meaning/intent) + keyword patterns."""
        # Ontology: extracts semantic intent from robotics concepts
        signals = list(dict.fromkeys(classify_signals_with_fallback(text)))
        # Merge with SIGNAL_PATTERNS for full coverage
        text_lower = text.lower()
        for signal_type, keywords in SIGNAL_PATTERNS.items():
            if signal_type not in signals and any(kw in text_lower for kw in keywords):
                signals.append(signal_type)
        return signals if signals else ["news"]
    
    def _infer_industry(self, text: str) -> str:
        """Infer industry from article text."""
        text_lower = text.lower()
        
        # Score each industry
        scores = {}
        for industry, keywords in INDUSTRY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[industry] = score
        
        # Return highest scoring industry
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return "Unknown"
    
    # ══════════════════════════════════════════════════════════════════════════
    # DATABASE OPERATIONS
    # ══════════════════════════════════════════════════════════════════════════
    
    def _get_or_create_company(self, name: str, context_text: str = "") -> Optional[Company]:
        """Get existing company or create new one."""
        # Normalize name
        name = name.strip()
        
        # Check if exists (case-insensitive)
        existing = (
            self.db.query(Company)
            .filter(func.lower(Company.name) == name.lower())
            .first()
        )
        
        if existing:
            self.stats["companies_enriched"] += 1
            # Update industry if we have better info
            if existing.industry == "Unknown" and context_text:
                industry = self._infer_industry(context_text)
                if industry != "Unknown":
                    existing.industry = industry
                    self.db.commit()
            return existing
        
        # Create new company
        industry = self._infer_industry(context_text) if context_text else "Unknown"
        
        company = Company(
            name=name,
            industry=industry,
            source="news_discovery",
        )
        
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        
        self.stats["companies_discovered"] += 1
        logger.info(f"  ✨ NEW LEAD: {name} ({industry})")
        
        return company
    
    def _create_signal(
        self,
        company: Company,
        signal_type: str,
        text: str,
        url: str,
        query: str
    ):
        """Create a signal for a company (with deduplication)."""
        # Check for duplicate
        existing = (
            self.db.query(Signal)
            .filter(
                Signal.company_id == company.id,
                Signal.signal_text == text
            )
            .first()
        )
        
        if existing:
            return  # Skip duplicates
        
        # Score the signal using inference engine
        strength = self._score_signal(text, company.name, company.industry)
        
        # Skip weak signals (0.04 tuned for 30-50 leads/run; was 0.05)
        if strength < 0.04:
            return
        
        signal = Signal(
            company_id=company.id,
            signal_type=signal_type,
            signal_text=text,
            signal_strength=min(strength, 1.0),
            source_url=url or "",
        )
        
        self.db.add(signal)
        self.db.commit()
        
        self.stats["signals_created"] += 1
        logger.debug(f"  📡 {signal_type} signal: {company.name} (strength={strength:.2f})")
    
    def _score_signal(self, text: str, company_name: str, industry: str) -> float:
        """Score signal strength using inference engine."""
        try:
            combined = f"{company_name} {industry} {text}"
            result = analyze(combined, industry=industry or None)
            return round(result.overall_intent, 4)
        except Exception as e:
            logger.warning(f"Scoring failed: {e}")
            return 0.5  # Default moderate strength
    
    # ══════════════════════════════════════════════════════════════════════════
    # STATS & REPORTING
    # ══════════════════════════════════════════════════════════════════════════
    
    def _print_stats(self):
        """Print scraper statistics."""
        logger.info("\n" + "="*60)
        logger.info("🎣 INTELLIGENCE SCRAPER RESULTS")
        logger.info("="*60)
        logger.info(f"  Articles Processed:    {self.stats['articles_processed']}")
        logger.info(f"  Queries Run:           {self.stats['queries_run']}")
        logger.info(f"  🆕 Companies Discovered: {self.stats['companies_discovered']}")
        logger.info(f"  📈 Companies Enriched:   {self.stats['companies_enriched']}")
        logger.info(f"  📡 Signals Created:      {self.stats['signals_created']}")
        logger.info("="*60)
        
        if self.stats['companies_discovered'] > 0:
            logger.info("✨ FREE LEAD DISCOVERY SUCCESS!")
            logger.info(f"   Value: ${self.stats['companies_discovered'] * 100} saved")
            logger.info("   (vs. LinkedIn Sales Nav @ $99/month per lead)")
