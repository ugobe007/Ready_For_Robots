"""Job Board Scraper — Google News RSS=====================================Scrapes Google News RSS to detect labor-pain signals for robot-buying prospects.Indeed blocks direct RSS access; Google News freely indexes hiring/shortage news.Strategy:  - Extract the job/role keyword from the existing Indeed scrape_targets URLs  - Build Google News RSS queries like "warehouse hiring shortage 2026"  - Parse article titles/snippets for company names + labor signal language  - Signal types: labor_pain, labor_shortage, strategic_hireNo Playwright, no browser, no CAPTCHA risk — pure urllib + XML."""import htmlimport loggingimport reimport timeimport urllib.requestimport urllib.parseimport xml.etree.ElementTree as ETfrom typing import List, Optionalfrom sqlalchemy.orm import Sessionfrom app.database import SessionLocalfrom app.models.company import Companyfrom app.models.signal import Signallogger = logging.getLogger(__name__)DELAY = 2.5  # seconds between requestsGNEWS_RSS = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"# Queries keyed to labour-pain themes — sent directly to Google NewsLABOR_NEWS_QUERIES = [    # Logistics / warehouse    ("warehouse labor shortage hiring 2026",           "Logistics",    "labor_shortage"),    ("fulfillment center hiring workers shortage",     "Logistics",    "labor_shortage"),    ("distribution center hiring now workers needed",  "Logistics",    "labor_pain"),    ("supply chain workforce shortage 2026",           "Logistics",    "labor_shortage"),    # Hospitality    ("hotel housekeeping staff shortage hiring 2026",  "Hospitality",  "labor_shortage"),    ("hotel workers hiring shortage turnover",         "Hospitality",  "labor_shortage"),    ("resort hiring hospitality staff shortage",       "Hospitality",  "labor_pain"),    # Food Service    ("restaurant staff shortage hiring 2026",          "Food Service", "labor_shortage"),    ("food service workers shortage turnover",         "Food Service", "labor_shortage"),    ("kitchen workers hiring fast food shortage",      "Food Service", "labor_pain"),    # Healthcare    ("hospital workers shortage hiring 2026",          "Healthcare",   "labor_shortage"),    ("healthcare staffing shortage nursing aide",      "Healthcare",   "labor_shortage"),    # Operations buyer personas    ("VP operations logistics hired appointment",      "Logistics",    "strategic_hire"),    ("director of operations hospitality appointed",   "Hospitality",  "strategic_hire"),    ("VP supply chain appointed named",                "Logistics",    "strategic_hire"),]JUNK_RE = re.compile(    r"^(how to|tips for|best|top \d|what is|why |guide to|review:|opinion:|editorial|"    r"government|congress|senate|bill |law |policy |regulation|union |strike )",    re.I,)COMPANY_EXTRACTORS = [    re.compile(r"^(.+?)\s+(?:is hiring|hiring|seeks|adds|names|appoints|expands|opens|faces shortage)", re.I),    re.compile(r"^(.+?)\s+(?:staff|worker|employee|labor)\s+shortage", re.I),    re.compile(r"^(.+?)[,;]\s+(?:a|an|the)\s+\w+\s+(?:company|corp|inc|group|hotel|resort|warehouse)", re.I),]INDUSTRY_MAP = {    "Logistics":   ["warehouse", "fulfillment", "logistics", "supply chain", "distribution", "dock", "3pl"],    "Hospitality": ["hotel", "resort", "hospitality", "housekeeper", "valet", "lodging", "casino"],    "Food Service": ["restaurant", "cook", "kitchen", "food", "cafe", "dining", "qsr", "fast food"],    "Healthcare":  ["hospital", "health", "medical", "pharmacy", "nursing", "clinic"],}SIG_STRENGTH = {    "labor_shortage": 0.72,    "labor_pain":     0.55,    "strategic_hire": 0.80,}def _infer_industry(text: str, hint: str = "") -> str:    lower = (text + " " + hint).lower()    for industry, keywords in INDUSTRY_MAP.items():        if any(kw in lower for kw in keywords):            return industry    return "Unknown"
# Words that end a sentence fragment, not a company name
_SENTENCE_VERBS = re.compile(
    r'\b(face|faces|faced|fight|fights|fighting|is|are|was|were|has|have|had|'
    r'work|works|worked|say|says|said|warn|warns|warned|warn|ring|rings|lack|lacks|'
    r'struggle|struggles|suffer|suffers|report|reports|feel|feels)\b$',
    re.I,
)

