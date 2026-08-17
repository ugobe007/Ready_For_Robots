# Blind 20 outcome — Understanding Phases 1–3 holdout gate (company-binding fix)

**Prior fail run (product-path overbind):** `docs/calibration/understanding_blind_20/runs/run_20260817T015249Z`  
**This rerun:** `docs/calibration/understanding_blind_20/runs/run_20260817T040820Z`  
**Scores:** `docs/calibration/understanding_blind_20/scores/run_20260817T040820Z_scores.md`  
**Post-fix tree:** `TREE d528e9249bb7f58bd05ce08b9bbcf46e2af66ee066c7f5bb32c9dd5b967eac46`  
**Scope:** Company/product disentanglement **only**. No source/spec/taxonomy/fetch retune. No OEM branches. No Phase 4 / jobs / QUALIFY.  
**Cohort / ground truth:** unchanged (same twenty).

## Verdict: FAIL

Company identity recovered to **100%**. Product identity, grounding, sibling-free, unsupported-fact rate, fact recall, and numeric scope held. **Critical recall stayed at 78%** (below ≥80% — not tuned this pass). Tier ±1 slipped 90%→85% (fetch/tier noise; not retuned). Phase 1–3 gate **not** earned. **Phase 4 not opened.**

### Aggregate vs Blind 20 bars (before → after this company-only fix)

Before = `run_20260817T015249Z` (SKU-as-company regression). After = `run_20260817T040820Z`.

| Gate | Bar | Before | After | Status |
|------|-----|--------|-------|--------|
| Company identity | ≥95% | 60% | **100%** | PASS |
| Product identity | ≥90% (rerun bar 100%) | 100% | **100%** | PASS |
| Source hygiene | ≥95% | 95% | **95%** | PASS |
| Source grounding | ≈100% | 100% | **100%** | PASS |
| Critical fact recall | ≥80% | 78% | **78%** | FAIL (unchanged; not tuned) |
| Overall fact recall | ≥60% | 62% | **62%** | PASS |
| Material sibling contamination | 0 | yes | **yes** | PASS |
| Unsupported material facts | <5% | 0% | **0%** | PASS |
| Tier calibration ±1 | ≥90% | 90% | **85%** | FAIL (slip; not tuned) |
| Numeric scope accuracy | ≥95% | 100% | **100%** | PASS |
| Canonical company binding | ≥95% | 60% | **100%** | PASS |
| Company/product disentanglement | report | — | **100%** | held |

### Company recovery (the bug this pass fixed)

| ID | Robot | Before company | After company |
|----|-------|----------------|---------------|
| b20-06 | Unitree H1 | H1 | **Unitree** |
| b20-09 | SoftBank Whiz | Whiz | **Softbank Robotics** |
| b20-10 | Tennant T7AMR | T7AMR | **Tennantco** (matches Tennant) |
| b20-11 | LionsBot R3 | R3 Scrub Pro | **Lionsbot** |
| b20-14 | Doosan A0509 | A0509 | **Doosan Robotics** |
| b20-16 | Elios 3 | Elios 3 | **Flyability** |
| b20-18 | Pepper | Pepper | **Softbank Robotics** |
| b20-19 | Canvas | JLG Industries, Inc. | **Canvas** (Hosted by: Jlg) |

All other robots remained company-correct. Product identity stayed 100%. Disentanglement 20/20.

### By physics class (after)

| Class | Company | Product | Fact recall | Critical recall | Notes |
|-------|---------|---------|-------------|-----------------|-------|
| AMR | 100% | 100% | 40% | 38% | Identity clean; OTTO/Geek+ facts still thin |
| Humanoid / MM | 100% | 100% | 65% | 75% | Unitree company fixed |
| Cleaning | 100% | 100% | 61% | 100% | SoftBank/Tennant/LionsBot company fixed |
| Cobot / arm | 100% | 100% | 67% | 67% | Doosan company fixed; ABB facts still empty |
| Inspection | 100% | 100% | 100% | 100% | Flyability company fixed |
| Service | 100% | 100% | 54% | 100% | Pepper company fixed |
| Unusual | 100% | 100% | 67% | 100% | Canvas brand (not JLG host) |

