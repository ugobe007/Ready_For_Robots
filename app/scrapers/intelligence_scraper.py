"""
Strategic Intelligence Scraper
================================
Fetches M&A, competitor, humanoid market, and industry trend news via
Google News RSS — same RSS pattern used by job_board_scraper.py.

Results are stored in the `intelligence_items` table (created on first run).
Runs once daily at 07:00 UTC. Can also be triggered manually via admin endpoint.

Categories:
  MA_WATCH      — acquisition targets: Reflex Robotics, DYNA, Vecna, Righthand, GreyOrange
  HUMANOID      — humanoid market: Figure AI, Agility Robotics, Boston Dynamics, 1X, Apptronik
  COMPETITOR    — direct competitors: Bear Robotics, Pudu, Keenon, Relay, Servi
  MARKET        — funding rounds, automation adoption, robotics investment
  INDUSTRY      — labor shortage, warehouse automation, hospitality robotics, logistics staffing
  PARTNER       — NVIDIA, Microsoft, Apple robotics; integration ecosystem news
"""

import logging
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus

import requests
from sqlalchemy import text
from app.database import SessionLocal, engine

logger = logging.getLogger(__name__)

RSS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ── Query registry ──────────────────────────────────────────────────────────

INTELLIGENCE_QUERIES: list[dict] = [
    # ── M&A Watch ───────────────────────────────────────────────────────────
    {"q": "Reflex Robotics acquisition OR funding OR partnership 2025",     "category": "MA_WATCH",   "tag": "Reflex Robotics"},
    {"q": "DYNA robotics acquisition OR merger OR investment",              "category": "MA_WATCH",   "tag": "DYNA Robotics"},
    {"q": "Vecna Robotics acquisition OR merger OR funding",                "category": "MA_WATCH",   "tag": "Vecna Robotics"},
    {"q": "Righthand Robotics acquisition OR funding OR merger",            "category": "MA_WATCH",   "tag": "Righthand Robotics"},
    {"q": "GreyOrange acquisition OR merger OR funding",                    "category": "MA_WATCH",   "tag": "GreyOrange"},
    {"q": "Aethon Robotics acquisition OR buy OR merge",                    "category": "MA_WATCH",   "tag": "Aethon"},
    {"q": "Locus Robotics acquisition OR merger acquisition 2025",          "category": "MA_WATCH",   "tag": "Locus Robotics"},
    {"q": "6 River Systems Fetch Robotics AMR acquisition 2025",            "category": "MA_WATCH",   "tag": "AMR M&A"},
    {"q": "service robot company acquisition merger deal 2025",             "category": "MA_WATCH",   "tag": "M&A Sector"},
    {"q": "humanoid robot company acquisition acqui-hire 2025",             "category": "MA_WATCH",   "tag": "Humanoid M&A"},

    # ── Humanoid Market ─────────────────────────────────────────────────────
    # US / Europe companies
    {"q": "Figure AI robot humanoid news funding 2025",                     "category": "HUMANOID",   "tag": "Figure AI"},
    {"q": "Agility Robotics Digit humanoid warehouse deployment 2025",       "category": "HUMANOID",   "tag": "Agility Robotics"},
    {"q": "Boston Dynamics Atlas humanoid biped commercial 2025",            "category": "HUMANOID",   "tag": "Boston Dynamics"},
    {"q": "1X Technologies Eve NEO humanoid robot 2025",                     "category": "HUMANOID",   "tag": "1X Technologies"},
    {"q": "Apptronik Apollo humanoid robot deployment partnership",          "category": "HUMANOID",   "tag": "Apptronik"},
    {"q": "Tesla Optimus humanoid robot production factory 2025",            "category": "HUMANOID",   "tag": "Tesla Optimus"},
    {"q": "Sanctuary AI Phoenix humanoid robot deployment 2025",             "category": "HUMANOID",   "tag": "Sanctuary AI"},
    {"q": "Apptronik humanoid robot news 2025",                              "category": "HUMANOID",   "tag": "Apptronik"},
    {"q": "NEURA Robotics 4NE-1 humanoid robot news 2025",                  "category": "HUMANOID",   "tag": "NEURA Robotics"},
    {"q": "Enchanted Tools Mirokai humanoid robot 2025",                    "category": "HUMANOID",   "tag": "Enchanted Tools"},
    {"q": "PAL Robotics TALOS humanoid robot deployment 2025",               "category": "HUMANOID",   "tag": "PAL Robotics"},
    {"q": "Clone Robotics humanoid robot news 2025",                        "category": "HUMANOID",   "tag": "Clone Robotics"},
    {"q": "Mentee Robotics humanoid navigation manipulation 2025",           "category": "HUMANOID",   "tag": "Mentee Robotics"},
    {"q": "Persona AI humanoid robot news 2025",                            "category": "HUMANOID",   "tag": "Persona AI"},
    # China / Asia companies
    {"q": "Unitree Robotics H1 G1 humanoid robot 2025",                     "category": "HUMANOID",   "tag": "Unitree Robotics"},
    {"q": "UBTECH Walker humanoid robot enterprise commercial 2025",         "category": "HUMANOID",   "tag": "UBTECH"},
    {"q": "Xiaomi CyberOne humanoid robot update 2025",                      "category": "HUMANOID",   "tag": "Xiaomi"},
    {"q": "Fourier Intelligence GR-1 humanoid robot deployment 2025",        "category": "HUMANOID",   "tag": "Fourier Intelligence"},
    {"q": "Astribot S1 humanoid robot dexterous 2025",                      "category": "HUMANOID",   "tag": "Astribot"},
    {"q": "Kepler humanoid robot deployment factory 2025",                  "category": "HUMANOID",   "tag": "Kepler Robotics"},
    {"q": "EX Robots humanoid industrial deployment 2025",                  "category": "HUMANOID",   "tag": "EX Robots"},
    {"q": "Rainbow Robotics RB-Y1 humanoid Samsung 2025",                   "category": "HUMANOID",   "tag": "Rainbow Robotics"},
    # Market-wide humanoid themes
    {"q": "humanoid robot factory labor shortage deployment 2025",           "category": "HUMANOID",   "tag": "Factory Deployment"},
    {"q": "humanoid robot funding investment valuation 2025",               "category": "HUMANOID",   "tag": "Humanoid Funding"},
    {"q": "humanoid robot commercial order contract deployment",             "category": "HUMANOID",   "tag": "Commercial Deals"},
    {"q": "China humanoid robot government policy production 2025",          "category": "HUMANOID",   "tag": "China Humanoid Race"},
    {"q": "humanoid robot unit cost production economics 2025",             "category": "HUMANOID",   "tag": "Unit Economics"},

    # ── Competitor Landscape ────────────────────────────────────────────────
    # Hospitality service robots
    {"q": "Bear Robotics Servi restaurant server robot news 2025",           "category": "COMPETITOR", "tag": "Bear Robotics"},
    {"q": "Pudu Robotics BellaBot KettyBot hotel restaurant deployment",     "category": "COMPETITOR", "tag": "Pudu Robotics"},
    {"q": "Keenon Robotics T9 W3 hotel restaurant robot deployment",         "category": "COMPETITOR", "tag": "Keenon Robotics"},
    {"q": "Savioke Relay hotel delivery robot deployment 2025",              "category": "COMPETITOR", "tag": "Savioke"},
    {"q": "Aethon TUG hospital robot deployment 2025",                       "category": "COMPETITOR", "tag": "Aethon TUG"},
    {"q": "Diligent Robotics Moxi hospital robot news 2025",                 "category": "COMPETITOR", "tag": "Diligent Robotics"},
    {"q": "Cobalt Robotics security robot deployment contract 2025",         "category": "COMPETITOR", "tag": "Cobalt Robotics"},
    {"q": "Maidbot ROSIE hotel cleaning robot 2025",                        "category": "COMPETITOR", "tag": "Maidbot"},
    {"q": "Avidbots Neo floor scrubbing robot deployment 2025",              "category": "COMPETITOR", "tag": "Avidbots"},
    # Logistics / warehouse AMR competitors
    {"q": "Locus Robotics AMR warehouse deployment partner 2025",            "category": "COMPETITOR", "tag": "Locus Robotics"},
    {"q": "Mobile Industrial Robots MiR AMR deployment expansion",           "category": "COMPETITOR", "tag": "MiR"},
    {"q": "OTTO Motors AMR factory warehouse deployment 2025",               "category": "COMPETITOR", "tag": "OTTO Motors"},
    {"q": "Geekplus AMR goods-to-person robot deployment 2025",              "category": "COMPETITOR", "tag": "Geekplus"},
    {"q": "Hai Robotics HAIO autonomous case-handling robot 2025",           "category": "COMPETITOR", "tag": "Hai Robotics"},
    {"q": "ForwardX AMR logistics autonomous picking robot 2025",            "category": "COMPETITOR", "tag": "ForwardX"},
    {"q": "Zebra Technologies Fetch Robotics AMR deployment news 2025",      "category": "COMPETITOR", "tag": "Zebra / Fetch"},
    {"q": "service robot hospitality logistics new contract 2025",           "category": "COMPETITOR", "tag": "Contract News"},

    # ── Market Signals ───────────────────────────────────────────────────────
    {"q": "Richtech Robotics news product partnership launch 2025",          "category": "MARKET",     "tag": "Richtech Press"},
    {"q": "robotics startup funding round Series A B C 2025",               "category": "MARKET",     "tag": "Robotics Funding"},
    {"q": "warehouse automation investment deal funding 2025",               "category": "MARKET",     "tag": "Warehouse Automation"},
    {"q": "logistics robot AMR investment deal 2025",                        "category": "MARKET",     "tag": "Logistics Robots"},
    {"q": "autonomous mobile robot market size forecast 2025 2030",          "category": "MARKET",     "tag": "AMR Market"},
    {"q": "robotics as a service RaaS contract enterprise deal",             "category": "MARKET",     "tag": "RaaS"},
    {"q": "Fortune 500 robot deployment pilot program 2025",                 "category": "MARKET",     "tag": "Enterprise Adoption"},
    {"q": "robotics IPO public offering listing 2025",                       "category": "MARKET",     "tag": "Robotics IPO"},
    {"q": "robot deployment ROI payback case study 2025",                    "category": "MARKET",     "tag": "ROI Evidence"},
    {"q": "hotel chain resort robot pilot deployment contract 2025",         "category": "MARKET",     "tag": "Hospitality Deals"},

    # ── Industry Trends ──────────────────────────────────────────────────────
    {"q": "labor shortage hospitality hotel restaurant 2025",                "category": "INDUSTRY",   "tag": "Hospitality Labor"},
    {"q": "warehouse distribution center labor shortage automation 2025",    "category": "INDUSTRY",   "tag": "Warehouse Labor"},
    {"q": "restaurant food service labor turnover automation 2025",          "category": "INDUSTRY",   "tag": "Food Service Labor"},
    {"q": "healthcare hospital robot supply delivery nursing shortage",      "category": "INDUSTRY",   "tag": "Healthcare Robots"},
    {"q": "senior living care facility robot pilot staffing 2025",           "category": "INDUSTRY",   "tag": "Senior Living"},
    {"q": "casino resort hotel robot guest experience deployment",           "category": "INDUSTRY",   "tag": "Gaming & Hospitality"},
    {"q": "airport terminal robot deployment passenger services 2025",       "category": "INDUSTRY",   "tag": "Airport"},
    {"q": "retail store robot inventory shelf scanning 2025",                "category": "INDUSTRY",   "tag": "Retail"},
    {"q": "automotive factory assembly robot cobot deployment 2025",         "category": "INDUSTRY",   "tag": "Auto Manufacturing"},
    {"q": "minimum wage increase labor cost automation robot 2025",          "category": "INDUSTRY",   "tag": "Wage Pressure"},

    # ── Partner & Tech Ecosystem ─────────────────────────────────────────────
    {"q": "NVIDIA Isaac ROS GR00T robotics platform partnership 2025",       "category": "PARTNER",    "tag": "NVIDIA"},
    {"q": "Microsoft Azure AI robotics integration partner 2025",            "category": "PARTNER",    "tag": "Microsoft"},
    {"q": "Apple robotics home assistant project news 2025",                 "category": "PARTNER",    "tag": "Apple"},
    {"q": "AWS Amazon robotics cloud integration 2025",                      "category": "PARTNER",    "tag": "Amazon / AWS"},
    {"q": "Qualcomm Snapdragon robotics edge AI platform 2025",              "category": "PARTNER",    "tag": "Qualcomm"},
    {"q": "robot fleet management software platform integration 2025",       "category": "PARTNER",    "tag": "Fleet Software"},
    {"q": "ROS2 robot operating system industrial deployment 2025",          "category": "PARTNER",    "tag": "ROS Ecosystem"},

    # ── VLA & Foundation Models ───────────────────────────────────────────────
    # Google VLA / robotics research
    {"q": "Google DeepMind Gemini Robotics demo release 2025 2026",              "category": "FOUNDATION", "tag": "Google Gemini Robotics"},
    {"q": "Google DeepMind robot AI model training manipulation",                "category": "FOUNDATION", "tag": "Google DeepMind"},
    {"q": "Google RT-2 RT-X robotic transformer model announcement",             "category": "FOUNDATION", "tag": "Google RT-X"},
    {"q": "Google robot learning foundation model breakthrough news",             "category": "FOUNDATION", "tag": "Google Research"},
    # Industry lab announcements
    {"q": "Physical Intelligence pi zero pi one robot policy release demo",       "category": "FOUNDATION", "tag": "Physical Intelligence"},
    {"q": "NVIDIA GR00T robot AI model training release 2025",                   "category": "FOUNDATION", "tag": "NVIDIA GR00T"},
    {"q": "Hugging Face LeRobot open source robot training model 2025",          "category": "FOUNDATION", "tag": "HuggingFace LeRobot"},
    {"q": "OpenAI robots embodied AI research model 2025 2026",                  "category": "FOUNDATION", "tag": "OpenAI Robotics"},
    {"q": "Meta AI robot learning research model announcement",                  "category": "FOUNDATION", "tag": "Meta Robotics"},
    {"q": "Microsoft robot AI model manipulation research 2025",                 "category": "FOUNDATION", "tag": "Microsoft Research"},
    {"q": "Amazon Robotics AI foundation model announcement 2025",               "category": "FOUNDATION", "tag": "Amazon Robotics"},
    # Conference and research coverage
    {"q": "ICRA 2025 robotics conference robot learning AI",                     "category": "FOUNDATION", "tag": "ICRA 2025"},
    {"q": "CoRL 2025 conference robot learning paper",                          "category": "FOUNDATION", "tag": "CoRL 2025"},
    {"q": "NeurIPS ICLR robot learning foundation model paper 2025",             "category": "FOUNDATION", "tag": "ML Conferences"},
    {"q": "IEEE Spectrum robot AI learning model news 2025 2026",                "category": "FOUNDATION", "tag": "IEEE Spectrum"},
    # University lab news coverage
    {"q": "Stanford robotics robot AI demo research news 2025",                  "category": "FOUNDATION", "tag": "Stanford"},
    {"q": "MIT CSAIL robot learning AI research demo 2025",                      "category": "FOUNDATION", "tag": "MIT"},
    {"q": "Berkeley robot learning AI research breakthrough 2025",               "category": "FOUNDATION", "tag": "UC Berkeley"},
    {"q": "CMU Carnegie Mellon robot AI learning research 2025",                 "category": "FOUNDATION", "tag": "CMU"},
    {"q": "ETH Zurich robot locomotion learning AI research 2025",               "category": "FOUNDATION", "tag": "ETH Zurich"},
    {"q": "Tsinghua University robot AI humanoid learning research 2025",         "category": "FOUNDATION", "tag": "Tsinghua"},
    # Concept / technique news
    {"q": "vision language action robot model demo release",                     "category": "FOUNDATION", "tag": "VLA Research"},
    {"q": "robot foundation model training demo commercial 2025",                 "category": "FOUNDATION", "tag": "Foundation Models"},
    {"q": "robot imitation learning demonstration policy model",                  "category": "FOUNDATION", "tag": "Imitation Learning"},
    {"q": "embodied AI robot world model simulation training 2025",               "category": "FOUNDATION", "tag": "World Models"},
    {"q": "humanoid robot AI model dexterous manipulation research",              "category": "FOUNDATION", "tag": "Dexterous Robots"},
    {"q": "robot reinforcement learning sim-to-real transfer 2025",               "category": "FOUNDATION", "tag": "Sim-to-Real"},
    {"q": "generalist robot AI policy zero-shot transfer breakthrough",           "category": "FOUNDATION", "tag": "Generalist Policy"},
]

