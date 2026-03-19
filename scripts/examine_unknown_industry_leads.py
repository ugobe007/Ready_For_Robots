#!/usr/bin/env python3
"""
Examine leads with unknown industry (the "Other" bucket).
Outputs: sample of company names + signal text for manual review, and a
keyword frequency report to suggest new industries or keyword rules.
"""
import os
import re
import sys
from collections import Counter

# Load .env so DATABASE_URL is set when running from project root
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal

# Industries we already have (so we can spot gaps)
KNOWN_INDUSTRIES = {
    "logistics", "hospitality", "food service", "healthcare", "medical technology",
    "food processing & manufacturing", "datacenters", "airports & aviation",
    "retail", "apparel & textiles", "casinos & gaming", "cruise lines",
    "theme parks & entertainment", "real estate & facilities", "automotive dealerships",
}


def is_unknown_industry(val):
    if val is None:
        return True
    v = (val or "").strip().lower()
    return v in ("", "unknown", "other")


def get_unknown_industry_leads(db, limit=2000):
    """Companies with null/empty/unknown industry, with signal text."""
    companies = (
        db.query(Company)
        .filter(
            (Company.industry == None)
            | (Company.industry == "")
            | (Company.industry.ilike("unknown"))
            | (Company.industry.ilike("other"))
        )
        .all()
    )
    out = []
    for c in companies:
        signals = db.query(Signal).filter(Signal.company_id == c.id).order_by(Signal.id).all()
        signal_texts = [s.signal_text or "" for s in signals if (s.signal_text or "").strip()]
        combined = " ".join([c.name or "", " ".join(signal_texts)])
        out.append({
            "id": c.id,
            "name": (c.name or "").strip(),
            "website": (c.website or "").strip(),
            "source": (c.source or "").strip(),
            "signal_count": len(signals),
            "signal_texts": signal_texts,
            "combined_lower": combined.lower() if combined else "",
        })
    return out


def word_freq(text_lower, min_len=4, stop=None):
    """Simple word frequency (skip numbers, very short, stopwords)."""
    stop = stop or {
        "that", "this", "with", "from", "have", "were", "been", "their", "would",
        "could", "should", "there", "about", "which", "when", "what", "them",
        "then", "than", "into", "more", "some", "will", "also", "other",
        "automation", "robot", "robots", "robotic", "company", "companies",
    }
    words = re.findall(r"[a-z0-9]+", text_lower)
    return Counter(w for w in words if len(w) >= min_len and w not in stop)


def ngram_freq(text_lower, n=2, min_count=2):
    """Bigram frequency to catch phrases like 'senior living', 'cold chain'."""
    words = text_lower.split()
    bigrams = [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]
    return Counter(b for b in bigrams if len(b) > 3 and not b.isdigit())


def main():
    db = SessionLocal()
    try:
        leads = get_unknown_industry_leads(db)
    finally:
        db.close()

    if not leads:
        print("No unknown-industry leads found.")
        return

    # Paths
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    sample_path = os.path.join(reports_dir, "unknown_industry_leads_sample.txt")
    keyword_path = os.path.join(reports_dir, "unknown_industry_keyword_analysis.txt")

    # --- 1. Sample for manual review: name + first 400 chars of combined text ---
    with open(sample_path, "w") as f:
        f.write(f"# Unknown-industry leads sample (total {len(leads)})\n")
        f.write("# Format: Company name | signal_count | first 400 chars of name + signal text\n")
        f.write("# Use this to decide new industries or keyword rules.\n\n")
        # Sort by signal count desc so we see leads with most context first
        by_signals = sorted(leads, key=lambda x: -x["signal_count"])
        for i, row in enumerate(by_signals[:400]):
            name = row["name"] or "(no name)"
            combined = (row["name"] or "") + " " + " ".join(row["signal_texts"])
            combined = re.sub(r"\s+", " ", combined).strip()[:400]
            f.write(f"{i+1}. {name} | signals:{row['signal_count']} | {combined}\n\n")
    print(f"Wrote sample to {sample_path} ({min(400, len(leads))} leads)")

    # --- 2. Keyword / bigram frequency on all unknown leads ---
    all_text = " ".join(r["combined_lower"] for r in leads)
    word_counts = word_freq(all_text)
    bigram_counts = ngram_freq(all_text, n=2)

    with open(keyword_path, "w") as f:
        f.write(f"# Keyword analysis for {len(leads)} unknown-industry leads\n\n")
        f.write("## Top 120 words (min 4 chars, stopwords removed)\n")
        for word, count in word_counts.most_common(120):
            f.write(f"  {count:5d}  {word}\n")
        f.write("\n## Top 80 bigrams (may suggest new industries)\n")
        for bigram, count in bigram_counts.most_common(80):
            f.write(f"  {count:5d}  {bigram}\n")
    print(f"Wrote keyword analysis to {keyword_path}")

    # --- 3. Print short summary to stdout ---
    print(f"\nTotal unknown-industry leads: {len(leads)}")
    print("Top 25 words:", [w for w, _ in word_counts.most_common(25)])
    print("Top 15 bigrams:", [b for b, _ in bigram_counts.most_common(15)])


if __name__ == "__main__":
    main()
