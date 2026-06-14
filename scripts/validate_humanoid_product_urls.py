"""
Validate candidate product URLs for humanoid_benchmarks rows that lack one.

For each (slug, candidate_url, must_match terms), fetch the page and confirm it
is live AND mentions the robot/vendor (so we don't seed a dead or wrong-product
link). Prints PASS/FAIL. PASS rows are safe to add to HUMANOID_CATALOG.

Usage: python scripts/validate_humanoid_product_urls.py
"""
from __future__ import annotations

import re
import sys

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# slug -> (url, [terms that must appear in page text, any-of])
# Round 2: user-supplied URLs (utm params stripped)
CANDIDATES: dict[str, tuple[str, list[str]]] = {
    "galbot-g1": ("https://www.galbot.com", ["galbot"]),
    "galbot-g2": ("https://www.galbot.com", ["galbot"]),
    "pndbotics-adam-u": ("https://wiki.pndbotics.com/en/robot/humanoid_robot/", ["adam", "pnd"]),
    "mentee-bot-pro": ("https://www.menteebot.com", ["mentee"]),
    "noetix-n2": ("https://www.noetix.ai", ["noetix"]),
    "noetix-e1": ("https://www.noetix.ai", ["noetix"]),
    "leju-kuavo-3": ("https://www.lejurobot.com", ["leju", "kuavo"]),
    "engineered-arts-mesmer": ("https://engineeredarts.co.uk/robot/mesmer/", ["mesmer"]),
    "chery-mornine": ("https://www.cheryinternational.com", ["chery"]),
    "estun-codroid": ("https://www.estun.com", ["estun"]),
    "seer-humanoid": ("https://www.seer-robotics.ai", ["seer"]),
    "syrius-humanoid": ("https://www.syriusrobotics.com", ["syrius"]),
    "pangolin-humanoid": ("https://www.pangolin-robot.com", ["pangolin"]),
    "xiaomi-cyberone-pro": ("https://www.mi.com/global/discover/article?id=1911", ["cyberone"]),
    "nasa-valkyrie": ("https://www.nasa.gov/technology/r5/", ["valkyrie", "r5"]),
    "dlr-toro": ("https://www.dlr.de/en/rm/research/expertise/robots-systems/humanoid-robots/toro", ["toro"]),
    "dlr-justin": ("https://www.dlr.de/en/rm/research/expertise/robots-systems/humanoid-robots/rollin-justin", ["justin"]),
    "honda-avatar": ("https://global.honda/en/innovation/avatarrobotics/", ["avatar"]),
    "samsung-bot-handy": ("https://research.samsung.com/artificial-intelligence/robotics", ["robot"]),
    "lg-cloi-suitbot": ("https://www.lg.com/global/business/cloi", ["cloi"]),
    "softbank-pepper-next": ("https://www.softbankrobotics.com/emea/en/pepper", ["pepper"]),
    "cloudminds-ginger-xr": ("https://www.cloudminds.com", ["cloudminds", "ginger"]),
}


def fetch_text(url: str) -> tuple[int, str]:
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15, allow_redirects=True)
        html = re.sub(r"(?is)<(script|style|noscript|svg|head).*?</\1>", " ", r.text)
        text = re.sub(r"(?s)<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
        return r.status_code, text
    except Exception as exc:
        return 0, f"ERR {type(exc).__name__}: {exc}"


def main() -> None:
    print(f"Validating {len(CANDIDATES)} candidate product URLs...\n")
    passed: dict[str, str] = {}
    for slug, (url, terms) in CANDIDATES.items():
        code, text = fetch_text(url)
        low = text.lower()
        hit = [t for t in terms if t.lower() in low]
        ok = code == 200 and bool(hit) and len(text) > 300
        status = "PASS" if ok else "FAIL"
        why = ""
        if code != 200:
            why = f"http {code}"
        elif not hit:
            why = f"no term match ({terms})"
        elif len(text) <= 300:
            why = f"thin page ({len(text)} chars — likely JS-only)"
        print(f"  [{status}] {slug:26s} {url}  {('matched ' + ','.join(hit)) if ok else why}")
        if ok:
            passed[slug] = url
    print(f"\n{len(passed)}/{len(CANDIDATES)} passed. Catalog-ready entries:")
    for slug, url in passed.items():
        print(f'    "{slug}": "{url}",')


if __name__ == "__main__":
    main()