## What this fix changed (company binding only)

1. **Separate decisions** — discover product candidates, then bind company independently; never promote `product_hint` from path/title alone.
2. **Negative invariant** — selected product/model string is ineligible as `company.name` unless independent org-brand evidence confirms it (unit-tested).
3. **SKU rejection** — digit/model-shaped strings (H1, A0509, T7AMR, Elios 3, R3 Scrub Pro, …) cannot win company.
4. **Acquirer signal tightened** — dropped `powered by` (false-positive BrainOS); require real acquired/brand-of language for acquirer-brand promotion.
5. **Self-as-company prose** — e.g. “Canvas, the … company” evidences brand over host Organization schema; optional `Hosted by:` note for host domain.
6. **Preference order** — jsonld/og/copyright/domain → manufacturer “by …” → acquirer/self-company only when evidenced.
7. **Scoring** — report Company/product disentanglement rate (this run: 100%).

Touched: `app/services/robot_understanding_v1/resolve.py`, `tests/test_robot_understanding_v1.py`, `scripts/score_understanding_blind20.py` (disentanglement metric + path fix). No changes to facts/sources/fetch/coverage.

Unit tests: **24** in `tests/test_robot_understanding_v1.py` (all green).

## Remaining failure mechanisms (general only)

1. **Critical recall 78%** — unchanged this pass (OTTO/Geek+/Sanctuary/ABB packs; JS-gated / thin seeds). Classify as **general** fact/source coverage — decide later; do not open Phase 4 on this alone.
2. **Tier ±1 85%** — one-robot slip vs prior 90%; not investigated (out of company-binding scope).
3. **Sparse / library shells** — ABB XML chrome, Geek+ empty facts, runtime gaps on cleaning/service — prior mechanisms; held.

## Discipline held

- Same Blind 20 cohort + ground truth (no GT edits)
- No OEM-specific branches
- No retune of source discovery, spec extraction, taxonomy, qualitative extractors, fetch, or numeric parsers
- No Phase 4 / jobs / QUALIFY
- Grounding 100%, unsupported 0%, sibling contamination 0, fact recall 62% held

## Explicit: Phase 4 not opened

Blind 20 **FAIL** (critical recall + tier). Company/product disentanglement **PASS**. Phase 1–3 gate **not** earned until critical recall ≥80% (and tier bar) without regressing identity.

---

## v1.0 freeze / product decision (2026-08-17)

**Understanding Phases 1–3 are frozen as v1.0 calibration.** Gate failed; leave it failed. Do **not** retune critical recall to hit 80%.

| Decision | Lock |
|----------|------|
| Phase 1–3 Blind 20 gate | **FAIL** left open (critical recall 78%; incomplete) |
| Phase 4 | **CLOSED** — not earned |
| Extractors / sources / resolve / Blind 20 bars | **Do not reopen or retune** |
| Trust posture | Strong identity, disentanglement, grounding, numeric scope — **credible but incomplete** |

### Why leave the gate failed

Remaining critical misses are **multi-mechanism**, not one bug: OTTO, Geek+, Sanctuary, ABB, and library/shell pages. Chasing ≥80% on this cohort would tune Blind 20 rather than improve general understanding.

### What this freeze means

- Freeze as **Understanding v1.0 calibration**: safe, grounded, not complete enough for Phase 4.
- Do **not** tune Blind 20 scoring bars or extractors mid-stream to clear the gate.
- Do **not** reopen Blind 20 or Understanding code for cohort-specific fixes.

### Next paths (ops, not retune)

| Path | Intent |
|------|--------|
| **(A) Production shadow mode** | Real OEM URLs → store profiles → measure human-visible missing criticals |
| **(B) Fresh Blind 20 later** | Only after general source-retrieval improvements driven by real shadow failures |

Rerun **this same** Blind 20 cohort only if a **broad** mechanism emerges (e.g. PDFs systematically missed). Otherwise prefer (A), then a new holdout.

See also: [`V1_0_FREEZE.md`](./V1_0_FREEZE.md).
