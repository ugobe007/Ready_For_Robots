"""
Lead Filter Service
===================
Two-stage pipeline applied to every lead before it surfaces in the API or dashboard:

  Stage 1 — JUNK FILTER: removes noise (scraped 404 pages, test artifacts, gibberish)
  Stage 2 — PRIORITY TIER: ranks clean leads as HOT / WARM / COLD

Usage
-----
  from app.services.lead_filter import classify_lead, is_junk, TIERS

  tier, reasons = classify_lead(company, score, signals)
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Any

from app.services.company_name_validation import reject_as_non_company_name
from app.services.known_brands import is_allowlisted_company_name
from app.services.news_publications import is_known_publication_name
from app.services.robot_vendor_names import is_known_robotics_vendor_name

# ─── Junk detection ───────────────────────────────────────────────────────────

# Substrings that always mean the record is scraper garbage (checked on lowercased name)
_JUNK_SUBSTRINGS = [
    # HTTP / browser errors
    "404", "not found", "page not found", "error", "access denied",
    "forbidden", "503 service", "502 bad gateway", "just a moment",
    "attention required", "cloudflare", "captcha", "enable javascript",
    "loading…", "loading...", "please wait", "robot check",
    # Placeholder / test records
    "test company", "test lead", "sample company", "demo company",
    "n/a", "unknown", "unnamed", "placeholder", "no name",
    "untitled", "company name", "your company",
    # Statistic / headline fragments — never a real company name
    "two-thirds", "three-quarters", "two thirds", "three quarters",
    "of hotels", "of companies", "of workers", "of employees",
    "of operators", "of businesses", "of respondents", "of travelers",
    "of guests", "of consumers", "of customers", "of managers",
    "of brands", "of chains", "of locations", "of properties",
    "of restaurants", "of warehouses", "of facilities",
    # Article / survey language
    "survey finds", "report finds", "study finds", "survey shows",
    "report shows", "data shows", "according to", "says report",
    "says study", "per report", "per survey",
    # SEC / financial filings scraped as company names
    "sec 10-k", "sec 10-q", "10-k filing", "10-q filing", "annual report sec",
    # Specific known-bad junk from user feedback
    "how ai ", "pro-level", "yegor traiman", "travel market", "tourism market", "ops 202", "how to ",
    # Article headline fragments reported by users
    "revenue drain", "hidden revenue", "industry could",
    "sport airline",
    # Do NOT add "sports retailer" alone — e.g. "Swedish sports retailer Stadium" is a real legal name.
    "ideas ahead",
    "supply chain drive",
    "gets high-tech", "gets high tech",
    "hn brief", "dropship",
    # News source names scraped as companies
    "business journals", "next web", "cap times", "the cap times",
    # Medical / research topic phrases (not company names)
    "hospital-acquired infections", "healthcare-associated infections",
    "infections prevention", "disease prevention technology",
    # Generic tech/supply chain descriptors
    "pallet labelling", "pallet labeling",
    "size share",  # market research fragment
    # Page chrome / syndication / research boilerplate (not legal entities)
    "read more", "click here", "subscribe to", "sign up for our", "cookie policy",
    "terms of use", "privacy policy", "getty images", "shutterstock", "photo credit",
    "image credit", "podcast episode", "webinar replay", "related articles", "see also",
    "continued on page", "full article", "pdf download",
    "pr newswire", "globe newswire", "business wire", "ein presswire", "accesswire",
    "press release", "earnings call", "conference call", "investor presentation",
    "research and markets", "researchandmarkets", "marketsandmarkets",
    "mordor intelligence", "fortune business insights", "coherent market insights",
    "experts say", "analysts say", "according to analysts",
    # News / research outlets and syndicated titles scraped as “company names”
    "business insider",
    "seeking alpha",
    "marketwatch",
    "barrons.com",
    "the motley fool",
    "grand view research",
    "verified market research",
    # Sector / market report fragments (not company names)
    " robot sector",
    " automation sector",
    " market forecast",
    " industry report",
    " research report",
    " weekly roundup",
    # Report / outlook titles mistaken for company names (RSS headlines)
    "global outlook",
    "market outlook",
    "sector outlook",
    "economic outlook",
    "weekly outlook",
    "cautiously optimistic",
    # EOL / packaging scrape artifacts — food politics, equipment types, market labels
    "caught covid", "meat plant workers", "covid outbreak",
    "declares meat", "meat supply critical",
    "senate democrats", "executive order",
    "market overview", "market report",
    "canned soup", "processed food", "fortified foods", "foods market",
    "vending machine", "filling machine", "sealing machine", "labeling machine",
    "wrapping machine", "packing machine", "capping machine",
    "workload automation tools", "automation tools",
    "top article", "creates new problems", "peels away",
    "should your packaging", "improving packaging line",
    "standout packaging", "package boiler", "drum filling",
    "showcases flexible", "weighing conveying",
    "global beer", "major food",
    "news us", "cornhusker clink", "spartanburg distribution",
    # Celebrity / entertainment headlines
    "celebrates rock", "gene simmons", "celebrates", "rock and roll",
    # Generic equipment / product categories (not companies)
    "testing equipment", "waterjet", "intensifier pump", "world cement",
    "world waterjet", "mezzanines", "reverse logistic",
    # Job listing / career headline fragments
    "highest paying", "paying tech jobs", "paying artificial intelligence",
    "paying jobs", "top paying",
    # Conference / event / show fragments
    "conference agenda", "full agenda", "smrsc", "empack",
    "packaging innovations", "packaging news",
    # Generic single words / non-company stubs
    "investment",
    # Headline / slide fragments (arrow bullets, FYI asides) scraped as company.name
    "-->",
    "fyi-->",
    "essential benefits",
    # Headline verb fragments
    "war just picked", "retail war",
    # Generic financial / corporate jargon scraped as names
    "million series", "nano one highlights",
    # Airport codes standing alone (3-letter IATA codes)
    # "MassRobotics startups", "AI startups" — list article fragments (not companies)
    "startups",
    # "Central Fill Pharmacy Automation" / "Intelligent Pharmacy Leveraging AI" — product descriptors
    "fill pharmacy", "pharmacy automation", "leveraging ai",
    # "Delta's Power Cooling" / possessive fragment patterns
    # (handled by regex below — kept here as belt+suspenders)
    # "Report UK Hospitality" — starts with "Report"
    # handled by regex below
    # "Expanding Healthcare Access" — should be caught by Rising/Exploring pattern
    # but adding as substring for safety
    "healthcare access",
    # "JAMES BEARD FOUNDATION RELEASES" — foundation + all-caps verb
    # NOTE: "can ai" removed from substrings — it's a substring of "American Airlines"
    # It lives in _JUNK_EXACT (exact match only)
    # "We want" / "Percent Solution" / "BE-A" — too generic or too short
    # handled by regex patterns below
    # "Xpanner Officially" — company + adverb (truncated headline)
    " officially",
    # "New Eastern Hub" / "Battery Lifters" etc. handled above
    # Log-confirmed specific junk names
    "report uk hospitality",
    # Intelligence scraper — headline / listicle fragments stored as company.name
    "unlock the roi",
    "chaos to consistency",
    "supply chain automation leaders",
    "hub in industry first",
    "ranked by",
    "demonstrates industry",
    "workflow orchestration",
    "strategic collaboration",
    "market size,",
    "robotics market size",
    "what bubble",
    "-- designed",
    # PR / news headline: "[Brand] Strengthens …" (not a legal entity name)
    "strengthens position",
    "strengthens presence",
    "strengthens leadership",
    # Listicle / deck fragments mistaken for company names
    "share insights",
    "ebrd grants",
    "technology banking coverage",
    # Magazine / SEO headline stubs (not legal entities)
    "power couple",
    "future proofing",
    # Stock/ETF/financial listicle fragments
    " etfs", " reits", " stocks to", " stock to",
    "swot analysis",
    # Product review listicles
    "we've tested", "we tested",
    "air fryers", "coffee makers", "dishwashers", "waffle makers",
    "pool vacuums", "cpap machines", "password managers", "grab bars",
    "toaster ovens", "meat thermometer", "sprinkler timers", "clothing irons",
    # Consumer guide catch-all (belt+suspenders for "Best" regex above)
    "best robot lawn mow", "best robot mop", "best robot vacuum",
    # Labor/union events
    "strike starts", "authorize strike",
    # Generic geographic + topic fragments
    "tourism poised", "minimum wage",
    # Breakthrough/technology descriptor fragments (not proper names)
    "breakthrough self driving", "bulk material handling system",
    "blowroom lines", "breaker panels", "bus duct inspection",
    "chilled water storage",
    # Financial/market fragments
    "bull of", "capital budget", "chat control",
    "cell therapy testing", "cloud computing",
    # Incomplete possessive country
    "china's", "india's",
    # User-reported: merged vendor line / geography-industry stub / CMS noise
    "lagertechnik and locus",
    "bangladesh rmg",
    "ydr==",
    " - ydr",
    # Market report fragments that look like companies in RSS extraction
    "machine market",
    "equipment market",
    "systems market",
    "system market",
]

# Regex patterns on the raw (original-case) name
_JUNK_PATTERNS = [
    r"^\s*$",                                          # blank / whitespace only
    r"^[\W\d_]+$",                                     # no letters at all
    r"^.{1,2}$",                                       # too short (1-2 chars)
    r"^(inc|llc|corp|ltd|co|company|the)\.?\s*$",     # generic legal suffix or article alone
    r"https?://",                                      # accidentally captured a URL
    r"<[^>]+>",                                        # HTML tags leaked in
    r"^\d+$",                                          # all digits
    r"[^\x00-\x7F]{3,}",                              # encoding garbage

    # ── Headline / article fragment patterns ──────────────────────────────────
    # Starts with a quantifier or statistical phrase (never a company name)
    r"^(nearly|almost|about|roughly|approximately|upwards?\s+of|over|more\s+than|"
    r"less\s+than|most|many|several|some|a\s+few|majority\s+of|"
    r"a\s+majority|a\s+third|a\s+quarter|a\s+half|half\s+of)\s+",

    # Questions / Article headings
    r"^(how|why|what|when|where|who)\s+(can|is|are|will|do|does|to|we|they|you)\b",

    # Starts with a number + unit/fraction combo
    r"^\d+\s*(percent|%|in\s+\d+|of\s+\d+|tips|ways|reasons|steps|things|facts)\b",

    # "Best X" — product reviews, stock/ETF listicles, consumer guides (never a company name)
    # Catches: "Best Spatulas", "Best AI Stocks", "Best Robot Vacuums We've Tested", etc.
    r"(?i)^best\s+.{2,}",

    # "Top X" / "Worst X" superlative listicles
    r"^(top|worst|biggest|largest|smallest|leading|growing|rising|"
    r"fastest|slowest|latest|recent|upcoming)\s+\d*\s*(hotel|restaurant|"
    r"chain|brand|company|operator|brand|employer|employer)\b",

    # Generic single-word industry terms (not proper nouns)
    r"^(trending|industry|the\s+industry|market|the\s+market|sector|the\s+sector|"
    r"report|the\s+report|study|the\s+study|survey|the\s+survey|"
    r"statistics|insights|analysis|the\s+analysis|update|the\s+update|"
    r"news|breaking|alert|exclusive|source|weekly|monthly|daily|annual|quarterly)\s*$",

    # "Rising X" / "Exploring X" / "Declining X" — trend/article titles
    r"(?i)^(rising|exploring|declining|growing|falling|surging|shrinking|emerging)\s+\w+(\s+\w+)*$",

    # "X Is Up/Down/Back/Next" — stock/market headline fragments
    r"(?i)\s+(is|are|was|were)\s+(up|down|back|next|out|in|gone|here|there|live|set|due|key|new)\s*$",

    # "Video X" / "Photo X" / "Audio X" — media file descriptors
    r"(?i)^(video|photo|audio|image|gallery|podcast|webinar|whitepaper|infographic)\s+\w",

    # Labor/union headlines: "X Teamsters Authorize Strike", "Workers Strike At X"
    r"(?i)\b(teamsters|authorize\s+strike|workers?\s+strike|union\s+vote|labor\s+action)\b",

    # "X Day Y" — event/holiday fragments (Moving Day March, Opening Day Spring…)
    r"(?i)^(\w+)\s+day\s+(\w+)\s*$",

    # "Big Tax", "Big Labor", "Big Tech", "Big Pharma" — political/editorial shorthand
    r"(?i)^big\s+(tax|labor|tech|pharma|food|ag|oil|data|bank|biz|gov|media|auto)\s*$",

    # "X Policy", "X Act", "X Law", "X Bill" — legislation, not companies
    r"(?i)^[\w\s]{3,40}\s+(policy|act|law|bill|legislation|regulation|rule|reform)\s*$",

    # "US-based X", "UK-based X" — geographic descriptor prefix, not a company name
    r"(?i)^(us|uk|china|japan|europe|germany|france|india|canada|australia)-based\s+",

    # "X distribution center" (no proper name), "X warehouse", "X hub" as full name
    r"(?i)^(new|north|south|east|west|central|regional|national|global)\s+"
    r"(distribution\s+center|fulfillment\s+center|warehouse|hub|facility|campus|complex)\s*$",

    # "$X billion expansion", "$X million warehouse" — financial fragment, not company
    r"(?i)^\$?\d[\d,.]*\s*(million|billion|m\b|b\b)\s+\w",
    r"(?i)^(billion|million|trillion)\s+\w",

    # (ISIN identifier check moved to is_junk() to stay case-sensitive)

    # "Reach US", "Reach USD", "Reach EUR" — currency/market fragments
    r"(?i)^reach\s+(us|usd|eur|gbp|cad|aud|jpy)\s*$",

    # "Report X" / "Report on X" — news summary title, not a company
    r"(?i)^report\s+(uk|us|on|from|for|about|into|of)\s+\w",
    r"(?i)^(annual|quarterly|monthly|weekly|special|full)\s+report\b",

    # "Lineage Continues North American Warehouse" — company name + action verb + location
    # Catches "[Company] continues/expands/opens/launches [Geographic] [Noun]"
    r"(?i)^(\w+\s+){1,2}(continues?|expands?|opens?|builds?|launches?|adds?|grows?)\s+"
    r"(north|south|east|west|central|global|national|regional|american|european)\b",

    # All-caps foundation / org + action verb: "JAMES BEARD FOUNDATION RELEASES"
    r"^[A-Z\s]{5,}\s+(RELEASES|DELIVERS|ANNOUNCES|LAUNCHES|NAMES|HIRES|OPENS|FILES)\s*$",

    # "Percent Solution" / "Billion X" / "Million X" — numerical fragment
    r"(?i)^percent\s+\w",
    r"(?i)^(a\s+)?few\s+(hundred|thousand|million|billion)\b",

    # "BE-A" / short hyphenated non-names (1-2 chars per segment)
    r"^[A-Z]{1,2}-[A-Z]{1,2}$",

    # Possessive + generic noun: "Delta's Power Cooling", "Walmart's New Hub"
    r"(?i)^\w+'s\s+(power|new|old|key|core|main|prime|central|global|major|first|second)\s+\w",

    # "X Officially" — company + adverb (incomplete headline)
    r"(?i)\s+(officially|reportedly|allegedly|finally|recently|actually|currently)\s*$",

    # "We X", "Can X" — first person / question fragment
    r"(?i)^(we|can|should|could|would|may|might|do|did|does|is|are|was|were)\s+\w",

    # "U.S" / "U.K" alone — country abbreviation, not a company
    r"^U\.(S|K|A)\.?$",

    # Generic equipment categories — allow optional middle adjective e.g. "Industrial Robotic Motors"
    r"(?i)^(battery|pallet|material|conveyor|fork|lift|stacker|sorter|nut|grain|seed|"
    r"scanner|sensor|picker|placer|gripper|actuator|industrial|robotic|motor|drive)\s+"
    r"(\w+\s+)?"
    r"(lifters?|trucks?|handling|equipment|systems?|vehicles?|loaders?|robots?|motors?|drives?|"
    r"processing\s+machines?|processing\s+equipment)\s*$",

    # "Nut Processing Machine", "Industrial Robotic Motors" — equipment type stubs
    r"(?i)^(nut|grain|seed|fruit|vegetable|meat|fish|poultry)\s+processing\s+(machines?|systems?|lines?|equipment)\s*$",
    r"(?i)^(industrial|robotic|servo|stepper|linear)\s+(\w+\s+)?(motors?|drives?|actuators?|arms?|grippers?)\s*$",

    # "New Eastern Hub", "New Central Facility" — "New" + geographic modifier + generic noun
    r"(?i)^new\s+(eastern|western|northern|southern|central|global|regional|national|"
    r"american|european|asian|pacific|atlantic)\s+(hub|facility|center|campus|office|warehouse|dc)\s*$",

    # Standalone policy/political topics
    r"(?i)^(immigration|trade|tariff|wage|minimum wage|carbon|climate)\s+"
    r"(policy|act|law|bill|reform|regulation|tax|credit)\s*$",

    # "Health Systems", "Hospital Systems" — generic category (not a named company)
    r"(?i)^(health|hospital|medical|care|pharmacy|clinical)\s+(systems?|networks?|services?|centers?|group)\s*$",

    # "Global Real Estate", "Global Logistics" — pure generic+category (no proper noun)
    r"(?i)^(global|national|regional|local|american|european|asian)\s+"
    r"(real estate|logistics|supply chain|automation|manufacturing|technology|innovation)\s*$",

    # "CPHI Frankfurt 2025", "ProPak Asia 2026" — conference acronym + city + year
    r"(?i)^[A-Za-z]{2,10}\s+(frankfurt|amsterdam|chicago|houston|las vegas|"
    r"london|paris|munich|dubai|singapore|toronto|barcelona|jakarta|atlanta|"
    r"asia|europe|americas?|latin|global)\s+20\d\d\s*$",

    # "Ongoing Automation", "Advanced Manufacturing" — adjective + generic industry noun (no proper noun)
    r"(?i)^(ongoing|advanced|smart|digital|modern|integrated|automated|autonomous|"
    r"next-gen|next gen|connected|emerging|evolving|traditional|conventional)\s+"
    r"(automation|manufacturing|logistics|production|processing|packaging|operations?|"
    r"technology|innovation|transformation|distribution)\s*$",

    # Generic category without a proper name: "Dairy Producer", "Food Manufacturer", "Packaging Plant"
    r"(?i)^(dairy|meat|poultry|seafood|snack|beverage|cereal|candy|confection|bakery|"
    r"frozen food|canned food|packaged food|processed food)\s+"
    r"(producer|manufacturer|processor|plant|facility|operation|company|supplier|brand)\s*$",

    # "Voting is" / "X is" — incomplete headline fragment (verb 'is' or 'are' as last word)
    r"(?i)\s+(is|are|was|were)\s*$",

    # "Eight Integrated Shows", "Seven Key Trends" — spelled number + words (article title)
    r"(?i)^(eight|nine|eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
    r"seventeen|eighteen|nineteen|twenty)\s+\w",

    # Generic two/three word "category" stubs — no proper noun:
    # "Food Safety", "Goat Equipment", "Eagle Product Inspection Highlights Pack"
    r"(?i)^(food|product|worker|plant|labor|supply|chain|market|industry|public|"
    r"consumer|workplace|global|national|regional)\s+"
    r"(safety|inspection|compliance|standards?|quality|testing?|equipment|regulation|"
    r"guidelines?|requirements?|alert|warning|recall)\s*$",

    # "X Inspection Highlights Y" / "X Inspections Rolled Out" — food safety headline
    r"(?i)\b(inspections?\s+(rolled|launched|expanded|highlighted|highlights))\b",

    # "Eagle Product Inspection Highlights Pack" type — product + inspection + action word
    r"(?i)\b(inspection|inspections)\s+(highlights?|packs?|report|results?|findings?)\b",

    # Standalone Co-op / Cooperative without a proper name qualifier
    r"^(the\s+)?co-?ops?\s*$",

    # "X SWOT Analysis" — company + analyst-framework descriptor (not a company name)
    r"(?i)\bSWOT\s+Analysis\b",

    # "X-based company/firm/startup" — geographic descriptor, not a proper company name
    r"(?i)\b\w+-based\s+(company|firm|startup|business|group|operation|manufacturer|provider)\s*$",

    # "X Sweetens Up Spring", "X Rolls Out", "X Levels Up" — company + marketing verb phrase
    # (Brand name mistakenly re-extracted from headline containing action verbs)
    r"(?i)\s+(sweetens|rolls\s+out|levels\s+up|gears\s+up|kicks\s+off|teams\s+up|"
    r"doubles\s+down|steps\s+up|beefs\s+up|ramps\s+up|inks\s+deal)\b",

    # "BIM-Driven X", "AI-Powered X", "Tech-Enabled X" — technology adjective + topic (not a company)
    r"(?i)^(bim|ai|iot|ar|vr|ml|erp|crm|rpa|saas|paas|api|edi)-"
    r"(driven|powered|enabled|based|led|first|native|ready|focused)\s+\w",

    # "[City/State] Local", "[City] Pushing", "[City/State] Minimum Wage" — geographic + generic topic
    r"(?i)^(california|chicago|texas|new\s+york|florida|ohio|georgia|michigan|"
    r"virginia|washington|colorado|illinois|arizona)\s+"
    r"(local|minimum\s+wage|pushing|tourism|natural|farming|jobs|firms?|companies)\b",

    # "Birmingham", "Chicago" alone — city names with no company qualifier
    r"(?i)^(birmingham|chicago|atlanta|dallas|houston|phoenix|seattle|denver|"
    r"boston|miami|detroit|portland|minneapolis|cleveland|pittsburgh|"
    r"memphis|nashville|baltimore|sacramento|kansas\s+city)\s*$",

    # "Black Friday", "Cyber Monday" — retail events, not companies
    r"(?i)^(black\s+friday|cyber\s+monday|prime\s+day|singles\s+day)\b",

    # "Cheap Summer Why Rising Costs", "Buying Online" — consumer advice fragments
    r"(?i)^(cheap|buying|selling|shopping|saving|spending|getting|making|finding|avoiding)\s+\w",

    # "China's", "India's" — possessive country name fragments (lowercase-first only).
    # Case-sensitive: uppercase-first possessives like "Wendy's" / "McDonald's" are
    # real company names and must NOT be caught here.
    r"^[a-z][a-z]+\'s\s*$",

    # "Beyond Tesla" — "Beyond X" stock/market analysis fragments
    r"(?i)^beyond\s+(tesla|apple|amazon|google|meta|nvidia|microsoft|walmart|amazon)\b",

    # "X rival", "X competitor" — comparative editorial fragment, not a company name
    r"(?i)\s+(rival|rivals|competitor|competitors|contender|contenders)\s*$",

    # "Beloved X chain", "Fast-growing X chain" — adjective + category + "chain"
    r"(?i)^(beloved|popular|iconic|famous|struggling|growing|fast-growing|booming|thriving)\s+\w+(\s+\w+)?\s+chain\b",

    # "Leaked X" — rumor/leak article title
    r"(?i)^leaked\s+\w",

    # "Every Budget and X" — consumer advice fragment
    r"(?i)^every\s+budget\b",

    # "X looks", "X needs most" — incomplete headline fragments
    r"(?i)\s+(looks|looks\s+to|needs\s+most|still\s+leads?|keeps?\s+going)\s*$",

    # "NC prisons", "State prisons" — government/facility category without a proper name
    r"(?i)^(nc|ny|ca|tx|fl|il|pa|oh|ga|mi|nj|wa|az|ma|tn|in|md|mn|co|wi|mo|al|sc|la|ky)\s+(prisons?|jails?|courts?|schools?|dept|department)\b",

    # "Healey-Driscoll Administration", "Biden Administration" — government, not a company
    r"(?i)\badministration\s*$",

    # "Elderly Americans", "Five senior" — demographic fragments
    r"(?i)^(elderly|aging|senior|young|older|younger)\s+(american|european|worker|adult|consumer|citizen|people|patient)\b",
    r"(?i)^(five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty)\s+(senior|major|key|leading|top|big|small|mid)\b",

    # "Gen Z", "Gen X", "Baby Boomer" — demographic group terms
    r"(?i)^gen\s+[xyz]\b",
    r"(?i)^baby\s+boomer\b",

    # "Electric Cars", "Flying Cars", "Self-Driving Cars" — vehicle category, not company
    r"(?i)^(electric|autonomous|self-driving|flying|driverless|hydrogen|hybrid)\s+(cars?|trucks?|vehicles?|buses?)\s*$",

    # "Hyundai labor union", "X labor union", "X workers union" — labor org fragment
    r"(?i)\b(labor\s+union|workers?\s+union|trade\s+union|union\s+workers?)\s*$",

    # "Bigger 2026 Capex", "Q3 2026 Revenue" — financial metric fragment
    r"(?i)^(bigger|higher|lower|rising|falling|record)\s+20\d\d\s+\w",
    r"(?i)^(q[1-4]|h[12])\s+20\d\d\s+\w",

    # "Islanders need most", "Islanders rally" — sports team + verb phrase (not a company)
    r"(?i)\b(islanders?|patriots?|eagles?|cowboys?|steelers?|lakers?|celtics?|warriors?|yankees?)\s+\w+\s*$",

    # "REVIEW You Won", "PREVIEW X" — content type marker at start
    r"(?i)^(review|preview|recap|roundup|analysis|commentary|opinion|column)\s+\w",

    # "Top Robotics Stocks Worth Investing" — stock investment titles with "Worth" or "Investing"
    r"(?i)\b(worth\s+investing|worth\s+buying|to\s+buy\s+now|to\s+watch\s+in\s+20\d\d)\s*$",

    # "DOT secretary", "Labor secretary", "Treasury secretary" — government role titles
    r"(?i)^(dot|fda|faa|cdc|epa|dol|hhs|doj|sec|fed|usda|osha)\s+(secretary|commissioner|director|chair|chief|head|official)\b",
    r"(?i)^(labor|treasury|commerce|energy|transportation|agriculture|interior|defense)\s+secretary\b",

    # "No-Brainer Robotics Stocks", "X-Brainer X" — financial editorial fragments
    r"(?i)^no-brainer\s+\w",

    # "X Advancing", "X Emerging", "X Expanding" — company/topic + action word (truncated headline)
    # Only if no proper noun qualifier before the action word
    r"(?i)^([A-Z]\w+)\s+(advancing|emerging|expanding|evolving|accelerating|transforming|disrupting|navigating)\s*$",

    # Buyer-opportunity gate support: event/category/publication strings that
    # were passing as title-case company names and inflating HOT.
    r"(?i)^sponsor\s+\w",
    r"(?i)^first\s+fully\s+autonomous\b",
    r"(?i)^(chinese|american|us|u\.s\.|japanese|korean|german|dutch|swedish|"
    r"french|british|canadian|australian)\s+(humanoids?|robots?|androids?)\s*$",
    r"(?i)^(dutch|american|us|u\.s\.|japanese|korean|german|swedish|french|"
    r"british|canadian|australian)\s+(hospitality|hotel|restaurant|logistics|"
    r"healthcare)\s+operating\s+system\s+\w+",
    r"(?i)^(california|texas|florida|new\s+york|nj|ny|ca|tx|fl)\s+health\s+"
    r"workers?\s+helps?\s+patients?\b",
    r"(?i)\s+-\s+hotel\s+technology\s+news\s*$",
    r"(?i)^(qsr|nj|ny|ca|tx|fl|us|u\.s\.)\s+(operators?|restaurants?|hotels?|retailers?)\s*$",
    r"(?i)^(supply\s+chain|hospitality|logistics|restaurant|hotel)\s+consultanc(?:y|ies)\s+[A-Z]",

    # "Cold Storage" alone, "Computer Vision" alone — generic tech/logistics category
    # (real companies have a proper name like "Lineage Cold Storage")
    r"(?i)^cold\s+storage\s*$",
    r"(?i)^computer\s+vision\s*$",

    # Names that are clearly job titles scraped as company names
    r"^(vp|vice\s+president|ceo|coo|cfo|cto|chief|president|director|manager|"
    r"head|svp|evp)\s+(of\s+)?\w+",

    # Numbered-list items scraped from "Top N" articles (e.g. "24.Joanna Vargas …")
    r"^\d+\.\s*\S",

    # Looks like a sentence: 10+ words → almost certainly a headline/sentence
    r"^(\S+\s+){9,}\S+$",

    # Starts with "Former/Ex/Outgoing" — scraped person descriptions, not companies
    # "new" only fires when followed by a digit or lowercase word (avoids "New Paltz", "New York", etc.)
    r"^(former|ex-?|outgoing|incoming|current)\s+\w",
    r"^new\s+(\d|\d+\s|\b(humanoid|robot|ai|model|version|feature|update|release|tool|product|"
    r"system|platform|software|hardware|solution|service|app|device|sensor|chip|module)\b)",

    # Trailing news-source attribution: "Hospital - FOX 13 Tampa Bay", "Casino - CDC Gaming"
    r"\s[-–—]\s*(fox|abc|cbs|nbc|cnn|bbc|msnbc|sky\s+news|bloomberg|reuters|ap\s+news|"
    r"cdc\s+gaming|skyhighnews|skyhinews)\b",

    # Calendar date embedded in a company name → event/article, not company
    r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}\b",

    # 5-9 word news headlines: subject + action verb (allow symbols like & in subject)
    r"^(?:\S+\s+){1,7}(?:unveil|reinforc|knock|launch|announc|reveal|acquir|hire|"
    r"expand|clos|shut|file|say|grow|rise|fall|win|lose|"
    r"drop|spike|surge|plunge|soar|slip|shed|boost|spur|gain|add|nam|serv|deliver|"
    r"cut|slash|trim|offer|earn|post|report|sign|open|celebrat|appoint|"
    r"anticipat|forecat|project|predict|expect|extend|continu|achiev|complet|"
    r"integrat|transform|accelerat|moderniz|optim|digitiz|"
    r"strengthen|sell|sold|partner(?!s)|pivot|rebrand|restructur|consolidat|divest|"
    r"rev|heat|ramp|gear|kick|speed|power|pick|wind|dial|step|scale|"
    r"secur|rais|clos|land|obtain|bagg|nail|snag|pull|haul|"
    r"turn|shift|pivot|reshape|redefin|reinvent|overhaul|navigat|tackle|"
    r"address|combat|fight|face|brac|struggl|grappl)\w*\b",

    # Phrasal verb at end: "Revs Up", "Heats Up", "Ramps Up", "Kicks In" etc.
    r"(?i)\s+(revs?|heats?|ramps?|gears?|picks?|winds?|steps?|scales?|powers?|dials?)\s+(up|in|off|out|down)\s*$",

    # "Here Are / There Are" list headlines: "Here Are Five Global Restaurants"
    r"(?i)^(here\s+(are|is|'s)|there\s+(are|is|'s))\s+",

    # "The Future of X" / "State of X" / "Rise of X" — article title pattern
    r"(?i)^(the\s+)?(future|state|rise|fall|history|evolution|dawn|end|era|age)\s+of\s+\w",

    # Generic "[Topic] Technology" / "[Topic] Solutions" / "[Topic] Management" (no proper noun)
    r"(?i)^(supply\s+chain|value\s+chain|cold\s+chain|food\s+supply|demand\s+chain)\s+"
    r"(technology|management|solutions?|software|analytics|visibility|optimization|platform)\s*$",

    # "X Technology" / "X Solutions" where X is a generic industry phrase (2-3 words)
    r"(?i)^(warehouse|logistics|fulfillment|distribution|manufacturing|packaging|"
    r"retail|hospitality|healthcare|food\s+safety|food\s+service|restaurant|"
    r"automation|robotics)\s+(technology|technologies|solutions?|management|"
    r"services?|systems?|analytics|platform|software|trends?)\s*$",

    # "Warehouse Technology Trends" / "Logistics Solutions Insights" — 3-word topic stubs
    r"(?i)^(warehouse|logistics|supply\s+chain|manufacturing|automation|packaging|"
    r"distribution|fulfillment|hospitality|retail|food\s+service)\s+\w+\s+"
    r"(trends?|insights?|outlook|roundup|update|report|analysis|review)\s*$",

    # "The" + generic category word (no proper noun)
    r"^the\s+(hotel|hotels|restaurant|restaurants|chain|chains|brand|brands|"
    r"company|companies|operator|operators|warehouse|warehouses|industry|"
    r"market|sector|report|study|survey|data|analysis)\s*$",

    # Possessive headlines: "Hotels' challenge", "Workers' concerns"
    r"^[a-z].*'s?\s+(challenge|problem|concern|issue|struggle|need|demand|"
    r"opportunity|trend|future|rise|growth|decline|shift|impact|role)\b",

    # "Global Outlook", "Retail Outlook" — research report titles, not operating companies
    r"(?i)^(global|regional|weekly|monthly|annual|retail|national|economic|industry)\s+outlook\.?$",

    # ── Market research / sector labels (scraped as company names) ─────────────
    r"(?i)\bsector\s*$",
    r"(?i)\bforecast\s*$",
    r"(?i)\breport\s*$",
    r"(?i)\boutlook\s*$",
    r"(?i)(market|industry|transformation)\s+(forecast|outlook)\s*$",
    r"(?i)\s+robot\s+sector\s*$",
    r"(?i)^(the\s+)?(associated\s+press|reuters|bloomberg\s+news|cnbc|fox\s+business|marketwatch)\s*$",

    # Supply chain / logistics section headers (exact-ish; allows trailing corporate buzzwords)
    r"(?i)^(the\s+)?(global\s+)?supply[\s-]chain(\s+(management|network|solutions|strategy|operations|visibility|optimization|digitalization|digitalisation))?\s*$",
    r"(?i)^(the\s+)?(global\s+)?value\s+chain(\s+(management|optimization|optimisation))?\s*$",

    # Generic warehouse / WMS topic titles scraped as “company” (see SEO listicles: “… Top 10”)
    r"(?i)^(warehouse|inventory|order)\s+management\s+top\s*$",
    r"(?i)^warehouse\s+automation\s*$",
    r"(?i)^(smart\s+)?warehouse\s+(robotics|systems?|solutions?|technology)\s*$",

    # Colon + "The 20NN Guide" / handbook titles (listicles, not legal names)
    r"(?i):\s*the\s+20\d\d\s+guide\s*$",

    # Article titles: "Why Automation Is…", "How Hotels Can…", "Why AI Companies May…"
    # Catches question-word headlines even when the modal verb appears later
    r"(?i)^(why|how|what)\s+\S+(\s+\S+)?\s+(is|are|was|were|will|would|should|can|could|may|might|must)\b",
    # Short "Why UC workers" / "Why AI Companies" — question word + 1-2-letter abbreviation
    # Only triggers on 1-2 char uppercase abbreviations to avoid "Why Not Coffee Co" false positives
    r"(?i)^(why|how|what)\s+[A-Z]{1,2}\s+\w",
    # Listicle openers: "Five Success Factors for…", "3 Tips for…"
    r"(?i)^(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+"
    r"(success\s+)?(factors|tips|ways|reasons|steps|things|secrets|rules|mistakes)\b",
    # Regional + generic facility (headline / section, not "Acme Warehousing LLC")
    r"(?i)^(east|west|north|south)\s+coast\s+warehouse\b",
    # News headline: sector + "Implements" + robots/workers (not a legal entity name)
    r"(?i)\b(restaurant|hotel|warehouse|hospital|casino|factory|plant|retail)\s+implements\s+",

    # Email / attribution / ticker lines leaked into the name field
    r"@",
    r"(?i)^\s*(source|photo|image|credit|filed under)\s*:",
    r"(?i)\b(nasdaq|nyse|otc)\s*:\s*[A-Za-z]{1,6}\b",

    # Stock / analyst headline templates
    r"(?i)\b(stock\s+)?(rises|falls|gains|drops|soars|plunges)\s+\d+\s*%",
    r"(?i)\bbeats\s+(q[1-4]|first|second|third|fourth)\s+quarter\b",

    # Names ending with a bare period that are NOT known corporate abbreviations.
    # Matches "Acme Logistics." but NOT "Acme Inc." / "Acme Ltd." / "Acme Co." / "Acme Corp."
    r"(?i)^(?!.*\b(inc|ltd|co|corp|llc|plc|llp|lp|gmbh|bv|nv|ag|sa|srl)\b\s*\.?\s*$)"
    r".+[a-z]\.$",

    # "… for Restaurants", "… for Hotels" — sector-targeting article fragments
    r"(?i)\bfor\s+(restaurants|hotels|warehouses|hospitals|retailers|operators|facilities)\s*$",

    # "Why X" article openers (single extra word, or industry/verb second word)
    r"(?i)^why\s+\w+\s*$",
    r"(?i)^why\s+(warehouse|hotel|restaurant|hospital|logistics|food|retail|manufacturing|healthcare|serve|use|choose|adopt|deploy|implement|invest|automate|switch|embrace|consider|event)\b",

    # "Where X Is/Are Headed" headline pattern
    r"(?i)^where\s+\w+\s+(is|are)\s+(headed|going)",

    # Action-verb openers — not company names
    r"(?i)^(pushing|boosting|leveraging|driving|solving|fixing|mastering|navigating|revolutionizing|transforming)\s+\w+",

    # "Using Flexible Robotics" — instructional headline, not a legal entity
    r"(?i)^using\s+\w+\s+robotics\s*$",

    # Multilateral / grant headlines: "EBRD Grants RON", "IMF Grants USD" (not companies)
    r"(?i)\bgrants\s+(usd|eur|gbp|ron|try|pln|czk|sek|nok|dkk|chf|huf|bgn|aed|sar)\b",

    # Listicle stub: "These Robotics Companies" (not a legal name)
    r"(?i)^these\s+\w+\s+companies\s*$",

    # News headline: "[Brand] hopes robots can…" (sentence in name field)
    r"(?i)^[A-Za-z][A-Za-z&]+\s+hopes\s+\w+",
    r"(?i)\bhopes\s+robots?\b",
    r"(?i)\bcan\s+replace\s+\d",

    # Truncated stat headline fragments
    r"(?i)\b\d+[KkMm]\s+future\s*$",

    # University / dept fragment: "UF's RoboPI lab" (not an operating company name)
    r"(?i)^[A-Z]{2,4}'s\s+\S+\s+lab\s*$",

    # Names ending in bare " industry" (sector label, not legal entity)
    r"(?i)\s+industry\s*$",

    # Trade show / conference names scraped as companies
    r"(?i)^(ces|logimat|promat|modex|imts|pack\s*expo|automatica|groceryshop|shoptalk)\b",

    # Year + dash separator in name → conference/event/article title, not a company
    r"\b(202[4-9]|20[3-9]\d)\s*[-–—]",

    # Named after a state/city + generic venue type — usually a headline "Florida Restaurant …"
    r"(?i)^(florida|california|texas|new\s+york|ohio|georgia|arizona|illinois|"
    r"michigan|washington|colorado|nevada|virginia|pennsylvania|north\s+carolina|"
    r"south\s+carolina|new\s+jersey|massachusetts|minnesota|tennessee)\s+"
    r"(restaurant|hotel|warehouse|hospital|casino|factory|retail\s+store|"
    r"grocery\s+store|distribution\s+center)\b",

    # Machine / equipment type labels (not companies) — common in packaging/EOL scrapes
    r"(?i)^(drum|bottle|can|case|tray|bag|pouch|box|carton|pallet)\s+(filling|packing|sealing|"
    r"labeling|wrapping|forming|erecting|loading|handling)\s+(machine|system|equipment|line)\s*$",
    r"(?i)\b(filling\s+machine|labeling\s+machine|wrapping\s+machine|sealing\s+machine|"
    r"packing\s+machine|capping\s+machine|casing\s+machine|palletizing\s+machine|"
    r"vending\s+machine|boiler\s+system|conveyor\s+system)\s*$",
    r"(?i)^(package|drum|boiler|filler|labeler|capper|sealer|wrapper|conveyor|sorter)\s+"
    r"(boiler|filler|machine|system|equipment|tools?|unit|assembly)\s*$",

    # Food product / ingredient categories (not operating companies)
    r"(?i)^(canned|frozen|dried|fresh|processed|packaged|organic|fortified)\s+"
    r"(soup|food|meals?|goods|produce|meat|protein|beverage|drinks?|snacks?|cereals?)\s*$",
    r"(?i)^(global|major|big|top|leading|premium|value)\s+"
    r"(food|beer|beverage|snack|brand|chain|market)\s*$",

    # Political / news headline openers (scraped from political news)
    r"(?i)^(trump|biden|president|senate|congress|democrat|republican|federal|white\s+house)\s+",
    r"(?i)\b(declares|passed|signed|voted|lawmakers|legislation|executive\s+order)\b",
    r"(?i)^exclusive\s+(senate|congress|report|investigation|sources?|data)\b",

    # COVID / crisis / disaster headline fragments
    r"(?i)\b(caught\s+covid|covid\s+outbreak|meat\s+plant\s+workers|covid-19\s+cases)\b",
    r"(?i)^at\s+least\s+\d+[KMB]?\s+\w+",

    # Market/research report patterns
    r"(?i)\s+(market\s+overview|market\s+report|market\s+analysis|market\s+forecast|"
    r"market\s+outlook|market\s+size|market\s+share|market\s+trends?)\s*$",
    r"(?i)^(foods?|snacks?|beverages?|retail|packaging)\s+market\s+overview\s*$",

    # Verb phrases that are clearly headlines, not company names (EOL scrape common)
    r"(?i)^[A-Z][a-z]+\s+(peels|peel|unveils|slashes|halts|pulls|rolls|taps|nets|inks|eyes)\s+",
    r"(?i)^(creates?\s+new|solves?\s+the|fixes?\s+the|should\s+your|improving\s+)",

    # "Standout X Machinery / Solutions / Products" — article titles, not companies
    r"(?i)^(standout|top|leading|best)\s+\w+\s+(machinery|solutions?|products?|technologies?|"
    r"systems?|approaches?)\s*$",

    # Distribution center / plant named with a city only — headline fragments
    r"(?i)^(spartanburg|cornhusker|blue\s+ridge|rust\s+belt|heartland)\s+(distribution|"
    r"plant|facility|center|clink|hub)\s*$",

    # (Airport / exchange code check moved to is_junk() to keep case-sensitive)

    # ── Hyperbole / editorial / how-to patterns ────────────────────────────
    # These look like automation signals but are editorial content, not company actions.
    # "This is the most awesome way to automate frying potatoes."
    # "Here's how to deploy robots in your warehouse."
    # "5 ways to automate your packaging line."
    r"(?i)^(this|it|that|these|those)\s+(is|are|was|were|has\s+been|have\s+been)\s+",
    r"(?i)^here('s|\s+is|\s+are)\s+(how|why|what|the|a)\b",
    r"(?i)^\d+\s+(ways?|tips?|steps?|reasons?|things?|methods?|strategies?)\s+(to|for)\b",
    r"(?i)^the\s+(best|ultimate|complete|definitive|top|only|right|smart|easiest|fastest)\s+"
    r"(way|ways|guide|method|approach|solution|strategy|path)\s+(to|for)\b",
    r"(?i)^how\s+to\s+(automate|deploy|use|leverage|integrate|implement|adopt)\b",
    r"(?i)^why\s+(you\s+)?(should|need|must|want|have\s+to)\s+(automate|deploy|use|invest)\b",
    r"(?i)^(a|the)\s+(beginner'?s?|complete|quick|simple|easy)\s+guide\s+(to|for)\b",
    r"(?i)^what\s+(is|are)\s+(automation|robotics|ai|the\s+future|the\s+difference)\b",
    # "The Future of X" / "State of X" already caught, but belt-and-suspenders:
    r"(?i)^(is|are|can|will|does|do|should)\s+(robots?|automation|ai|technology)\b",
    # "X Celebrates Y" / "X Highlights Y" — headline verb fragments not company names
    r"(?i)\b(celebrates|highlighted?s?|announces?|introduces?|names?|appoints?|"
    r"sets|picks|picks up|taps|inks|nets|eyes|unveils?)\s+\w",

    # "Highest Paying …" / "Best Paying …" job article titles
    r"(?i)^(highest|best|top)\s+paying\b",

    # Generic single-word stubs that are not proper nouns (exact match via short word)
    r"^(Investment|Mezzanines|Logistics|Packaging|Manufacturing|Automation|"
    r"Technology|Innovation|Solutions|Services|Operations|Distribution)\s*$",

    # "World X" where X is a product/material (not "World Bank", "World Health Org")
    r"(?i)^world\s+(cement|waterjet|steel|plastic|packaging|paper|rubber|foam|glass)\b",

    # Conference / agenda / schedule fragments
    r"(?i)^(full|complete|complete\s+list\s+of|official)\s+(conference|agenda|schedule|program|lineup)\b",
    r"(?i)\d{4}\s*(agenda|schedule|lineup|program)\s*$",

    # ── Junk patterns added from user feedback (Apr 2026) ────────────────────
    # "Koch Strengthens Retail Fulfillment Strategy" / "Sweetgreen Sells Robotics Arm"
    # Catches company name + strong headline verb — expands the existing verb stem list.
    # NOTE: "plan" omitted — matches "Plant" (noun). Exclude "Partnership …" and plural "Partners " (legal names).
    r"(?i)^(?:\S+\s+){0,3}(strengthen|sell|sold|sells|acquir|partner(?!ship|s(?:\s|$))|pivot|merge|rebrand|restructur)\w*\s+\w",

    # "Wins EU Contract", "Won the Bid", "Secures Major Deal" — verb-first fragment
    r"(?i)^(wins?|won|secures?|secured|clinch(es)?|clinched|bags?|bagged|awarded?|landed?)\s+\w",

    # "Tesla Plans" / "Amazon Eyes" — [known brand] + standalone verb (headline stub, ≤3 words)
    r"(?i)^(tesla|apple|amazon|google|meta|nvidia|microsoft|walmart|target|kroger|"
    r"starbucks|mcdonald|costco|home\s*depot|lowe'?s|walgreens|cvs|fedex|ups)\s+"
    r"(plans?|eyes?|aims?|mulls?|weighs?|considers?|explores?|eyes?)\b",

    # "[US city] plant / facility" — location description, not a company
    r"(?i)^(tampa|orlando|jacksonville|phoenix|tucson|denver|boulder|oakland|"
    r"raleigh|durham|richmond|norfolk|buffalo|rochester|louisville|"
    r"birmingham|mobile|charleston|columbia|tulsa|albuquerque|omaha|"
    r"spokane|tacoma|stockton|toledo|anchorage|bakersfield|modesto)\s+"
    r"(plant|facility|hub|depot|campus|warehouse|distribution)\s*$",

    # "[Country adjective] facility / plant / operation" — location not company
    r"(?i)^(german|french|japanese|chinese|british|italian|spanish|dutch|"
    r"korean|swedish|canadian|australian|mexican|brazilian|indian|thai|"
    r"polish|czech|romanian|hungarian|greek|portuguese|turkish|"
    r"russian|ukrainian|vietnamese|singaporean|taiwanese|belgian|swiss|"
    r"austrian|danish|norwegian|finnish|irish)\s+"
    r"(facility|plant|campus|hub|office|warehouse|factory|center|operation|subsidiary)\s*$",

    # "[Name] County restaurant / hospital / warehouse" — county + venue type
    r"(?i)^[A-Za-z]+\s+county\s+(restaurant|hotel|hospital|warehouse|casino|"
    r"grocery\s+store|retail\s+store|distribution\s+center|facility|plant)\b",

    # "[Industry] robotics firm [Company]" — company description wrapping another name
    # "Warehouse robotics firm GreyOrange", "Food delivery robot company Starship"
    r"(?i)^(warehouse|logistics|food|delivery|service|hospital|retail|"
    r"manufacturing|industrial)\s+(robotics?|automation)\s+(firm|company|"
    r"startup|vendor|maker|provider|specialist|leader)\s+[A-Z]",

    # "CSA Exclusive H&M" / "Nike Exclusive [Partner]" — retail collab header scraped as name
    r"(?i)\bexclusive\s+[A-Z&][A-Z&]*\s*$",

    # "[Adjective] + expansion / acquisition / merger" — M&A headline fragment
    r"(?i)^(major|new|record|significant|massive|large-scale|historic|planned|"
    r"pending|proposed|confirmed|announced|completed)\s+"
    r"(expansion|acquisition|merger|deal|investment|partnership|contract|order)\s*$",

    # "Global Pallet Labelling System" / "Automated Case Labeling Equipment"
    r"(?i)^(global|new|advanced|automated|smart|integrated|next-gen)\s+"
    r"(pallet|case|box|carton|drum|bottle|can)\s+"
    r"(labelling|labeling|packing|sealing|wrapping|forming)\s+"
    r"(system|systems?|machine|equipment|line|solution)\s*$",

    # "[Topic] Research" / "[Topic] Technology Research" — academic/research label
    r"(?i)^([\w\s-]+)\s+(prevention|treatment|management)\s+technology\s+research\s*$",

    # "[Material] Manufacturing Plant DPR/Setup" — project brief, not a company
    r"(?i)^[\w\s]+(manufacturing|fabrication|processing)\s+plant\s+(dpr|setup|project|brief|report|study)\s*$",

    # ── Editorial deck / headline fragments (user-reported, Apr 2026) ─────────
    # "Meet Betty Bot" — article / profile intro, not a legal entity name
    r"(?i)^meet\s+",
    # "New MIT Mecalux" — news-deck collaboration line (university + partner), not a company row
    r"(?i)^new\s+(mit|harvard|stanford|berkeley|cmu|caltech|yale|princeton|columbia|cornell|"
    r"gatech|georgia tech|ucla|usc|nyu|duke|northwestern|oxford|cambridge)\s+\S",
    # "Inside Alaska Airlines…" — magazine-style deck (needs ≥3 words; avoids "Inside Out")
    r"(?i)^inside\s+[A-Z]\w+\s+[A-Z]",
    # Rhetorical or survey-style titles scraped as names
    r"(?i)\?{2,}\s*$",  # two+ trailing ? (clickbait / deck uncertainty)
    r"\?\s*$",
    # Truncated RSS / deck copy: "Swedish sports retailer…?"
    r"\.{3,}",
    # Nordic + sport + generic role — **entire** name is the headline stub (not "… retailer Stadium").
    r"(?i)^(swedish|norwegian|danish|finnish|icelandic|estonian|latvian|lithuanian)\s+"
    r"(sport|sports)\s+(airline|airlines|carrier|retailer|retailers|chain|chains|"
    r"brand|brands|group)\s*[\s.?!…]*$",

    # ── User-reported composites / deck garbage (Apr 2026) ───────────────────
    # SQL/CMS fragments ("… ydr=="), double hyphen export ("CharterSync--")
    r"==",
    r"(?i)--+\s*$",
    # UI/headline tail: "Lucas Systems Fetch"
    r"(?i).{10,}\s+fetch\s*$",
    # Two vendors concatenated in one name field
    r"(?i)\s+and\s+locus\s+robotics\b",
    r"(?i)\bbito\s+lagertechnik\s+and\b",
    # Hospital + local paper slug leaked into name
    r"(?i)\s-\s*ydr\b",
    # Buzzword stubs mistaken for companies (exact-ish; see _JUNK_EXACT too)
    r"(?i)^physical\s+ai\s*$",
    r"(?i)^tutor\s+intelligence\s*$",
    r"(?i)^bangladesh\s+rmg\s*$",
]
_JUNK_RE = [re.compile(p, re.IGNORECASE) for p in _JUNK_PATTERNS]

# Names that should always be treated as junk regardless of other rules
# (exact match, case-insensitive)
_JUNK_EXACT = frozenset({
    "trending", "co-op", "co op", "cooperative", "industry", "market",
    "the market", "brands", "hotels", "operators", "chains", "companies",
    "businesses", "employers", "workers", "travelers", "guests", "consumers",
    "managers", "respondents", "report", "study", "survey", "data", "news",
    "update", "alert", "source", "analysis", "insights", "statistics",
    "the", "a", "an", "and", "or", "inc", "llc", "corp", "ltd", "co",
    # Domain / section titles scraped as “company” (not proper nouns)
    "supply chain", "supply-chain", "the supply chain",
    "value chain", "the value chain",
    "logistics", "the logistics", "global logistics",
    "procurement", "strategic sourcing", "global sourcing", "sourcing",
    "distribution", "distribution network",
    "operations", "operations management",
    "fulfillment", "order fulfillment",
    "warehouse", "warehousing",
    "inventory management",
    "transportation", "freight", "shipping",
    "digital transformation", "business transformation",
    "customer experience", "customer service",
    "human resources", "human capital",
    "e-commerce", "ecommerce", "omnichannel",
    "industrial automation",
    "machine learning",
    # Single generic adjectives commonly scraped as company names
    "flexible", "scalable", "automated", "autonomous", "intelligent",
    "advanced", "integrated", "connected", "digital",
    # Generic two-word stubs
    "material handling", "battery lifters", "pallet trucks",
    "can ai", "we want",
    # Geography / generic words mistaken for company names (single-field scrapes)
    "capital",
    "las vegas",
    # Single generic words that slip through (user-reported)
    "growth", "growth rate", "data center", "boosting",
    # Generic plural category nouns (not company names)
    "hotel chains", "restaurant chains", "grocery chains", "retail chains",
    "hotel brands", "restaurant brands", "food brands", "consumer brands",
    "hospital networks", "health networks", "hospital systems",
    "hotel groups", "restaurant groups", "food groups",
    # Countries / regions as standalone "companies" (user-reported)
    "germany", "france", "japan", "china", "india", "brazil", "canada",
    "australia", "mexico", "italy", "spain", "south korea", "north korea",
    "russia", "ukraine", "turkey", "indonesia", "argentina", "netherlands",
    "switzerland", "sweden", "norway", "denmark", "finland", "poland",
    "singapore", "taiwan", "vietnam", "thailand", "malaysia", "philippines",
    "saudi arabia", "uae", "united arab emirates", "egypt", "nigeria",
    "south africa", "kenya", "israel", "pakistan", "bangladesh",
    "europe", "asia", "africa", "latin america", "middle east",
    "north america", "south america", "southeast asia", "western europe",
    "eastern europe", "asia pacific",
    # News / syndicated (whole “name” is the outlet or a sector label)
    "business insider",
    "reuters",
    "associated press",
    "cnbc",
    "fox business",
    "marketwatch",
    "the wall street journal",
    "wall street journal",
    "hospitality robot sector",
    # Article / category lines mistaken for legal names (user-reported)
    "warehouse automation",
    "warehouse management top",
    # Single-token vertical stubs scraped from news (not operating company names)
    "airport",
    "development",
    "equipment",
    "football",
    "smoothies",
    # Generic tech headline noun pair (not a company name by itself)
    "ai agents",
    # Headline dollar/stat fragments scraped as company names (e.g. "$46 million round")
    "million",
    # HR / benefits listicle fragment scraped as a company name
    "essential benefits",
    # Headline/UI tail merged into company.name
    "lucas systems fetch",
    # Generic single nouns that are never company names
    "expansion", "acquisition", "merger", "investment", "contract", "deal",
    "announcement", "restructuring", "partnership", "collaboration",
    "major expansion", "new expansion", "record expansion",
    "cold storage network", "cold storage networks",
    "medication safety", "patient safety", "worker safety", "food safety",
    "warehouse robotics use", "warehouse robotics adoption",
    "semiconductor sourcing", "component sourcing", "chip sourcing",
    "size share",
    # User-reported scraper headline fragments (Apr 2026)
    "peak season",
    "exclusive eqt bets",
    "google cloud team up",
    "distribution center jobs while increasing",
    "blue jay takes flight amazon",
    "kenco greyorange",
    "san jos",
    "domino effect",
    "warehouse dc operations survey tech",
    "your warehouse",
    "melonee wise",
    "flexkeeping rollout following",
    "kentucky distribution center",
    # Location + facility stubs (not operating companies)
    "tampa plant", "tampa facility", "german facility", "german plant",
    "french facility", "japanese facility", "chinese facility",
})


def is_junk(name: Optional[str]) -> tuple[bool, str]:
    """
    Returns (True, reason) if the company name looks like scraper garbage.
    Returns (False, '') for clean names.
    """
    if not name:
        return True, "empty name"

    stripped = name.strip()
    low = stripped.lower()

    # Align with company_validator: short tickers (LG, BP, 3M) are not junk.
    if is_allowlisted_company_name(stripped):
        return False, ""

    if is_known_publication_name(stripped):
        return True, "news or trade publication (not a buyer company)"
    # Catch publications stored with trailing punctuation ("Modern Materials Handling.")
    stripped_punct = stripped.rstrip(".,;:!?")
    if stripped_punct != stripped and is_known_publication_name(stripped_punct):
        return True, "news or trade publication (not a buyer company)"

    bad_nc, reason_nc = reject_as_non_company_name(stripped)
    if bad_nc:
        return True, reason_nc

    if is_known_robotics_vendor_name(stripped):
        return True, "robotics vendor / OEM (not a buyer opportunity)"

    # Exact match against known-bad generic words
    if low in _JUNK_EXACT:
        return True, f"generic non-company word: '{stripped}'"

    # Substring check
    for sub in _JUNK_SUBSTRINGS:
        if sub in low:
            return True, f"junk substring: '{sub}'"

    # Regex pattern check
    for rx in _JUNK_RE:
        if rx.search(stripped):
            return True, f"junk pattern: {rx.pattern[:60]}"

    # Case-sensitive: standalone ALL-CAPS airport codes (EWR, JFK, LAX) — 2-3 letters only.
    # 4+ letter all-caps can be real companies (URBN, LVMH, BASF), so we exclude them.
    if re.match(r"^[A-Z]{2,3}(\d)?$", stripped):
        return True, "standalone uppercase airport/ticker code"

    # Case-sensitive: ISIN bond/stock identifier (two uppercase letters + 10 uppercase/digits)
    # e.g., "Rockwell Automation Stock ISIN US77463M1053"
    if re.search(r"\b[A-Z]{2}[A-Z0-9]{10}\b", stripped):
        return True, "ISIN bond/stock identifier embedded in name"

    # Article titles / listicles scraped as company.name — real buyer legal names here are short.
    if len(stripped) >= 68:
        return True, "name too long (likely article headline, not a company)"

    return False, ""


# ─── Priority tier ────────────────────────────────────────────────────────────

TIERS = ("HOT", "WARM", "COLD")

# Industries where automation robots have the strongest fit
HIGH_FIT_INDUSTRIES = {
    "hospitality", "hotel", "hotel & hospitality",
    "logistics", "supply chain", "3pl", "distribution",
    "healthcare", "hospital", "senior living", "assisted living",
    "food service", "food & beverage", "restaurant", "catering",
    "warehouse", "fulfillment",
    # End-of-line / manufacturing / CPG verticals
    "food processing", "food manufacturing", "food processing & manufacturing",
    "cpg", "consumer goods", "cpg & consumer goods",
    "contract manufacturing", "contract manufacturer",
    "beverage", "bottling", "packaging",
    "manufacturing", "automotive & manufacturing",
}

# Signal types — exported for SQL rollups (leads API) so summary/homepage match classify_lead.
# HOT  → budget / mandate / deployment — priority outreach
# WARM → pain, expansion, exploration — nurture & watch
# API still emits tier COLD internally; product copy calls it "Emerging" (all have potential).
SIGNAL_TYPES_HOT = frozenset({
    "funding_round",
    "strategic_hire",
    "capex",
    "ma_activity",
    "labor_pain",
    "labor_shortage",          # can't staff = direct robotics buyer
    "expansion",               # capital deployment = budget for automation
    "automation_intent",       # internal / job-board style
    "quality_bottleneck",
    "safety_incident",
    "production_capacity",
    "warehouse_throughput",
    "packaging_automation",
    "repetitive_process",
    "material_handling",       # physical throughput problem
    # Deployment & procurement
    "robot_installation",
    "pilot_success",
    "scale_expansion",
    "vendor_selection",
    "roi_documented",
    "economics_driven",
    "competitive_response",
    "problem_solution",
    "government_contract",
    "rfp_posted",
})
SIGNAL_TYPES_WARM = frozenset({
    "job_posting",
    "news",
    "service_consistency",
    "equipment_integration",
    # Classifier emits automation_interest widely — treat as explore/nurture, not max HOT
    "automation_interest",
})

# Aliases for membership checks in priority_tier (frozenset supports `in`)
_HOT_SIGNAL_TYPES = SIGNAL_TYPES_HOT
_WARM_SIGNAL_TYPES = SIGNAL_TYPES_WARM

# One strong deployment/procurement hit can justify HOT with moderate ML score
DEPLOYMENT_SIGNAL_TYPES = frozenset({
    "robot_installation", "pilot_success", "scale_expansion", "vendor_selection", "rfp_posted",
})

# Buyer-opportunity gate: a lead must show end-customer buying intent before it
# can be treated as a sales opportunity. This protects HOT/WARM from article
# subjects, vendor funding stories, category names, and event/sponsorship noise.
BUYER_DIRECT_SIGNAL_TYPES = frozenset({
    "labor_pain",
    "labor_shortage",
    "capex",
    "quality_bottleneck",
    "safety_incident",
    "production_capacity",
    "warehouse_throughput",
    "packaging_automation",
    "repetitive_process",
    "material_handling",
    "robot_installation",
    "pilot_success",
    "scale_expansion",
    "vendor_selection",
    "roi_documented",
    "economics_driven",
    "competitive_response",
    "problem_solution",
    "government_contract",
    "rfp_posted",
})

BUYER_EXPANSION_RE = re.compile(
    r"\b(new|opening|opened|opens|build(?:ing)?|construction|breaks?\s+ground|"
    r"expan(?:d|ds|ded|sion)|renovat(?:e|es|ed|ion)|facility|warehouse|"
    r"distribution\s+center|fulfillment\s+center|plant|factory|hotel|property|"
    r"resort|terminal|gate|sq\.?\s*ft|square\s+feet)\b",
    re.IGNORECASE,
)

BUYER_OPERATIONS_HIRE_RE = re.compile(
    r"\b(?:vp|svp|evp|vice\s+president|director|head|chief|manager|lead)\s+"
    r"(?:of\s+)?(?:operations?|automation|robotics?|supply\s+chain|warehouse|"
    r"fulfillment|manufacturing|facilit(?:y|ies)|logistics|engineering)\b|"
    r"\b(?:operations?|automation|robotics?|supply\s+chain|warehouse|fulfillment|"
    r"manufacturing|facilit(?:y|ies)|logistics)\s+"
    r"(?:vp|svp|evp|vice\s+president|director|head|chief|manager|lead)\b",
    re.IGNORECASE,
)

BUYER_TEXT_EVIDENCE_RE = re.compile(
    r"\b(labor\s+shortage|worker\s+shortage|staff(?:ing)?\s+shortage|"
    r"vacanc(?:y|ies)|understaffed|turnover|wage\s+pressure|overtime|"
    r"capex|capital\s+(?:expenditure|investment)|budget(?:ed|ing)?|"
    r"rfp|request\s+for\s+proposal|procurement|vendor\s+selection|"
    r"deployed?|deploying|deployment|install(?:s|ed|ing|ation)?|pilot(?:s|ing|ed)?|"
    r"rollout|go-live|went\s+live|fleet\s+of\s+robots|robot\s+staff|"
    r"unveil(?:s|ed|ing)?\s+(?:.*\b)?(?:robot|robotic|automation)|"
    r"evaluating\s+(?:robot|automation)|implement(?:s|ed|ing)?\s+(?:robot|automation)|"
    r"throughput\s+bottleneck|capacity\s+constraint|at\s+capacity|"
    r"quality\s+(?:issue|problem|bottleneck)|safety\s+(?:incident|risk)|"
    r"repetitive\s+(?:task|work|process)|material\s+handling|"
    r"housekeeping|room\s+service|back-of-house|kitchen\s+automation)\b",
    re.IGNORECASE,
)

SELLER_OR_PUBLISHER_CONTEXT_RE = re.compile(
    r"\b(sponsor(?:s|ed|ing)?|summit|conference|webinar|expo|trade\s+show|"
    r"press\s+release|pr\s+newswire|globenewswire|business\s+wire|"
    r"robotics?\s+(?:firm|startup|vendor|maker|manufacturer|company)|"
    r"automation\s+(?:platform|vendor|software|startup|provider|solution)|"
    r"healthtech\s+automation\s+platform|deeptech\s+startup|"
    r"consultanc(?:y|ies)\s+(?:appoints?|hires?|names?)|"
    r"raises?\s+\$|funding\s+round|series\s+[abc])\b",
    re.IGNORECASE,
)

# ─── Priority scoring knobs (Hot / Warm / Emerging) — also surfaced on /api/leads/scoring-system ───
# Tuned looser (Mar 2026 v2): lower composite floors, higher boosts, broader HOT signal set.
PRIORITY_COMPOSITE_CAP = 100.0
PRIORITY_INDUSTRY_FIT_BOOST = 8.0         # was 6.0 — high-fit industry is a strong buy signal
# Volume tiers: first matching tier applies (not cumulative)
PRIORITY_SIGNAL_VOLUME_TIERS = (
    (8, 4.5, True),   # (min_signal_count, boost_points, append_reason_to_priority_reasons)
    (5, 3.0, False),
    (3, 2.0, False),
)
PRIORITY_ENTERPRISE_MIN_EMPLOYEES = 5000
PRIORITY_ENTERPRISE_BOOST = 6.0           # was 5.0
PRIORITY_MIDMARKET_MIN_EMPLOYEES = 1000
PRIORITY_MIDMARKET_BOOST = 3.0            # was 2.0
# Tier cutoffs on composite = min(PRIORITY_COMPOSITE_CAP, ml_base + boosts)
PRIORITY_HOT_COMPOSITE_MIN = 70.0         # was 78.0
PRIORITY_HOT_COMPOSITE_WITH_HOT_SIGNALS = 62.0  # was 72.0
PRIORITY_WARM_COMPOSITE_MIN = 42.0        # was 47.0
PRIORITY_WARM_BASE_WITH_INDUSTRY = 35.0   # was 40.0
# "hot_enough" gates: a single distinct hot type is sufficient
PRIORITY_HOT_DISTINCT_TYPES_MIN = 1       # was 2 — one real buying signal is enough
PRIORITY_HOT_BASE_WITH_TWO_HITS = 45.0   # was 55.0
PRIORITY_HOT_BASE_WITH_ONE_HIT = 52.0    # was 62.0
PRIORITY_HOT_BASE_WITH_DEPLOYMENT = 38.0  # was 45.0
# Sublinear hot/warm boost caps (see _hot_signal_boost / _warm_signal_boost)
HOT_SIGNAL_BOOST_CAP = 24.0              # was 18.0
WARM_SIGNAL_BOOST_CAP = 12.0             # was 9.0


@dataclass
class PriorityResult:
    tier: str                        # HOT | WARM | COLD
    score: float                     # 0–100
    reasons: List[str] = field(default_factory=list)


def _industry_fits(industry: Optional[str]) -> bool:
    if not industry:
        return False
    low = industry.lower()
    return any(k in low for k in HIGH_FIT_INDUSTRIES)


def _hot_signal_boost(hot_types: List[str]) -> float:
    """
    Cap how much raw signal *count* can inflate the tier. Previously every row in
    `signals` repeated the same type (e.g. many `news` mis-tagged as hot bucket
    in SQL rollups) and added +5 each → composite pegged at 100 and HOT flooded.
    """
    if not hot_types:
        return 0.0
    n = len(hot_types)
    u = len(set(hot_types))
    # Diversity: up to +14 for 2+ distinct hot types; volume: sublinear, capped
    diversity = min(14.0, 7.0 * min(2, u))
    extra_same = max(0, n - u)
    volume = min(10.0, 1.6 * min(6, extra_same) + 1.1 * min(3, u))
    return min(HOT_SIGNAL_BOOST_CAP, diversity + volume)


def _warm_signal_boost(warm_types: List[str]) -> float:
    if not warm_types:
        return 0.0
    n = len(warm_types)
    u = len(set(warm_types))
    return min(WARM_SIGNAL_BOOST_CAP, 3.0 * min(3, u) + 0.9 * min(5, max(0, n - u)))


def priority_tier(
    overall_score: float,
    industry: Optional[str],
    signal_types: List[str],
    signal_count: int,
    employee_estimate: Optional[int] = None,
) -> PriorityResult:
    """
    Compute a priority tier independently of the inference engine score.
    Combines rule-based boosters with the overall ML score.
    """
    reasons: List[str] = []
    boost = 0.0

    # Base: ML inference score drives the tier
    base = overall_score

    # Industry fit boost (was 8 — too many WARM/HOT via industry alone)
    if _industry_fits(industry):
        boost += PRIORITY_INDUSTRY_FIT_BOOST
        reasons.append(f"high-fit industry ({industry})")

    # Signal type boosters (capped — do not let N duplicate rows max out composite)
    hot_hits = [s for s in signal_types if s in _HOT_SIGNAL_TYPES]
    warm_hits = [s for s in signal_types if s in _WARM_SIGNAL_TYPES]
    if hot_hits:
        boost += _hot_signal_boost(hot_hits)
        unique_hot = list(dict.fromkeys(hot_hits))[:5]
        if len(hot_hits) > 5:
            reasons.append(f"{len(hot_hits)} hot-type signals ({', '.join(unique_hot)}, ...)")
        else:
            reasons.append(f"{len(hot_hits)} hot-type signals ({', '.join(unique_hot)})")
    if warm_hits:
        boost += _warm_signal_boost(warm_hits)

    # Signal volume boost (mild — type boosts already reflect volume somewhat)
    for min_cnt, pts, with_reason in PRIORITY_SIGNAL_VOLUME_TIERS:
        if signal_count >= min_cnt:
            boost += pts
            if with_reason:
                reasons.append(f"{signal_count} signals")
            break

    # Employee size boost (enterprise = more budget)
    if employee_estimate and employee_estimate >= PRIORITY_ENTERPRISE_MIN_EMPLOYEES:
        boost += PRIORITY_ENTERPRISE_BOOST
        reasons.append(f"enterprise ({employee_estimate:,} employees)")
    elif employee_estimate and employee_estimate >= PRIORITY_MIDMARKET_MIN_EMPLOYEES:
        boost += PRIORITY_MIDMARKET_BOOST

    composite = min(PRIORITY_COMPOSITE_CAP, base + boost)

    # HOT: stricter. Duplicate rows of one hot type (e.g. RSS noise) must not
    # qualify on composite alone — need distinct intent types OR strong base score.
    distinct_hot = len(set(hot_hits))
    has_deployment_signal = any(s in DEPLOYMENT_SIGNAL_TYPES for s in signal_types)
    hot_enough = (
        distinct_hot >= PRIORITY_HOT_DISTINCT_TYPES_MIN
        or (len(hot_hits) >= 2 and base >= PRIORITY_HOT_BASE_WITH_TWO_HITS)
        or (len(hot_hits) >= 1 and base >= PRIORITY_HOT_BASE_WITH_ONE_HIT)
        or (
            has_deployment_signal
            and len(hot_hits) >= 1
            and base >= PRIORITY_HOT_BASE_WITH_DEPLOYMENT
        )
    )
    if composite >= PRIORITY_HOT_COMPOSITE_MIN or (
        composite >= PRIORITY_HOT_COMPOSITE_WITH_HOT_SIGNALS and hot_enough
    ):
        return PriorityResult("HOT", composite, reasons)
    if composite >= PRIORITY_WARM_COMPOSITE_MIN or (
        base >= PRIORITY_WARM_BASE_WITH_INDUSTRY and _industry_fits(industry)
    ):
        return PriorityResult("WARM", composite, reasons)
    return PriorityResult("COLD", composite, reasons)


# "Target" as common word (goal/benchmark) — when signals are about xAI, Anthropic, etc. saying "exceeds target"
# "Target" as single word is almost always a false positive (common word in funding headlines)
# Real Target Corporation would typically have "Target Corporation" or "Target stores"
_TARGET_FALSE_POSITIVE_PHRASES = (
    "exceeds its target", "exceeding its target", "surpassing target", "surpassed target",
    "exceeds target", "exceeded target", "exceeding target", "xai", "anthropic",
    "elon musk", "billion target", "million target", "funding target", "revenue target",
    "exceeds its own target", "surpassing initial target", "exceeding its $",
)

def _signal_text_blob(signals) -> str:
    parts = []
    for s in signals or []:
        t = getattr(s, "signal_text", None) or ""
        t = re.sub(r"<[^>]+>", " ", str(t))
        parts.append(t.lower())
    return " ".join(parts)


def _buyer_opportunity_gate(signals) -> tuple[bool, str]:
    """
    Require evidence that the record is an end-customer buying opportunity, not
    just a robotics/news/vendor headline. Empty signal sets are allowed to stay
    as non-promoted COLD records; records with signals must prove buyer intent.
    """
    sigs = list(signals or [])
    if not sigs:
        return True, ""

    sig_types = [getattr(s, "signal_type", None) or "" for s in sigs]
    blob = _signal_text_blob(sigs)

    direct_types = {t for t in sig_types if t in BUYER_DIRECT_SIGNAL_TYPES}
    has_direct_type = bool(direct_types)
    has_expansion_evidence = "expansion" in sig_types and bool(BUYER_EXPANSION_RE.search(blob))
    has_operations_hire = "strategic_hire" in sig_types and bool(BUYER_OPERATIONS_HIRE_RE.search(blob))
    has_text_evidence = bool(BUYER_TEXT_EVIDENCE_RE.search(blob))

    has_buyer_intent = (
        has_direct_type
        or has_expansion_evidence
        or has_operations_hire
        or has_text_evidence
    )
    has_seller_context = bool(SELLER_OR_PUBLISHER_CONTEXT_RE.search(blob))

    if has_seller_context and not has_buyer_intent:
        return False, "seller/vendor or publisher story, not a buyer opportunity"

    if not has_buyer_intent:
        return False, "no buyer-intent signal found (labor, expansion, capex, RFP, deployment, or operations hiring)"

    return True, ""


def _company_name_not_corroborated_by_signals(name: str, signals) -> bool:
    """
    Headline fragments stored as company.name with unrelated news bullets (e.g. "Million"
    + Fetch Robotics / Starship stories). Require the name tokens to appear in signal text.
    """
    if not name or not signals or len(signals) < 2:
        return False
    stripped = name.strip()
    if is_allowlisted_company_name(stripped):
        return False
    low = stripped.lower()
    blob = _signal_text_blob(signals)
    if low in blob:
        return False
    tokens = [t for t in re.split(r"[\s'&]+", low) if len(t) >= 3]
    if len(tokens) >= 2:
        return not any(tok in blob for tok in tokens)
    if len(tokens) == 1:
        tok = tokens[0]
        if len(tok) < 4 or len(tok) > 18:
            return False
        return tok not in blob
    return False


def _is_target_false_positive(company_name: str, signals) -> bool:
    """Target Corp vs common-word 'target' in funding headlines (xAI, Anthropic, etc.)."""
    name_lower = (company_name or "").strip().lower()
    # Single-word "Target" only - "Target Corporation" stays
    if not name_lower or name_lower != "target":
        return False
    # Always filter single-word "Target" - nearly always false positive from "exceeds target" etc.
    # Keep only if signals clearly reference Target Corporation (stores, retail, etc.)
    sigs = signals or []
    target_corp_phrases = ("target corporation", "target corp", "target stores", "target retail", "target.com")
    for s in sigs:
        text = (getattr(s, "signal_text", None) or getattr(s, "raw_text", None) or "").lower()
        if any(phrase in text for phrase in target_corp_phrases):
            return False  # Real Target Corp - don't filter
    # Single-word "Target" with no Target Corp context = always block (false positive from "exceeds target" etc.)
    return True


# ─── Convenience wrapper ──────────────────────────────────────────────────────

def pick_primary_score(scores_or_one: Any):
    """
    ORM may return one Score (uselist=False) or multiple rows in Postgres (duplicates / migrations).
    SQLAlchemy raises MultipleResultsFound for uselist=False when >1 row exists — use uselist=True
    and pick the latest score row here.
    """
    if scores_or_one is None:
        return None
    if isinstance(scores_or_one, list):
        if not scores_or_one:
            return None
        return max(
            scores_or_one,
            key=lambda s: (
                getattr(s, "last_calculated_at", None) or datetime.min.replace(tzinfo=timezone.utc),
                getattr(s, "id", 0) or 0,
            ),
        )
    return scores_or_one


def classify_lead(company, scores_or_one, signals) -> tuple[bool, str, PriorityResult]:
    """
    Full classification for a single lead.

    `scores_or_one` may be a single Score, a list[Score], or None (relationship).

    Returns:
        (junk: bool, junk_reason: str, priority: PriorityResult)

    If junk is True, priority tier will be 'COLD' with no reasons.
    """
    name = getattr(company, "name", None)
    junk, junk_reason = is_junk(name)
    if junk:
        return True, junk_reason, PriorityResult("COLD", 0.0, [junk_reason])
    # Target false positive: "Target" from "exceeds its target" in xAI/Anthropic headlines
    if _is_target_false_positive(name or "", signals):
        return True, "target false positive (common-word in funding headlines)", PriorityResult("COLD", 0.0, ["target false positive"])

    if _company_name_not_corroborated_by_signals(name or "", signals):
        return True, "company name not found in signal text (mis-attributed headline fragment)", PriorityResult(
            "COLD", 0.0, ["mis-attributed headline fragment"]
        )

    # Logic engine (legal suffix, distinctive noun, structure, vendor, publication).
    # Listing APIs use classify_lead; this aligns HOT/WARM spotlight with is_valid_lead.
    from app.services.company_validator import is_valid_lead

    ok_logic, logic_reason = is_valid_lead(name or "", skip_junk_check=True)
    if not ok_logic:
        return True, f"logic engine: {logic_reason}", PriorityResult("COLD", 0.0, [logic_reason])

    ok_buyer, buyer_reason = _buyer_opportunity_gate(signals)
    if not ok_buyer:
        return True, f"buyer opportunity gate: {buyer_reason}", PriorityResult(
            "COLD", 0.0, [buyer_reason]
        )

    score = pick_primary_score(scores_or_one)
    overall = getattr(score, "overall_intent_score", 0.0) if score else 0.0
    sig_types = [s.signal_type for s in (signals or [])]
    sig_count = len(signals or [])
    emp = getattr(company, "employee_estimate", None)

    pri = priority_tier(overall, company.industry, sig_types, sig_count, emp)
    return False, "", pri