CATEGORY_LABELS = {
    "MA_WATCH":   "M&A Watch",
    "HUMANOID":   "Humanoid Market",
    "COMPETITOR": "Competitor Landscape",
    "MARKET":     "Market Signals",
    "INDUSTRY":   "Industry Trends",
    "PARTNER":    "Partner & Tech Ecosystem",
    "FOUNDATION": "VLA & Foundation Models",
}


# ── DB helpers ──────────────────────────────────────────────────────────────

# DDL is split into individual statements because SQLAlchemy text() only
# executes the first statement in a multi-statement string.
_DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS intelligence_items (
        id              SERIAL      PRIMARY KEY,
        guid            TEXT        UNIQUE NOT NULL,
        title           TEXT        NOT NULL,
        summary         TEXT,
        source_url      TEXT,
        source_name     TEXT,
        category        TEXT        NOT NULL,
        tag             TEXT,
        relevance_score INTEGER     DEFAULT 0,
        pub_date        TIMESTAMPTZ,
        fetched_at      TIMESTAMPTZ DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_intelligence_category  ON intelligence_items(category)",
    "CREATE INDEX IF NOT EXISTS ix_intelligence_fetched   ON intelligence_items(fetched_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_intelligence_relevance ON intelligence_items(category, relevance_score DESC)",
    # Migration-safe: add column if the table already existed without it
    "ALTER TABLE intelligence_items ADD COLUMN IF NOT EXISTS relevance_score INTEGER DEFAULT 0",
    # Daily briefing summaries table
    """
    CREATE TABLE IF NOT EXISTS intelligence_summaries (
        id            SERIAL       PRIMARY KEY,
        summary_date  DATE         UNIQUE NOT NULL,
        summary_json  JSONB        NOT NULL,
        generated_at  TIMESTAMPTZ  DEFAULT now()
    )
    """,
]