def _extract_company(title: str) -> Optional[str]:
    """Try to pull a real company name from a news headline.

    Strict rules:
    - At most 5 words (long extractions are sentence fragments, not names)
    - Must contain at least one capitalized word (proper noun signal)
    - Must not end with a verb or connector word
    - Must pass the lead_filter junk check
    """
    from app.services.lead_filter import is_junk

    for pattern in COMPANY_EXTRACTORS:
        m = pattern.match(title)
        if not m:
            continue
        name = m.group(1).strip().strip('"\'')

        # Length sanity
        if not (3 < len(name) < 55):
            continue

        words = name.split()

        # No more than 5 words — real company names are short
        if len(words) > 5:
            continue

        # At least one word must start with an uppercase letter (proper noun)
        if not any(w[0].isupper() for w in words if w):
            continue

        # Must not end with a verb/sentence-connector
        if _SENTENCE_VERBS.search(name):
            continue

        # Reject trailing articles / determiners
        if re.search(r'\b(the|a|an|this|that|these|those|and|or|but|for)\b$', name, re.I):
            continue

        # Final junk check
        junk, _ = is_junk(name)
        if junk:
            continue

        return name

    return None
def _query_from_indeed_url(source_url: str) -> str:    """Extract q= from an Indeed /jobs URL and build a Google News query."""    try:        params = urllib.parse.parse_qs(urllib.parse.urlparse(source_url).query)        q = params.get("q", [""])[0].replace("+", " ")        if q:            return f"{q} hiring shortage 2026"    except Exception:        pass    return ""class JobBoardScraper:    """Uses Google News RSS to surface labor-pain signals for robot-buying prospects."""    def __init__(self, db: Session = None):        self.db = db or SessionLocal()        self._leads_added = 0    def run(self, urls: List[str]):        """Run all hardcoded labor-pain news queries (ignores the Indeed URL list)."""        for query, industry_hint, default_sig_type in LABOR_NEWS_QUERIES:            self._run_query(query, industry_hint, default_sig_type)            time.sleep(DELAY)        # Also try to derive extra queries from the scrape_targets Indeed URLs        seen_queries = {q for q, _, _ in LABOR_NEWS_QUERIES}        for url in urls:            q = _query_from_indeed_url(url)            if q and q not in seen_queries:                seen_queries.add(q)                self._run_query(q, "", "labor_pain")                time.sleep(DELAY)    def _run_query(self, query: str, industry_hint: str, default_sig_type: str):        rss_url = GNEWS_RSS.format(q=urllib.parse.quote(query))        try:            req = urllib.request.Request(                rss_url,                headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"},            )            with urllib.request.urlopen(req, timeout=12) as resp:                self._parse_rss(resp.read(), query, industry_hint, default_sig_type)        except Exception as e:            logger.warning("Google News RSS failed for %r: %s", query, e)    def _parse_rss(self, xml_bytes: bytes, query: str, industry_hint: str, default_sig_type: str):        try:            root = ET.fromstring(xml_bytes)        except ET.ParseError as e:            logger.warning("XML parse error: %s", e)            return        channel = root.find("channel")        if channel is None:            return        for item in channel.findall("item"):            raw_title = html.unescape(item.findtext("title", "") or "")            raw_desc  = html.unescape(item.findtext("description", "") or "")            link      = item.findtext("link", "") or ""            title = re.sub(r"\s*-\s*[^-]{3,50}$", "", raw_title).strip()  # strip "- Source Name"            full_text = f"{title} {raw_desc}".lower()            if JUNK_RE.match(title):                continue            company_name = _extract_company(title)            if not company_name:                continue            # Determine signal type from query context            if "strategic_hire" in default_sig_type or re.search(r"(VP|director|appointed|named)", full_text, re.I):                sig_type = "strategic_hire"                strength = 0.80            elif "shortage" in full_text or "turnover" in full_text:                sig_type = "labor_shortage"                strength = 0.72            else:
