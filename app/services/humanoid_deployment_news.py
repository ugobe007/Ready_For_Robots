"""
Scan Google News RSS (English + Chinese) for humanoid deployment / trial evidence.

Chinese headlines are classified with native keywords and optionally translated to English
via the configured LLM for storage and reporting.
"""
from __future__ import annotations

import json
import logging
import re
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS_EN = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
GOOGLE_NEWS_RSS_ZH = "https://news.google.com/rss/search?q={query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    )
}

_PUBLISHER_SUFFIX = re.compile(r"\s+[-–—|]\s+[^-–—|]{2,80}$")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

DEPLOYMENT_SIGNAL_RE = re.compile(
    r"\b("
    r"deploy(?:ed|ment|s|ing)?|"
    r"roll(?:ed|s|ing)?\s+out|"
    r"commercial(?:ly| rollout)?|"
    r"production (?:floor|line|facility|use)|"
    r"installed (?:at|in)|"
    r"fleet of|"
    r"ships? to customers?|"
    r"warehouse (?:automation|deployment)|"
    r"factory (?:floor|deployment|pilot)|"
    r"goes live|"
    r"operational (?:at|in)"
    r")\b",
    re.I,
)

TRIAL_SIGNAL_RE = re.compile(
    r"\b("
    r"pilot(?:ing|s| program)?|"
    r"trial|"
    r"proof of concept|\bPoC\b|"
    r"customer trial|"
    r"field test|"
    r"beta (?:test|program)|"
    r"test(?:ing)? (?:at|in|with)|"
    r"partnership (?:with|to deploy)|"
    r"collaborat(?:e|ion) (?:with|on)"
    r")\b",
    re.I,
)

HUMANOID_RE = re.compile(
    r"\b(humanoid|biped(?:al)?|android robot|general.?purpose robot|"
    r"human.?shaped robot|anthropomorphic robot|robot worker)\b",
    re.I,
)

# Chinese deployment / trial / humanoid signals
CN_DEPLOYMENT_RE = re.compile(
    r"(部署|落地|量产|商用|交付|出厂|投产|上岗|进厂|入驻|规模化|批量生产|正式应用|实现应用)"
)
CN_TRIAL_RE = re.compile(
    r"(试点|试用|验证|合作|签约|战略协议|首发|亮相|发布|测试|演示|实训|示范|订单)"
)
CN_HUMANOID_RE = re.compile(r"(人形机器人|人形机器|人形|仿生机器人|具身智能|通用机器人)")

KNOWN_CUSTOMERS = (
    "BMW", "Mercedes-Benz", "Mercedes Benz", "Amazon", "GXO", "Schaeffler",
    "Hyundai", "Samsung", "Foxconn", "Boeing", "Airbus", "UPS", "FedEx",
    "Toyota", "Honda", "Nvidia", "Microsoft", "Meta",
    "Mercedes-Benz Manufacturing", "BMW Group", "GXO Logistics",
    "丰田", "宝马", "奔驰", "比亚迪", "华为", "小米", "京东", "宁德时代",
)

# English vendor → Chinese search aliases (news / press)
VENDOR_ZH_ALIASES: Dict[str, List[str]] = {
    "Unitree Robotics": ["宇树科技", "宇树"],
    "Agibot (Zhiyuan Robotics)": ["智元机器人", "智元"],
    "UBTECH Robotics": ["优必选"],
    "EngineAI": ["众擎机器人", "众擎"],
    "Deep Robotics": ["云深处科技", "云深处"],
    "Fourier Robotics": ["傅利叶智能", "傅利叶"],
    "Robotera (星动纪元)": ["星动纪元"],
    "Leju Robotics": ["乐聚机器人", "乐聚"],
    "Kepler": ["开普勒机器人", "开普勒"],
    "XPeng Robotics": ["小鹏机器人", "小鹏"],
    "Astribot": ["星尘智能", "Astribot"],
    "Galbot": ["银河通用", "Galbot"],
    "LimX Dynamics": ["逐际动力", "LimX"],
    "Booster Robotics": ["加速进化"],
    "EngineAI": ["众擎"],
    "Matrix Robotics": ["矩阵超智"],
    "Lanxin Technology": ["蓝芯科技"],
    "Estun Automation": ["埃斯顿"],
    "Siasun": ["新松"],
    "CloudMinds": ["达闼科技", "达闼"],
    "Realman Robotics": ["睿尔曼"],
    "PNDbotics": ["帕西尼", "PNDbotics"],
}


def _ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _strip_title(title: str) -> str:
    return _PUBLISHER_SUFFIX.sub("", (title or "").strip()).strip()


def _has_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text or ""))


def fetch_news_rss(
    query: str,
    *,
    max_items: int = 6,
    locale: str = "en",
) -> List[dict]:
    template = GOOGLE_NEWS_RSS_ZH if locale == "zh" else GOOGLE_NEWS_RSS_EN
    url = template.format(query=urllib.parse.quote(query))
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=14, context=_ssl_context()) as resp:
            root = ET.fromstring(resp.read())
    except Exception as exc:
        logger.warning("RSS fetch failed (%s) for %r: %s", locale, query[:80], exc)
        return []

    items = []
    for item in root.findall(".//item")[:max_items]:
        title = _strip_title(item.findtext("title") or "")
        link = item.findtext("link") or ""
        desc = item.findtext("description") or ""
        if title:
            items.append({
                "title": title,
                "url": link,
                "description": desc,
                "query": query,
                "locale": locale,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            })
    return items


def translate_headlines(articles: List[dict], *, max_titles: int = 40) -> int:
    """
    Translate Chinese headlines to English via LLM (batch).
    Sets ``title_en`` on each article dict. Returns count translated.
    """
    pending = [
        a for a in articles
        if _has_cjk(a.get("title", "")) and not a.get("title_en")
    ][:max_titles]
    if not pending:
        return 0

    try:
        from app.services.llm_client import llm_json_completion
    except ImportError:
        return 0

    lines = "\n".join(f'{i}. {a["title"]}' for i, a in enumerate(pending))
    raw = llm_json_completion(
        "You translate robotics news headlines from Chinese to English. "
        "Return ONLY valid JSON: {\"translations\": [\"...\", ...]} with one English string per numbered line, same order.",
        f"Translate these headlines to concise English:\n{lines}",
        max_tokens=1200,
        temperature=0.1,
    )
    if not raw:
        return 0

    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        parsed = json.loads(match.group() if match else raw)
        translations = parsed.get("translations") or []
    except (json.JSONDecodeError, AttributeError):
        logger.warning("Headline translation JSON parse failed")
        return 0

    translated = 0
    for art, en in zip(pending, translations):
        en_text = str(en).strip()
        if en_text:
            art["title_en"] = en_text
            translated += 1
    return translated


def _article_blob(article: dict) -> str:
    parts = [
        article.get("title") or "",
        article.get("title_en") or "",
        article.get("description") or "",
    ]
    return " ".join(p for p in parts if p)


def _robot_search_terms(name: str, vendor: str) -> List[str]:
    terms = []
    vendor_short = vendor.split("(")[0].strip()
    if vendor_short:
        terms.append(vendor_short.lower())
    for zh in VENDOR_ZH_ALIASES.get(vendor, []):
        terms.append(zh)
    name_lower = (name or "").lower()
    for token in re.split(r"[\s\-–]+", name):
        t = token.strip()
        if len(t) >= 2 and t not in ("humanoid", "robot", "series", "gen", "the"):
            terms.append(t.lower())
    if "digit" in name_lower:
        terms.append("digit")
    if "apollo" in name_lower:
        terms.append("apollo")
    if "figure" in name_lower:
        terms.append("figure")
    if "optimus" in name_lower:
        terms.append("optimus")
    if "walker" in name_lower:
        terms.append("walker")
    if "g1" in name_lower.split():
        terms.append("g1")
    return list(dict.fromkeys(terms))


def article_matches_robot(
    article: dict,
    name: str,
    vendor: str,
    *,
    vendor_scope: bool = False,
) -> bool:
    blob = _article_blob(article).lower()
    blob_raw = _article_blob(article)
    vendor_short = vendor.split("(")[0].strip().lower()
    zh_names = VENDOR_ZH_ALIASES.get(vendor, [])

    if vendor_scope:
        vendor_hit = vendor_short and vendor_short in blob
        zh_hit = any(z in blob_raw for z in zh_names)
        humanoid_hit = HUMANOID_RE.search(blob) or CN_HUMANOID_RE.search(blob_raw)
        if (vendor_hit or zh_hit) and humanoid_hit:
            return True

    terms = _robot_search_terms(name, vendor)
    if not terms:
        return False
    vendor_hit = terms[0] in blob if terms else False
    zh_vendor_hit = any(z in blob_raw for z in zh_names)
    product_hits = sum(1 for t in terms[1:] if t.lower() in blob or t in blob_raw)
    if (vendor_hit or zh_vendor_hit) and (product_hits >= 1 or len(terms) == 1):
        return True
    if product_hits >= 2:
        return True
    strong = {"digit", "apollo", "figure", "optimus", "ameca", "phoenix", "atlas", "g1"}
    return any(t in strong and (t in blob or t in blob_raw.lower()) for t in terms)


def classify_article_evidence(article: dict) -> Tuple[str, List[str]]:
    blob = _article_blob(article)
    blob_lower = blob.lower()
    signals = []

    if DEPLOYMENT_SIGNAL_RE.search(blob) or CN_DEPLOYMENT_RE.search(blob):
        signals.append("deployment")
    if TRIAL_SIGNAL_RE.search(blob) or CN_TRIAL_RE.search(blob):
        signals.append("trial")

    customers = []
    for c in KNOWN_CUSTOMERS:
        if c.lower() not in blob_lower and c not in blob:
            continue
        if c == "Google" and "google news" in blob_lower:
            continue
        customers.append(c)
    if customers:
        signals.append(f"customer:{customers[0]}")

    if "deployment" in signals:
        return "deployment", signals
    if "trial" in signals or any(s.startswith("customer:") for s in signals):
        return "trial", signals
    if HUMANOID_RE.search(blob) or CN_HUMANOID_RE.search(blob):
        return "general", signals
    return "unrelated", signals


def news_evidence_level_from_sources(sources: List[dict]) -> str:
    """Best deployment-news evidence level stored on a robot row."""
    level = "none"
    for src in sources or []:
        if src.get("type") not in ("deployment_news", "deployment_news_zh"):
            continue
        el = src.get("evidence_level") or "general"
        level = _merge_evidence(level, el)
    return level


def _evidence_rank(level: str) -> int:
    return {"deployment": 3, "trial": 2, "general": 1, "unrelated": 0, "none": -1}.get(level, -1)


def _merge_evidence(current: str, new: str) -> str:
    return new if _evidence_rank(new) > _evidence_rank(current) else current


def _short_robot_query(name: str, vendor: str, *, locale: str = "en") -> Optional[str]:
    name = (name or "").strip()
    vendor_short = vendor.split("(")[0].strip()
    generic = re.match(r"^.+\s(Humanoid|Robot)$", name, re.I)
    if generic and len(name.split()) <= 3:
        return None
    parts = [p for p in re.split(r"\s+", name) if p]
    if len(parts) >= 2:
        model_part = parts[-1]
        if locale == "zh":
            zh_vendor = VENDOR_ZH_ALIASES.get(vendor, [vendor_short])[0]
            return f"{zh_vendor} {model_part} 人形机器人 部署 OR 试点 OR 量产"
        if len(model_part) >= 2:
            return f'"{vendor_short}" "{model_part}" humanoid pilot OR deployment OR trial'
    return None


