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
CANDIDATES: dict[str, tuple[str, list[str]]] = {
    # confirmed via web search
    "neura-maira": ("https://neura-robotics.com/products/maira/", ["maira"]),
    "pal-ari": ("https://pal-robotics.com/robot/ari/", ["ari"]),
    "toyota-punyo": ("https://punyo.tech/", ["punyo"]),
    "pndbotics-adam": ("https://wiki.pndbotics.com/en/robot/humanoid_robot/", ["adam"]),
    "pndbotics-adam-u": ("https://pndbotics.com/", ["adam", "pnd"]),
    "galbot-g1": ("https://www.galbot.com/", ["galbot"]),
    "galbot-g2": ("https://www.galbot.com/", ["galbot"]),
    # high-confidence vendor/product pages (validated by fetch)
    "clone-alpha": ("https://clonerobotics.com/", ["clone"]),
    "engineered-arts-mesmer": ("https://engineeredarts.com/robot/mesmer/", ["mesmer"]),
    "mentee-bot-pro": ("https://www.menteebot.com/", ["mentee"]),
    "reflex-gen2": ("https://reflexrobotics.com/", ["reflex"]),
    "shadow-hand-platform": ("https://www.shadowrobot.com/dexterous-hand-series/", ["shadow", "hand"]),
    "kawasaki-kaleido": ("https://kawasakirobotics.com/", ["kawasaki"]),
    "leju-kuavo-3": ("https://www.lejurobotics.com/", ["leju", "kuavo"]),
    "segway-humanoid": ("https://robotics.segway.com/", ["segway"]),
    "apptronik-a2": ("https://apptronik.com/", ["apptronik"]),
    "realman-humanoid": ("https://www.realman-robotics.com/", ["realman"]),
    "noetix-n2": ("https://www.noetixrobotics.com/", ["noetix"]),
    "noetix-e1": ("https://www.noetixrobotics.com/", ["noetix"]),
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
