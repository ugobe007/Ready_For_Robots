import re
from bs4 import BeautifulSoup
from app.scrapers.base_scraper import BaseScraper

# Operational roles posted in volume = labor pain = robot opportunity.
# We score by how many qualifying role keywords appear and how senior the posting is.
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

# Retention / wage pain language in job descriptions
PAIN_SIGNALS = [
    "competitive pay", "immediate hire", "hiring now", "urgent", "high turnover",
    "retention bonus", "sign-on bonus", "starting immediately",
    "multiple openings", "various shifts", "night shift", "weekend required",
    "staffing shortage", "hard to fill", "labor shortage",
]

# Buyer personas: operations decision-makers who approve robot purchases.
# VP/Director of Operations, Facilities, F&B, Housekeeping — NOT robotics engineers.
BUYER_PERSONA_PATTERNS = [
    re.compile(r"(VP|SVP|Director|Head|Chief).{0,30}(operations|facilities|logistics|supply chain)", re.I),
    re.compile(r"(VP|SVP|Director|Head).{0,30}(food.{0,10}beverage|F&B|restaurant|culinary)", re.I),
    re.compile(r"(VP|SVP|Director|Head).{0,30}(housekeeping|rooms|property)", re.I),
    re.compile(r"(VP|SVP|Director|Head).{0,30}(distribution|fulfillment|warehouse)", re.I),
    re.compile(r"Chief (Operating|Operations|Supply Chain|Facilities) Officer", re.I),
    re.compile(r"(General Manager|GM).{0,20}(hotel|resort|property|distribution)", re.I),
    re.compile(r"(Director|Manager).{0,20}(guest services|guest experience)", re.I),
]

MULTI_BRAND_HOTELS = ["marriott", "hilton", "hyatt", "ihg", "wyndham", "best western", "radisson"]

# Operational efficiency / digital transformation hires.
# These are managers and directors whose mandate IS to automate — NOT engineers
# who build robots. A "Director of Operational Excellence" is approving budgets;
# a "Robotics Engineer" is a builder we will never sell to.
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


class JobBoardScraper(BaseScraper):
    """Scrapes job boards for robot-buying intent signals.

    Strategy: we are NOT looking for companies that build robots.
    We look for companies that:
      1. Post high volumes of manual operational roles  → labor_pain signal
      2. Use retention/urgency language in postings    → labor_shortage signal
      3. Hire operations decision-makers               → strategic_hire (buyer persona)
    """

    def parse(self, html: str, url: str):
        soup = BeautifulSoup(html, "html.parser")

        postings = (
            soup.select("div.job_seen_beacon")      # Indeed
            or soup.select("div.base-card")          # LinkedIn
            or soup.select("article.jobsearch-result")
            or soup.select(".job-listing, .result, .posting")
        )

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