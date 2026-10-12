# ✅ Buyer Readiness Fixes Applied

## What Was Fixed

### Problem
- **Hoboken** and other city names were incorrectly appearing as buyers in the `buying_now` stage
- Hand-typed place list was incomplete and would never catch all cities
- No distinction between bare place names ("Hoboken") vs. qualified organizations ("City of Hoboken")

### Solution Applied
Two commits from `buyer-readiness-fixes.patch`:

1. **Junk company names & typed signals** (commit `acfc176f`)
   - Added `buyer_name_problem()` function to filter out junk company names
   - Added support for typed intent signals (vendor_selection, pilot_success, robot_installation)
   - Added initial place name filtering with `_COUNTRIES_REGIONS`

2. **Comprehensive place names** (commit `cf3262a7`)
   - Added `app/data/place_names.txt` with **8,908 place names** from GeoNames database
   - US cities ≥15k population
   - World cities ≥100k population
   - US states
   - Countries
   - Exact match only: "Hoboken" blocked, "City of Hoboken" passes
   - Known brands exempted: "Providence" (hospital), "Columbia" (clothing), "Target"

## Test Results

✅ **All 37 buyer readiness tests passed**

### Key Test Cases
- ✅ "Hoboken" → Watch (place name, not a company)
- ✅ "Hoboken, NJ" → Watch (place name, not a company)
- ✅ "Henderson" → Watch (place name, not a company)
- ✅ "Las Vegas" → Watch (place name, not a company)
- ✅ "Sri Lanka" → Watch (place name, not a company)
- ✅ "City of Hoboken" → Passes (qualified name)
- ✅ "Hoboken University Medical Center" → Passes (institution)
- ✅ "Clark County Department of Aviation" → Passes (government agency)
- ✅ "Providence" → Passes (known brand - hospital system)
- ✅ "Target" → Passes (known brand - retailer)
- ✅ "Omni Hotels & Resorts" → Passes (real company)

## How It Works

```python
# Example usage
from app.services.buyer_readiness import buyer_name_problem

buyer_name_problem("Hoboken")                    # → "place name, not a company"
buyer_name_problem("City of Hoboken")            # → None (passes)
buyer_name_problem("Hoboken University...")      # → None (passes)
buyer_name_problem("Target")                     # → None (known brand)
buyer_name_problem("Providence")                 # → None (known brand)
```

### Filtering Logic

1. **Check for encoded/junk**: Base64 strings, "Dwbrobot", etc. → Watch
2. **Check for headlines**: "How Robots Are Changing..." → Watch
3. **Check for place names**:
   - Strip trailing ", ST" suffix ("Hoboken, NJ" → "Hoboken")
   - Check if in 8,908 place names list
   - Exempt known brands (Providence, Columbia)
   - Check against known brands allowlist
   - **Exact match only**: "Hoboken" fails, "City of Hoboken" passes

## Changes Made

```
app/data/place_names.txt        | 8908 new lines (place name database)
app/services/buyer_readiness.py |  102 additions (name filtering + typed signals)
tests/test_buyer_readiness.py   |   21 additions (place name test cases)
```

## Git Commits

```
cf3262a7 Buyer readiness: catch every city/state/country as a place name
acfc176f Buyer readiness: drop junk company names, credit typed intent signals
```

Pushed to `origin/main` ✅

## Next Step

Run the buyer ranking script with the database:

```bash
# Where DATABASE_URL is available (local or Fly SSH)
python3 scripts/rank_buyers.py --apply
```

This will:
1. Re-classify all companies with the new place name filtering
2. Move "Hoboken", "Henderson", "Las Vegas", etc. from buyer stages → Watch
3. Keep qualified names like "City of Hoboken" in their proper buyer stage
4. Stamp updated classifications to `companies.automation_profile.buyer_readiness`

## Expected Impact

**Before fix**:
- Bare city names appearing in buyer pipeline
- False positives in buying_now/evaluating stages
- Confusion about whether a city government is a real buyer

**After fix**:
- Only qualified organization names appear as buyers
- City governments properly identified: "City of Hoboken" (buyer) vs. "Hoboken" (place)
- Clean buyer pipeline with 8,908 place names filtered out
- Known brands (Target, Providence, Columbia) still pass through correctly

## About the Daily Jobs Email

Per your note:
> "The daily jobs email reads from robot_jobs, which the purge emptied. The rebuild only restores postings that show buying intent, so the table holds very few rows and the email has almost nothing to send. Your actual buyer list is reports/buyer_readiness.csv."

The buyer list is now in `reports/buyer_readiness.csv` after running `rank_buyers.py`. If you want the daily email to show buying_now and evaluating companies with their evidence lines (instead of robot_jobs postings), let me know and I can make that change.

## Status

✅ **Buyer readiness fixes applied successfully**  
✅ **All 37 tests passing**  
✅ **Committed and pushed to main**  
⏸️ **Ready to run**: `python3 scripts/rank_buyers.py --apply` (when DATABASE_URL available)

The Hoboken false positive is now fixed with comprehensive place name filtering covering 8,908 cities, states, and countries worldwide.