def _ensure_table():
    with engine.begin() as conn:
        for stmt in _DDL_STATEMENTS:
            try:
                conn.execute(text(stmt))
            except Exception as exc:
                logger.warning("[intelligence] DDL stmt skipped (%s): %s", exc.__class__.__name__, stmt[:60])


def _guid(url: str, title: str) -> str:
    return hashlib.md5(f"{url}|{title}".encode()).hexdigest()


# ── RSS fetch ───────────────────────────────────────────────────────────────

def _fetch_rss(query: str) -> list[dict]:
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        r = requests.get(url, headers=RSS_HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as exc:
        logger.warning("[intelligence] RSS fetch failed for %r: %s", query, exc)
        return []

    items = []
    try:
        root = ET.fromstring(r.text)
        channel = root.find("channel")
        if channel is None:
            return []
        for item in channel.findall("item"):
            title   = (item.findtext("title") or "").strip()
            link    = (item.findtext("link")  or "").strip()
            summary = (item.findtext("description") or "").strip()
            pub_raw = (item.findtext("pubDate") or "").strip()
            source  = item.find("source")
            source_name = source.text.strip() if source is not None and source.text else ""

            if not title or not link:
                continue

            # Parse pub_date
            pub_date = None
            if pub_raw:
                for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
                    try:
                        pub_date = datetime.strptime(pub_raw, fmt).replace(tzinfo=timezone.utc)
                        break
                    except ValueError:
                        pass

            items.append({
                "title":       title,
                "link":        link,
                "summary":     summary,
                "source_name": source_name,
                "pub_date":    pub_date,
            })
    except ET.ParseError as exc:
        logger.warning("[intelligence] XML parse error: %s", exc)

    return items


# ── Relevance scoring ───────────────────────────────────────────────────────

RELEVANCE_BOOSTS = {
    "MA_WATCH":   ["acqui", "merger", "buy", "invest", "fund", "deal", "partner", "acqui-hire"],
    "HUMANOID":   ["humanoid", "deploy", "commerci", "labor", "plant", "factor", "bipedal", "production", "order"],
    "COMPETITOR": ["deploy", "launch", "contract", "hotel", "restaurant", "warehouse", "partner", "install"],
    "MARKET":     ["fund", "million", "billion", "series", "invest", "deal", "growth", "forecast", "market"],
    "INDUSTRY":   ["shortage", "automat", "robot", "staffing", "labor", "cost", "turnover", "wage"],
    "PARTNER":    ["partner", "integrat", "launch", "platform", "sdk", "robot", "ecosystem", "api"],
    "FOUNDATION": ["vla", "foundation model", "locomot", "policy", "transfer", "embodied", "generaliz",
                    "diffusion policy", "manipulation", "dexterous", "vision language action", "rt-2", "rt-x",
                    "gemini robotics", "gr00t", "lerobot", "openvla", "aloha", "cross-embodiment",
                    "robot learning", "imitation learning", "reinforcement learning", "robot transformer",
                    "robot", "robotic", "deepmind", "ai model", "neural", "deep learning",
                    "language model", "autonomous", "perception", "dexterity", "manipulation",
                    "llm", "multimodal", "pretraining", "fine-tun", "benchmark", "simulation"],
}

# Titles that are generic aggregators / listicles, not actual company-specific news
JUNK_TITLE_FRAGMENTS = [
    "top 10", "top 5", "top 20", "best robot", "list of robot",
    "everything you need to know", "what you need to know",
    "how to invest", "stocks to buy", "etf", "stock market",
    "quiz", "crossword", "horoscope",
    "technology trends", "tech trends", "predictions for", "trends to watch",
]

def _is_junk_title(title: str) -> bool:
    t = title.lower()
    return any(frag in t for frag in JUNK_TITLE_FRAGMENTS)

def _relevance(title: str, summary: str, category: str) -> int:
    text_lower = (title + " " + summary).lower()
    boosts = RELEVANCE_BOOSTS.get(category, [])
    score = sum(1 for word in boosts if word in text_lower)
    # Extra boost for direct robotics / core topic words
    if any(w in text_lower for w in ["robot", "automat", "humanoid", "amr", "bipedal"]):
        score += 2
    # Boost for recency signals in title
    if any(yr in title for yr in ["2025", "2026"]):
        score += 1
    return min(score, 10)

# Minimum relevance score required to store an item (per category)
# FOUNDATION uses 1 because the queries are already highly targeted academic/research searches
_MIN_RELEVANCE: dict[str, int] = {
    "MA_WATCH":   2,
    "HUMANOID":   2,
    "COMPETITOR": 2,
    "MARKET":     2,
    "INDUSTRY":   2,
    "PARTNER":    2,
    "FOUNDATION": 1,
}


# ── Main scraper function ───────────────────────────────────────────────────

def run_intelligence_scraper() -> dict:
    """
    Fetch all intelligence queries, deduplicate by GUID, and persist.
    Returns a summary dict with counts per category.
    """
    _ensure_table()
    db = SessionLocal()

    # Cutoff: ignore items older than 14 days (FOUNDATION uses 60 days — research news is slower)
    cutoff_default = datetime.now(timezone.utc) - timedelta(days=14)
    cutoff_foundation = datetime.now(timezone.utc) - timedelta(days=60)

    summary: dict[str, int] = {cat: 0 for cat in CATEGORY_LABELS}
    total_new = 0
    total_seen = 0

    try:
        for entry in INTELLIGENCE_QUERIES:
            q        = entry["q"]
            category = entry["category"]
            tag      = entry["tag"]

            items = _fetch_rss(q)
            cutoff = cutoff_foundation if category == "FOUNDATION" else cutoff_default
            for item in items:
                # Skip old items
                if item["pub_date"] and item["pub_date"] < cutoff:
                    continue

                # Skip junk / generic aggregator headlines
                if _is_junk_title(item["title"]):
                    continue

                relevance = _relevance(item["title"], item["summary"], category)

                # Skip completely off-topic results (threshold is category-aware)
                min_score = _MIN_RELEVANCE.get(category, 2)
                if relevance < min_score:
                    continue

                guid = _guid(item["link"], item["title"])

                # Dedup check
                exists = db.execute(
                    text("SELECT 1 FROM intelligence_items WHERE guid = :g"),
                    {"g": guid}
                ).fetchone()
                if exists:
                    total_seen += 1
                    continue

                db.execute(text("""
                    INSERT INTO intelligence_items
                        (guid, title, summary, source_url, source_name,
                         category, tag, relevance_score, pub_date)
                    VALUES
                        (:guid, :title, :summary, :source_url, :source_name,
                         :category, :tag, :relevance_score, :pub_date)
                    ON CONFLICT (guid) DO NOTHING
                """), {
                    "guid":            guid,
                    "title":           item["title"][:500],
                    "summary":         (item["summary"] or "")[:1000],
                    "source_url":      item["link"][:800],
                    "source_name":     (item["source_name"] or "")[:200],
                    "category":        category,
                    "tag":             tag,
                    "relevance_score": relevance,
                    "pub_date":        item["pub_date"],
                })
                db.commit()
                summary[category] = summary.get(category, 0) + 1
                total_new += 1

    except Exception as exc:
        logger.error("[intelligence] scraper error: %s", exc)
        db.rollback()
    finally:
        db.close()

    logger.info(
        "[intelligence] done — %d new items, %d already seen. breakdown: %s",
        total_new, total_seen, summary
    )

    # Generate (or refresh) the daily briefing summary now that we have fresh data
    try:
        from app.services.intelligence_summary import generate_daily_summary
        summary_db = SessionLocal()
        try:
            generate_daily_summary(summary_db, new_count=total_new)
        finally:
            summary_db.close()
    except Exception as exc:
        logger.warning("[intelligence] daily summary generation skipped: %s", exc)

    return {"new": total_new, "seen": total_seen, "by_category": summary}
