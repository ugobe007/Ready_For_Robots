# Robot Understanding v1: Offline Benchmark Infrastructure

## Overview

This directory contains the offline benchmark infrastructure for testing robot understanding extraction quality without requiring live network access.

## How It Works

1. **Snapshot Phase** (`scripts/snapshot_robot_pages.py`):
   - Run from a machine with full internet access
   - Fetches each benchmark robot's URL
   - Saves HTML, extracted text, and metadata (status code, fetch date)
   - Commits snapshots to `tests/fixtures/robot_pages/<robot-id>/`

2. **Test Phase** (`scripts/test_understanding_v1_benchmark.py`):
   - Runs offline against saved snapshots (default)
   - Or with `--live` flag to fetch URLs in real time
   - Reports three buckets:
     - **FETCH FAILED**: Network/snapshot issues (doesn't count against v1)
     - **EXTRACTION FAILED**: Zero facts extracted (v1 problem)
     - **PASSED**: Meets all criteria

## Directory Structure

```
tests/fixtures/robot_pages/
  manifest.json                 # Index of all snapshots
  moxi-hospital/
    metadata.json               # Fetch date, status, URL
    page.html                   # Raw HTML
    page.txt                    # Extracted text
  locus-multi-ind/
    metadata.json
    page.html
    page.txt
  ...
```

## Usage

### Taking Snapshots

```bash
# From a machine with internet (not Cloud Agent VM):
python3 scripts/snapshot_robot_pages.py

# Commit results:
git add tests/fixtures/robot_pages/
git commit -m "Add robot page snapshots for benchmark"
```

### Running Benchmark

```bash
# Offline mode (default, uses snapshots):
python3 scripts/test_understanding_v1_benchmark.py

# Test specific robot:
python3 scripts/test_understanding_v1_benchmark.py --robot moxi-hospital

# Live mode (requires internet):
python3 scripts/test_understanding_v1_benchmark.py --live
```

## Current Limitation

**TODO**: `match_robot_url_v1` does not yet accept pre-cached page text. It still fetches the URL internally. To make the benchmark truly offline, we need to:

1. Add `page_text` parameter to `match_robot_url_v1()`
2. Update `build_robot_profile()` in `robot_understanding_v1/pipeline.py` to accept pre-fetched content
3. Cache extraction results by `(url, sha256(page_text))` to avoid re-processing unchanged pages

For now, the snapshot infrastructure is in place and ready. The benchmark will use snapshots for validation once the extraction pipeline accepts cached input.

## Three-Bucket Reporting

The benchmark separates:

1. **Fetch failures** (network/DNS/timeout) - infrastructure issues, not extraction quality
2. **Extraction failures** (zero capabilities, wrong class, no jobs) - actual v1 problems
3. **Passes** - met all criteria

This lets us distinguish "URL is down" from "v1 failed to extract."

## Next Steps

1. ✅ Snapshot infrastructure
2. ✅ Three-bucket reporting
3. 🚧 Semantic extraction (LLM-based facts with confidence + provenance)
4. 🚧 Pass cached page_text through to extraction
5. 🚧 Page hash caching to avoid re-extraction
6. 🚧 Fallback to legacy matcher when extraction yields zero facts