def build_search_queries_for_robots(
    robots: List[dict],
    *,
    include_chinese: bool = True,
) -> List[Tuple[str, str, str, str]]:
    """Return (query, scope, key, locale)."""
    queries: List[Tuple[str, str, str, str]] = []
    seen: Set[str] = set()

    by_vendor: Dict[str, List[dict]] = defaultdict(list)
    for r in robots:
        by_vendor[r.get("vendor") or "Unknown"].append(r)

    for vendor in sorted(by_vendor.keys()):
        vendor_short = vendor.split("(")[0].strip()
        q_en = f'"{vendor_short}" humanoid robot deployment OR pilot OR trial 2025 2026'
        if q_en not in seen:
            seen.add(q_en)
            queries.append((q_en, "vendor", vendor, "en"))

        if include_chinese and (vendor in VENDOR_ZH_ALIASES or "China" in vendor):
            pass
        if include_chinese and vendor in VENDOR_ZH_ALIASES:
            zh_name = VENDOR_ZH_ALIASES[vendor][0]
            q_zh = f"{zh_name} 人形机器人 部署 OR 试点 OR 量产 OR 交付 2025 2026"
            if q_zh not in seen:
                seen.add(q_zh)
                queries.append((q_zh, "vendor", vendor, "zh"))

    for r in robots:
        for locale in (["en", "zh"] if include_chinese and r.get("vendor") in VENDOR_ZH_ALIASES else ["en"]):
            rq = _short_robot_query(r.get("name") or "", r.get("vendor") or "", locale=locale)
            if rq and rq not in seen:
                seen.add(rq)
                queries.append((rq, "robot", r.get("model_slug") or "", locale))

    return queries


