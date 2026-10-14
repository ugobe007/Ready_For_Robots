# Hold-out v2 results (prompt v4, taxonomy v1.1)

Run 2026-10-14 per `rules_for_use` in `tests/fixtures/robot_holdout_set.v2.json`. This is the measurement of prompt `v4`. Nothing in the prompt, scorer, rules or answer key was changed based on these results. Taxonomy v1.2 and prompt `v5` came after this run. These results are **not** re-scored under v1.2; the next fresh set measures v1.2.

- **Frozen commit:** `18691ab22ce59467a363cb3f483c635f675bae5d` (code, scorer, runner, taxonomy v1.1 and snapshots), recorded before the run. The worktree was clean.
- **Snapshots:** `tests/fixtures/robot_pages_holdout_v2/` (rendered, committed in the freeze). No `--url` retakes were made.
- **Command:** `python3 scripts/test_understanding_v2_benchmark.py --benchmark tests/fixtures/robot_holdout_set.v2.json --fixtures tests/fixtures/robot_pages_holdout_v2 --hint off|on`. Each run was done once.

## Robots (19)

| | Hint off (headline) | Hint on (reference) |
|---|---|---|
| Not read: unreadable per key | 2 (v2-10 Asylon, v2-12 SafeAI) | 2 (same) |
| Not read: `target_not_on_page` | 2 (v2-07 SwarmFarm, v2-08 SoftBank) | 2 (same) |
| Readable | 15 | 15 |
| `target_not_extracted` | 1 (v2-16 Doosan) | 0 |
| Scored | 14 | 15 |
| **All five fields pass** | **10 of 14 scored (71%); 10 of 15 readable (67%)** | 10 of 15 (67%) |
| offering_type | 13/14 | 14/15 |
| form | 13/14 | 14/15 |
| primary_class | 13/14 | 15/15 |
| primary_function | 14/14 | 14/15 |
| industries | 11/14 | 13/15 |
| Fields blanked as unsupported | industries 1 (v2-14) | industries 5 (v2-01 ×4, v2-14) |
| Every matched record (pass/total) | offering 27/28, form 26/28, class 25/28, function 24/28, industries 23/28 | 20/21, 20/21, 21/21, 20/21, 17/21 |
| Tokens / time | 326,193 / 421 s | 324,335 / 412 s |

### Failures by ID, hint off

- **v2-02 Exotec:** industries. `hospital` is tagged (must_not) from the word "Healthcare" in an industries list.
- **v2-13 Kewazo LIFTBOT:** form `portable_stationary_unit`, expected `fixed_gantry_system`. The model noted that LIFTBOT "does not map cleanly to any taxonomy form value".
- **v2-14 UVD Robot:** primary_class `cleaning`, expected `healthcare`. Industries are missing `hospital`: the model tagged it, but the evidence check blanked it. The quote dropped one closing `"` before "- Erik Christenson…", so it did not match the page exactly.
- **v2-16 Doosan:** `target_not_extracted`. The records were `P-SERIES (Cobots)`, `PalletizHD+`, `AI Depalletizer`, `Scan & Go` and `Dr.Presso`. The aliases are model numbers (`P3020`, `H2515`, `M1013`, …), and none of the records uses one.
- **v2-18 Gather AI:** offering_type `robotics_as_a_service`, expected `robot_product` or `autonomy_software`. Industries tag `hospital` (must_not) from an "Industries … Healthcare …" list.

### Failures by ID, hint on

- v2-02, v2-13 and v2-14 fail as with the hint off. For v2-14, primary_class now passes, but `hospital` is blanked the same way.
- **v2-09 Robotise JEEVES:** primary_function `serving_hospitality`, expected `delivery_transport` (from "Reinvent minibar and room service with JEEVES"). JEEVES passes with the hint off.
- **v2-18 Gather AI:** offering_type `robotics_as_a_service` (industries pass this time).
- v2-16 Doosan passes only because the model named a record "Doosan cobots", copying the hint text. v2-01 Geek+ was named "Geek+ warehouse robots" the same way. That is one reason the hint-on number is reference only.

## Taxonomy gap probes (3)

| | Hint off | Hint on |
|---|---|---|
| gp2-01 Nuro | PASS (gap named: automakers); offering, form, industries pass | PASS |
| gp2-02 Ekso Bionics | PASS (gap named: exoskeleton); offering, class, industries pass | PASS |
| gp2-03 Unitree | **FAIL**: notes don't name research/education; industries have none of `research_lab`, `college_university` | PASS (gap named). offering_type blanked as unsupported; industries still fail |
| Blanked as unsupported | 0 | offering_type 1 (gp2-03) |

## Negative controls (2)

| | Hint off | Hint on |
|---|---|---|
| neg-v2-1 (directory) | PASS: `directory_or_multi_company`, 0 robot records | PASS |
| neg-v2-2 Indeed (drift guard) | **FETCH_FAILED**: HTTP 403. Not substituted, per the key | same |
| Blanked as unsupported | 0 | 0 |

## Page type for every entry

- Robots: all 15 readable robots are `manufacturer_product_page`, as expected. v2-07 and v2-08 were not extracted (`target_not_on_page`). v2-10 and v2-12 were not read.
- Gap probes: all 3 are `manufacturer_product_page` (no expected type in the key).
- Negative controls: neg-v2-1 is `directory_or_multi_company`, as expected. neg-v2-2 was not read (HTTP 403).

The page types are the same with the hint on.

## Dead or wrong URLs

- neg-v2-2 (Indeed) returns 403 to the snapshotter. The key says to report FETCH_FAILED and not substitute.
- Asylon (security block) and SafeAI (acquired, redirects to pronto.ai) are unreadable per the key.
- SwarmFarm and SoftBank pages don't name the target (`target_not_on_page`, per the freeze).
- No same-company `--url` retake was available or made.

## Observations (no change made; for the next design cycle)

- **Industries:** "Healthcare" in a maker's industries list becomes `hospital` (v2-02, v2-18) even when the robot is warehouse or inventory work. This is a buyer-operator rule miss.
- **Evidence check:** a single dropped quote character blanks a correct fact (v2-14). The check is exact by design.
- **Aliases:** model-number aliases don't match family-level record names (v2-16).
- **Hint:** with the hint on, the model copies the hint into the record name, so the name match is no longer independent.
