# Robot Understanding v1: Semantic Extraction Progress

**Status**: Offline benchmark infrastructure complete. Semantic extraction engine built but not yet wired to pipeline.

## Completed (commits a7eaebf9, f6336544)

### 1. Offline Benchmark Infrastructure ✅

Created `scripts/snapshot_robot_pages.py`:
- Fetches robot pages from benchmark set
- Saves HTML, plain text, and metadata (status code, fetch date, final URL)
- Output: `tests/fixtures/robot_pages/<robot-id>/` (page.html, page.txt, metadata.json)
- Run from machine with internet; commit snapshots for offline testing

Updated `scripts/test_understanding_v1_benchmark.py`:
- **Three-bucket reporting**: FETCH_FAILED, EXTRACTION_FAILED, PASSED
- Offline mode (default): uses snapshots from `tests/fixtures/robot_pages/`
- Live mode (`--live`): fetches URLs in real-time
- Per-robot testing: `--robot <robot-id>`
- Separates network issues from extraction quality

Documentation: `tests/fixtures/robot_pages/README.md`

### 2. Semantic Extraction Engine ✅

Created `app/services/robot_understanding_v1/semantic_extraction.py`:

**Core capabilities**:
- Single LLM call per page with strict JSON schema
- Extracts 7 fact categories with confidence + evidence:
  1. Product class (mobile_robot, humanoid, etc.)
  2. Domains (healthcare, warehouse, construction, etc.)
  3. Tasks (picking, transport, inspection, etc.)
  4. Capabilities (navigation, grasping, vision, etc.)
  5. Deployment environments (indoor, hospital, factory, etc.)
  6. Buyer verticals (target customer industries)
  7. Hardware properties (payload, speed, battery, dimensions)

**Confidence calibration**:
- 0.3-0.5: vague marketing ("AI-powered", "flexible automation")
- 0.6-0.8: specific but unquantified claims
- 0.9-1.0: concrete, quantified facts

**Ontology mapping**:
- Maps extracted terms to `ontology/rfr_graph.v1.json` predicates
- Logs unmapped terms to `ontology_gaps.jsonl` for review
- Preserves original term + confidence even when unmapped

**Evidence tracking**:
- Each fact includes exact text snippet (20-50 words) from page
- Enables audit and debugging of extraction quality

**Page hashing**:
- Computes SHA256 of page_text for caching key
- Result format includes `(url, page_hash)` for cache lookup
- Caching not yet implemented but structure ready

## Next Steps (in order)

### 3. Wire Semantic Extraction to Pipeline 🚧

**Problem**: `match_robot_url_v1()` doesn't accept pre-cached page_text yet. It still fetches URLs internally via `build_robot_profile()`.

**Solution**:
1. Add `page_text` parameter to `match_robot_url_v1(url, *, page_text=None, ...)`
2. Update `build_robot_profile()` in `robot_understanding_v1/pipeline.py`:
   - Accept optional `page_text` parameter
   - Skip fetching if `page_text` provided
   - Pass through to `extract_robot_facts_semantic()`
3. Update `extract_robot_facts_semantic()` to be called from pipeline
4. Add mode flag: `use_semantic=True` to switch between regex and LLM extraction

### 4. Implement Result Caching 🚧

Cache semantic extraction results by `(url, sha256(page_text))`:
- Cache location: `app/services/robot_understanding_v1/extraction_cache/`
- Format: JSON files keyed by `{url_hash}_{page_hash}.json`
- TTL: 7 days (configurable)
- Speeds up benchmark re-runs and avoids re-extracting unchanged pages

### 5. Implement Fallback Logic 🚧

In `match_robot_url_v1()`:
```python
try:
    semantic_result = extract_robot_facts_semantic(url, page_text)
    
    # Check if extraction yielded facts
    if (semantic_result.product_class is None and 
        len(semantic_result.capabilities) == 0 and
        len(semantic_result.tasks) == 0):
        # Zero facts extracted - flag for review and fall back
        log_extraction_failure(url, "zero_facts", semantic_result)
        return match_robot_url(url)  # Legacy matcher
    
    # Use semantic result
    return convert_semantic_to_profile(semantic_result)
    
except Exception as e:
    # Extraction error - flag and fall back
    log_extraction_failure(url, "error", error=str(e))
    return match_robot_url(url)
```