def scan_humanoid_deployment_news(
    robots: List[dict],
    *,
    max_queries: Optional[int] = None,
    sleep_sec: float = 1.0,
    articles_per_query: int = 6,
    include_chinese: bool = True,
    translate_chinese: bool = True,
) -> dict:
    queries = build_search_queries_for_robots(robots, include_chinese=include_chinese)
    if max_queries is not None:
        queries = queries[:max_queries]

    by_vendor: Dict[str, List[dict]] = defaultdict(list)
    by_slug: Dict[str, dict] = {r["model_slug"]: r for r in robots if r.get("model_slug")}
    for r in robots:
        by_vendor[r.get("vendor") or "Unknown"].append(r)

    robot_evidence: Dict[str, dict] = {
        slug: {
            "model_slug": slug,
            "name": r.get("name"),
            "vendor": r.get("vendor"),
            "status": r.get("status"),
            "news_evidence_level": "none",
            "articles": [],
            "matched_signals": [],
            "named_customers": [],
        }
        for slug, r in by_slug.items()
    }

    global_articles: List[dict] = []
    seen_urls: Set[str] = set()
    stats = {
        "queries_run": 0,
        "queries_en": 0,
        "queries_zh": 0,
        "articles_fetched": 0,
        "articles_relevant": 0,
        "articles_deployment": 0,
        "articles_trial": 0,
        "articles_zh": 0,
        "headlines_translated": 0,
    }

    for query, scope, key, locale in queries:
        stats["queries_run"] += 1
        if locale == "zh":
            stats["queries_zh"] += 1
        else:
            stats["queries_en"] += 1

        batch = fetch_news_rss(query, max_items=articles_per_query, locale=locale)
        stats["articles_fetched"] += len(batch)
        if locale == "zh":
            stats["articles_zh"] += len(batch)

        if sleep_sec > 0:
            time.sleep(sleep_sec)

        if translate_chinese and locale == "zh" and batch:
            stats["headlines_translated"] += translate_headlines(batch)

        for art in batch:
            url = art.get("url") or ""
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)

            level, signals = classify_article_evidence(art)
            if level == "unrelated":
                continue

            stats["articles_relevant"] += 1
            if level == "deployment":
                stats["articles_deployment"] += 1
            elif level == "trial":
                stats["articles_trial"] += 1

            art_record = {
                **art,
                "evidence_level": level,
                "signals": signals,
                "scope": scope,
            }
            global_articles.append(art_record)

            targets: List[dict] = []
            if scope == "vendor":
                targets = by_vendor.get(key, [])
            elif scope == "robot" and key in by_slug:
                targets = [by_slug[key]]
            else:
                targets = robots

            for r in targets:
                slug = r.get("model_slug")
                if not slug or slug not in robot_evidence:
                    continue
                if not article_matches_robot(
                    art,
                    r.get("name") or "",
                    r.get("vendor") or "",
                    vendor_scope=(scope == "vendor"),
                ):
                    continue
                entry = robot_evidence[slug]
                entry["news_evidence_level"] = _merge_evidence(
                    entry["news_evidence_level"], level
                )
                entry["articles"].append(art_record)
                for s in signals:
                    if s.startswith("customer:"):
                        cust = s.split(":", 1)[1]
                        if cust not in entry["named_customers"]:
                            entry["named_customers"].append(cust)
                    elif s not in entry["matched_signals"]:
                        entry["matched_signals"].append(s)

    for entry in robot_evidence.values():
        seen = set()
        deduped = []
        for a in entry["articles"]:
            u = a.get("url") or a.get("title")
            if u in seen:
                continue
            seen.add(u)
            deduped.append(a)
        entry["articles"] = deduped[:8]

    evidence_counts = Counter(e["news_evidence_level"] for e in robot_evidence.values())
    vendor_with_news: Set[str] = set()
    vendor_with_trial_plus: Set[str] = set()
    for e in robot_evidence.values():
        if e["news_evidence_level"] != "none":
            vendor_with_news.add(e["vendor"])
        if e["news_evidence_level"] in ("trial", "deployment"):
            vendor_with_trial_plus.add(e["vendor"])

    robots_with_trial_plus = sum(
        1 for e in robot_evidence.values()
        if e["news_evidence_level"] in ("trial", "deployment")
    )
    robots_with_deployment = sum(
        1 for e in robot_evidence.values()
        if e["news_evidence_level"] == "deployment"
    )

    priority_vendors = [
        "Agility Robotics", "Figure AI", "Reflex Robotics", "Apptronik",
        "EngineAI", "Persona AI", "Sanctuary AI", "Unitree Robotics",
        "UBTECH Robotics", "Agibot (Zhiyuan Robotics)", "1X Technologies",
        "Boston Dynamics", "Neura Robotics", "Deep Robotics", "Fourier Robotics",
    ]
    priority_review = []
    for pv in priority_vendors:
        matches = [
            e for e in robot_evidence.values()
            if (e.get("vendor") or "").startswith(pv.split("(")[0].strip())
            or pv in (e.get("vendor") or "")
        ]
        if not matches:
            continue
        best = max(matches, key=lambda x: _evidence_rank(x["news_evidence_level"]))
        sample = best["articles"][0] if best["articles"] else {}
        priority_review.append({
            "vendor": pv,
            "best_evidence_level": best["news_evidence_level"],
            "example_robot": best["name"],
            "article_count": sum(len(m["articles"]) for m in matches),
            "named_customers": sorted({c for m in matches for c in m["named_customers"]}),
            "sample_headline": sample.get("title_en") or sample.get("title"),
            "sample_headline_zh": sample.get("title") if sample.get("locale") == "zh" else None,
        })

    total = len(robot_evidence)
    unique_vendors = len(by_vendor)

    findings = [
        f"{robots_with_trial_plus} of {total} robots ({round(100 * robots_with_trial_plus / total, 1)}%) "
        f"have trial or deployment signals in recent news (EN + ZH RSS)",
        f"{robots_with_deployment} of {total} ({round(100 * robots_with_deployment / total, 1)}%) "
        f"have explicit deployment language in headlines",
        f"{len(vendor_with_trial_plus)} of {unique_vendors} vendors show trial+ news "
        f"({len(vendor_with_news)} with any humanoid news match)",
        f"Scanned {stats['queries_en']} EN + {stats['queries_zh']} ZH queries → "
        f"{stats['articles_relevant']} relevant ({stats['articles_zh']} from Chinese RSS); "
        f"{stats['headlines_translated']} headlines translated",
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology": (
            "Google News RSS in English (US) and Chinese (CN). Chinese headlines classified with "
            "native deployment/trial keywords and translated to English via LLM when configured. "
            "Verify articles before citing."
        ),
        "stats": stats,
        "summary": {
            "total_robots": total,
            "unique_vendors": unique_vendors,
            "news_evidence_breakdown": dict(evidence_counts),
            "robots_with_trial_or_deployment_news": robots_with_trial_plus,
            "robots_with_deployment_news": robots_with_deployment,
            "vendors_with_trial_or_deployment_news": len(vendor_with_trial_plus),
            "vendors_with_any_news": len(vendor_with_news),
            "pct_robots_trial_plus": round(100 * robots_with_trial_plus / total, 1) if total else 0,
            "pct_vendors_trial_plus": round(100 * len(vendor_with_trial_plus) / unique_vendors, 1) if unique_vendors else 0,
        },
        "key_findings": findings,
        "priority_vendor_review": priority_review,
        "robots": sorted(
            robot_evidence.values(),
            key=lambda x: (_evidence_rank(x["news_evidence_level"]), len(x["articles"])),
            reverse=True,
        ),
        "top_articles": sorted(
            global_articles,
            key=lambda a: _evidence_rank(a.get("evidence_level", "none")),
            reverse=True,
        )[:25],
    }


