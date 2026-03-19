#!/usr/bin/env python3
"""
Examine 'Other' (unknown) industry leads using the public API (no DB needed).
Fetches leads, filters to industry=Other, runs keyword/bigram analysis,
writes reports to reports/ for adjusting industry list.
"""
import json
import os
import re
import sys
from collections import Counter
from urllib.request import urlopen

API_BASE = os.environ.get("API_BASE", "https://ready-2-robot.fly.dev")
LEADS_URL = f"{API_BASE}/api/leads"
# API returns max 800 per request (candidate_limit cap)
LIMIT = 800


def fetch_leads():
    """Fetch leads (multiple pages by sort to get more coverage)."""
    out = []
    for sort in ("score", "signals", "name"):
        url = f"{LEADS_URL}?limit={LIMIT}&sort={sort}&exclude_junk=true"
        with urlopen(url, timeout=120) as r:
            data = json.load(r)
        out.extend(data)
    # Dedupe by id
    by_id = {c["id"]: c for c in out}
    return list(by_id.values())


def is_other(c):
    ind = (c.get("industry") or "").strip().lower()
    return ind in ("", "other", "unknown")


def strip_html(text):
    """Remove HTML tags and common entities for cleaner keyword analysis."""
    if not text:
        return ""
    # Remove tags
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&amp;|&lt;|&gt;|&quot;", " ", text)
    text = re.sub(r"https?://[^\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def word_freq(text_lower, min_len=4):
    stop = {
        "that", "this", "with", "from", "have", "were", "been", "their", "would",
        "could", "should", "there", "about", "which", "when", "what", "them",
        "then", "than", "into", "more", "some", "will", "also", "other",
        "automation", "robot", "robots", "robotic", "company", "companies",
        "nbsp", "font", "href", "https", "articles", "target", "blank", "color",
        "6f6f6f", "news", "google", "times", "motley", "fool", "reviews",
    }
    words = re.findall(r"[a-z0-9]+", text_lower)
    return Counter(w for w in words if len(w) >= min_len and w not in stop)


def ngram_freq(text_lower, n=2):
    words = text_lower.split()
    bigrams = [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]
    return Counter(b for b in bigrams if len(b) > 3)


def main():
    print("Fetching leads from API...")
    all_leads = fetch_leads()
    other_leads = [c for c in all_leads if is_other(c)]
    print(f"Total leads fetched: {len(all_leads)}, industry=Other: {len(other_leads)}")

    if not other_leads:
        print("No Other leads in this sample. Try increasing limit or check API.")
        return

    # Build combined text per lead and full corpus
    combined_list = []
    for c in other_leads:
        name = c.get("company_name") or ""
        texts = [s.get("raw_text") or "" for s in c.get("signals") or []]
        raw_combined = name + " " + " ".join(texts)
        combined = strip_html(raw_combined)
        combined = re.sub(r"\s+", " ", combined).strip()
        combined_list.append({
            "name": name,
            "signal_count": len(c.get("signals") or []),
            "combined": combined[:500],
            "combined_lower": combined.lower()[:3000],
        })
    all_text = " ".join(r["combined_lower"] for r in combined_list)
    word_counts = word_freq(all_text)
    bigram_counts = ngram_freq(all_text, n=2)

    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    sample_path = os.path.join(reports_dir, "unknown_industry_leads_sample.txt")
    keyword_path = os.path.join(reports_dir, "unknown_industry_keyword_analysis.txt")

    # Sample for manual review
    by_signals = sorted(combined_list, key=lambda x: -x["signal_count"])
    with open(sample_path, "w") as f:
        f.write(f"# Unknown-industry (Other) leads sample — {len(other_leads)} from API\n")
        f.write("# Company name | signal_count | first 400 chars of name + signal text\n\n")
        for i, row in enumerate(by_signals[:350]):
            f.write(f"{i+1}. {row['name']} | signals:{row['signal_count']} | {row['combined'][:400]}\n\n")
    print(f"Wrote {sample_path}")

    # Keyword analysis
    with open(keyword_path, "w") as f:
        f.write(f"# Keyword analysis for {len(other_leads)} Other leads (via API)\n\n")
        f.write("## Top 120 words\n")
        for word, count in word_counts.most_common(120):
            f.write(f"  {count:5d}  {word}\n")
        f.write("\n## Top 80 bigrams (suggest new industries)\n")
        for bigram, count in bigram_counts.most_common(80):
            f.write(f"  {count:5d}  {bigram}\n")
    print(f"Wrote {keyword_path}")

    print("\nTop 25 words:", [w for w, _ in word_counts.most_common(25)])
    print("Top 15 bigrams:", [b for b, _ in bigram_counts.most_common(15)])


if __name__ == "__main__":
    main()
