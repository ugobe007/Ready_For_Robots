# Snapshot Robot Pages - Instructions for Mac

## Quick Start

```bash
# 1. Pull latest from repo
git pull origin main

# 2. Install dependencies (if not already installed)
pip install requests beautifulsoup4

# 3. Run snapshot script
python3 scripts/snapshot_robot_pages.py

# 4. Review results and commit
git status
git add tests/fixtures/robot_pages/
git commit -m "Add robot page snapshots for offline benchmark"
git push origin main
```

## What It Does

The script fetches 28 robot company URLs plus 3 negative controls from `tests/fixtures/robot_benchmark_set_e5e6.json` and saves:

- **HTML** (`page.html`) - raw HTML from the page
- **Plain text** (`page.txt`) - extracted text content
- **Metadata** (`metadata.json`) - fetch date, status code, final URL after redirects

Output structure:
```
tests/fixtures/robot_pages/
  manifest.json                 # Summary of all snapshots
  hc-01/                        # Diligent Robotics (Moxi)
    metadata.json
    page.html
    page.txt
  con-01/                       # Gritt (construction - the failure case)
    metadata.json
    page.html
    page.txt
  log-01/                       # Locus Robotics
    metadata.json
    page.html
    page.txt
  ...
```

## Expected Output

The script will print status for each URL:

```
================================================================================
Snapshotting Robot Pages for Offline Benchmark
================================================================================
Benchmark version: 2026-10-13
Total robots: 28
Output directory: tests/fixtures/robot_pages

Fetching hc-01: Diligent Robotics - https://www.diligentrobotics.com
  ✓ HTTP 200
Fetching hc-02: Relay Robotics - https://relayrobotics.com
  ✓ HTTP 200
Fetching con-01: Gritt - https://gritt.ai
  ✓ HTTP 200
...

================================================================================
Summary
================================================================================
Successful fetches: 28/28
Failed fetches: 0/28

Manifest written to: tests/fixtures/robot_pages/manifest.json
```

## Troubleshooting

**If some URLs fail (timeout, DNS, etc.)**:
- The script continues and marks failures in metadata
- Failed snapshots still get directories with error metadata
- This is OK - the benchmark will report these as FETCH_FAILED (not extraction failures)

**If a URL redirects**:
- The script follows redirects automatically
- Final URL is saved in metadata.json
- This is fine - the benchmark uses the fetched page regardless

**If you need to re-run**:
- The script will overwrite existing snapshots
- You can re-run specific robots by modifying the script temporarily (or we can add a --robot flag)

## After Snapshotting

Once snapshots are committed, the Cloud Agent can run the benchmark offline:

```bash
# Offline mode (uses committed snapshots - no internet needed)
python3 scripts/test_understanding_v1_benchmark.py

# Test specific robot
python3 scripts/test_understanding_v1_benchmark.py --robot con-01

# Three-bucket output:
#   FETCH FAILED:       X/28 (network issues, doesn't count against v1)
#   EXTRACTION FAILED:  Y/28 (v1 problems - zero facts, wrong class, no jobs)
#   PASSED:             Z/28 (met all criteria)
```

## Benchmark Coverage

28 robots across 14 domains:
- **Healthcare**: Moxi (Diligent), Relay, Xenex
- **Construction**: Gritt (THE FAILURE CASE), Dusty, ACR, Canvas
- **Hospitality**: Bear, Pudu, Richtech
- **Cleaning**: Avidbots, Brain Corp
- **Food**: Miso, Chef Robotics
- **Warehouse**: Locus, Boston Dynamics Stretch, Agility Digit
- **Security**: Knightscope, Cobalt
- **Agriculture**: Burro, Carbon Robotics
- **Inspection**: ANYbotics, Gecko
- **Retail**: Simbe
- **Delivery**: Starship
- **Manufacturing**: Universal Robots, Formic
- **General humanoid**: Figure AI

Plus 3 negative controls (news article, simulation software, partial-robot company).

## Why This Matters

**Gritt is the key test**: It describes itself as "physical AI for construction workforce" attached to "skid steers and forklifts" for "jobsite" work. Regex misses this entirely because it doesn't say "construction robot." Semantic extraction must catch "physical AI", "construction workforce", "jobsite", "attachments to equipment" → derive construction_domain + construction_robot_retrofit class.

Once snapshots are in, we can run offline benchmarks comparing:
- v1 regex (current): Expected to fail on Gritt + others with non-obvious phrasing
- v1 semantic (LLM): Expected to extract facts from vague/marketing copy with confidence scores

Then we wire the semantic extraction to the pipeline and make it the default.