def persist_deployment_news(db: Session, scan_result: dict) -> dict:
    updated = 0
    now = datetime.now(timezone.utc).isoformat()

    for entry in scan_result.get("robots") or []:
        if entry.get("news_evidence_level") == "none" and not entry.get("articles"):
            continue
        slug = entry.get("model_slug")
        if not slug:
            continue

        row = db.execute(
            text("SELECT sources FROM humanoid_benchmarks WHERE model_slug = :slug"),
            {"slug": slug},
        ).first()
        if not row:
            continue

        existing = list(row[0] or [])
        existing_urls = {s.get("url") for s in existing if s.get("url")}
        new_sources = []
        for art in entry.get("articles") or []:
            url = art.get("url")
            if url and url in existing_urls:
                continue
            src_type = "deployment_news_zh" if art.get("locale") == "zh" else "deployment_news"
            new_sources.append({
                "type": src_type,
                "url": url,
                "title": art.get("title"),
                "title_en": art.get("title_en"),
                "locale": art.get("locale", "en"),
                "evidence_level": art.get("evidence_level"),
                "signals": art.get("signals"),
                "query": art.get("query"),
                "scraped_at": art.get("scraped_at") or now,
            })

        if not new_sources:
            continue

        merged = existing + new_sources
        db.execute(
            text("""
                UPDATE humanoid_benchmarks
                SET sources = cast(:sources as jsonb),
                    last_scraped_at = :now,
                    updated_at = :now
                WHERE model_slug = :slug
            """),
            {"slug": slug, "sources": json.dumps(merged[-30:]), "now": datetime.now(timezone.utc)},
        )
        updated += 1

    db.commit()
    return {"robots_updated": updated}


def run_humanoid_deployment_news_review(
    db: Session,
    *,
    persist: bool = False,
    max_queries: Optional[int] = None,
    use_db: bool = True,
    include_chinese: bool = True,
    translate_chinese: bool = True,
) -> dict:
    if use_db:
        rows = db.execute(
            text("""
                SELECT name, vendor, model_slug, status, specs
                FROM humanoid_benchmarks
                WHERE score_total IS NOT NULL
                ORDER BY vendor, name
            """)
        ).mappings().all()
        robots = [dict(r) for r in rows]
    else:
        from app.services.humanoid_vendor_catalog import catalog_entries
        robots = catalog_entries()

    if not robots:
        return {"error": "no robots to scan"}

    result = scan_humanoid_deployment_news(
        robots,
        max_queries=max_queries,
        include_chinese=include_chinese,
        translate_chinese=translate_chinese,
    )
    if persist:
        result["persist"] = persist_deployment_news(db, result)
    return result