### 6. Run Comparative Benchmark 🚧

Execute both extraction methods on all 28 benchmark robots + 3 negative controls:

**Comparison table**:
```
| Robot ID | v1 Regex | v1 Semantic | Winner |
|----------|----------|-------------|--------|
| moxi-hospital | PASSED | PASSED | tie |
| locus-multi-ind | PASSED | PASSED | tie |
| gritt-construction | EXTRACTION_FAILED | PASSED | semantic |
| figure-humanoid | EXTRACTION_FAILED | EXTRACTION_FAILED (low conf) | tie |
| ... | ... | ... | ... |
```

**Metrics**:
- Pass rate (28 robots)
- Fetch failures (excluded from quality score)
- Extraction failures (zero facts or wrong classification)
- Confidence distribution (for semantic)
- Ontology gap count (terms with no mapping)

### 7. Review & Tune 🚧

After benchmark:
1. Review ontology gaps (`ontology_gaps.jsonl`)
2. Add missing terms to ontology or map to existing predicates
3. Adjust confidence thresholds if needed
4. Update prompts for problematic extraction patterns

## Testing Commands

```bash
# Take snapshots (from machine with internet):
python3 scripts/snapshot_robot_pages.py

# Commit snapshots:
git add tests/fixtures/robot_pages/
git commit -m "Add robot page snapshots for offline benchmark"

# Run benchmark offline (after snapshots committed):
python3 scripts/test_understanding_v1_benchmark.py

# Test specific robot:
python3 scripts/test_understanding_v1_benchmark.py --robot moxi-hospital

# Run with live URLs (requires internet):
python3 scripts/test_understanding_v1_benchmark.py --live
```

## Architecture Notes

**Current flow (regex)**:
```
match_robot_url_v1(url)
  → build_robot_profile(url)
    → fetch_page(url)
    → extract_facts_regex(page_text)  # app/services/robot_understanding_v1/facts.py
  → derive_capabilities(profile)
  → match_jobs_for_profile(profile)
```

**Target flow (semantic)**:
```
match_robot_url_v1(url, page_text=snapshot['text'])
  → build_robot_profile(url, page_text=page_text)
    → extract_robot_facts_semantic(url, page_text)  # NEW
      → check cache by (url, page_hash)
      → LLM extraction with JSON schema
      → map to ontology
      → log ontology gaps
      → cache result
  → derive_capabilities(semantic_profile)
  → match_jobs_for_profile(profile)
```

**Fallback flow** (when semantic extraction fails):
```
match_robot_url_v1(url)
  → build_robot_profile(url)
    → extract_robot_facts_semantic(url, page_text)
      → returns zero facts or errors
    → log_extraction_failure(url, reason)
    → FALLBACK: match_robot_url(url)  # Legacy regex matcher
```

## Files Changed

```
scripts/snapshot_robot_pages.py                          [NEW]
scripts/test_understanding_v1_benchmark.py              [NEW]
tests/fixtures/robot_pages/README.md                    [NEW]
app/services/robot_understanding_v1/semantic_extraction.py  [NEW]
```

## Not Yet Changed (pending wiring)

```
app/services/robot_understanding_v1/pipeline.py          [TODO: accept page_text]
app/services/robot_job_capability_match.py              [TODO: add fallback logic]
```

## Benchmark Status

- **Snapshots**: Not yet taken (requires machine with internet)
- **Offline benchmark**: Ready to run after snapshots committed
- **Semantic extraction**: Built but not wired to pipeline
- **Comparative test**: Blocked until wiring complete

## Immediate Next Action

**Wire semantic extraction to pipeline**:
1. Update `build_robot_profile()` to accept `page_text` parameter
2. Call `extract_robot_facts_semantic()` when `use_semantic=True`
3. Convert `SemanticExtractionResult` to `RobotProfile` format
4. Test with single robot snapshot to verify end-to-end flow

Once wired, we can run the full comparative benchmark: v1 regex vs v1 semantic.
