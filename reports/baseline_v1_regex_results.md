# ⚠️ INVALID BASELINE - DO NOT USE

**Status**: This report is **INVALID** and should not be relied upon.

**Reason**: The benchmark called `build_robot_profile()` which fetches URLs live via `fetch_page()`. The Cloud Agent VM has no reliable DNS. The regex extraction never saw the snapshot text - it extracted from empty pages returned by failed network requests.

**Evidence**: Direct test of regex extraction on TyBot snapshot (15,840 chars, "rebar" mentioned 19 times) extracted 4 facts including `product_class: construction` and `claims_construction: True`. During benchmark run, same robot yielded 0 facts because `build_robot_profile()` fetched live instead of using cached text.

**Corrected baseline**: See later reports after `page_text` parameter is wired to `build_robot_profile()`.

---

# Original Report (Invalid - Kept for Audit Trail)

**Date**: 2026-10-13  
**Snapshots**: Commit b2bb6e0b (24/28 valid pages)  
**Test**: `PYTHONPATH=/workspace python3 scripts/test_understanding_v1_benchmark.py`

## Summary

| Bucket | Count | Percentage |
|--------|-------|------------|
| **FETCH_FAILED** | 4/28 | 14% |
| **EXTRACTION_FAILED** | 24/28 | 86% |
| **PASSED** | 0/28 | 0% |

**Conclusion**: Current regex-based extraction is completely broken. Zero robots passed.

## Fetch Failures (4) — Infrastructure Issues

These don't count against extraction quality:

1. **hc-01** (Diligent Robotics / Moxi) - DNS resolution failed
2. **con-04** (Canvas) - SSL handshake failure
3. **ag-01** (Burro) - HTTP 403
4. **insp-01** (ANYbotics) - HTTP 403

Note: **hos-02** (Pudu) returned HTTP 200 but only navigation/cookie banner (127 words, no product copy). Treating as usable but expect extraction challenges.

## Extraction Failures (24) — The Core Problem

All 24 robots with valid snapshots failed extraction. Common patterns:

### Zero Capabilities Extracted (19 robots)

These pages have clear product copy but regex missed everything:

- **con-01** (Gritt) - THE KEY TEST CASE
  - Page says: "construction workforce", "jobsites", "attachments to common equipment"
  - Regex extracted: 0 capabilities
  - **This is why we're building semantic extraction**

- **log-02** (Boston Dynamics Stretch) - 1,168 words of product copy
  - Clear description of truck unloading, case handling, mobile manipulation
  - Regex extracted: 0 capabilities
  
- **log-03** (Agility Digit) - 479 words
  - Humanoid for logistics/warehouse
  - Regex extracted: 0 capabilities

- **gen-01** (Figure) - 172 words
  - Vague aspirational copy ("general purpose humanoid")
  - Regex extracted: 0 capabilities
  - **This is correct behavior** - low confidence is better than invented facts

- Also failed: hc-02, hos-01, hos-02, hos-03, cln-01, cln-02, food-01, food-02, log-01, sec-01, sec-02, ret-01, mfg-01, con-03

### Wrong Product Class (3 robots)

Extracted some facts but misclassified:

- **con-02** (Dusty Robotics) - classified as generic "construction_robot" instead of "construction_layout_robot"
- **del-01** (Starship) - classified as "serving" instead of "outdoor_delivery_robot"
- **mfg-02** (Formic) - classified as "warehouse" instead of "robotics_service_provider"

### Insufficient Capabilities (2 robots)

Extracted 1 capability when ≥2 required:

- **hc-03** (Xenex) - only 1 cap matched
- **ag-02** (Carbon Robotics) - only 1 cap matched

### Could Not Understand (3 robots)

Hit explicit "could_not_understand" state:

- **hc-02** (Relay Robotics)
- **sec-02** (Cobalt Robotics)
- **ret-01** (Simbe)

## Key Failure Modes

### 1. Non-Obvious Phrasing (Primary Issue)

Regex looks for exact keywords like "construction robot", "warehouse AMR", "mobile manipulator".

Pages use natural language instead:
- Gritt: "physical AI for the construction workforce"
- Boston Dynamics: "case handling", "trailer unloading"
- Figure: "general purpose humanoid"
- Miso: "fry station", "back of house automation"

### 2. Domain-Specific Terminology

- Construction: "jobsite", "attachments", "infrastructure buildout"
- Hospitality: "food runner", "bussing", "front of house"
- Manufacturing: "machine tending", "production line"
- Security: "patrol", "deterrence", "guard augmentation"

Regex has patterns for maybe 10-20 terms. Real pages use hundreds.

### 3. Multi-Product Sites

- Pudu: sells cleaning + delivery + service robots
- Richtech: ADAM, Titan, Matradee, Medbot
- Universal Robots: many cobot models

Regex doesn't handle product disambiguation.

## What Semantic Extraction Should Fix

1. **Extract from natural language**: "construction workforce" → `construction_domain`
2. **Map domain terminology**: "jobsite" → construction, "fry station" → food service
3. **Confidence scoring**: Figure's vague copy → low confidence (correct!)
4. **Evidence tracking**: "attachments to common equipment" → `equipment_retrofit` capability
5. **Ontology mapping**: Log unmapped terms for review

## Expected Semantic Results

After wiring semantic extraction, we expect:

- **Gritt (con-01)**: Extract `construction_domain`, `pick_and_place`, `material_transport`, `assembly` with medium confidence (0.6-0.8) and evidence snippets
- **Boston Dynamics (log-02)**: Extract `mobile_manipulator`, `box_handling`, `truck_unloading` with high confidence (0.9+)
- **Figure (gen-01)**: Extract `humanoid_robot` with low confidence (0.3-0.5) because copy is vague — **this is correct**
- **Overall pass rate**: Expecting 20-22/24 to pass (some like Pudu may still fail due to no content)

## Next Steps

1. ✅ Baseline documented (0/28 passed)
2. 🚧 Wire `page_text` parameter through `match_robot_url_v1()` and `build_robot_profile()`
3. 🚧 Integrate semantic extraction engine
4. 🚧 Run comparative benchmark: regex vs semantic
5. 🚧 Implement fallback when semantic yields zero facts
6. 🚧 Review ontology gaps and tune confidence thresholds

## Detailed Results

Full results saved to: `reports/understanding_v1_benchmark_results.json`

Command:
```bash
PYTHONPATH=/workspace python3 scripts/test_understanding_v1_benchmark.py
```
