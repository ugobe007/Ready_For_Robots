# Taxonomy extraction policy

Rules the robot classifier (`app/services/robot_understanding_v1/taxonomy_extraction.py`) follows. Rules 1–2 were adopted 2026-10-14 at prompt `v3`; rules 3–5 at prompt `v4`. Prompt `v5` changed no rule: it carried taxonomy v1.2's new enum values (six industries, `surgical_assistance`). It never ran on a test set. Prompt `v6` adds rule 1a (industry descriptions in the prompt). Hold-out v2 measured `v4` on taxonomy v1.1; the first fresh set after it measures `v6` on v1.2. Each design change is measured on a hold-out set it was not designed against. Hold-out v1 informed the `v4` changes, so `v4` results on v1 are "seen data", reference only; the `v4` number comes from hold-out v2.

## 1. Industry means the buyer-operator's industry

An industry is the industry of the organization that **buys and operates** the robot. It is not the building type, the project type, or the industry of that organization's customers.

- A construction robot used on a hospital project is `construction`.
- A warehouse robot doing pharma logistics is `warehouse_distribution` or `3pl`.

Source of truth: `industries._definition` in `tests/fixtures/taxonomy.v1.json`. The extractor puts that text into the prompt verbatim. Keys starting with `_` are documentation and never become enum values.

### 1a. Industry descriptions in the prompt (prompt `v6`)

The prompt lists every industry as `- value: description`, with the description copied verbatim from the taxonomy, instead of the bare value names. Descriptions carry boundaries the names alone don't, e.g. `restaurant` includes the bars inside restaurants, while `bar_nightclub` is only for standalone bars, lounges and nightclubs (Bob, spec v1.6 §1). This is a rule change, so it is measured on the next fresh test set, not on hold-out v1 or v2.

## 2. Unsupported facts are excluded

A fact is supported only if its evidence passes the evidence check (rule 3). Any fact that fails:

- is removed from the product record, so scoring and matching cannot see it;
- is kept in the record's `unsupported_facts` list with its confidence capped, for logs and review;
- if it is a single-value field (`offering_type`, `form`, `primary_class`, `primary_function`), the field becomes `null` and scores as empty, i.e. wrong.

## 3. Evidence check v2 (prompt `v4`)

- Page text and evidence are both normalized: whitespace collapsed, curly and straight quotes unified, dash variants unified, lowercased.
- Evidence is split on `...` (or `…`). Every piece must appear on the page, in the same order.
- The prompt asks for one contiguous passage per fact, copied exactly: no joined passages, no `...`, no heading glued to body text, no rewording.

## 4. Page type first (prompt `v4`)

The model first classifies the page itself as one of `page_types` in the config. Only `record_page_types` (`manufacturer_product_page`) produce product records. Any other page produces a page record (`page_type`, evidence, `offering_type: non_robot`) and no product records, even if the model returned some; the dropped count is logged as `records_dropped_by_page_type`. The page-type evidence is checked and logged, but a failed check does not blank the page type.

## 5. Output and record limits (prompt `v4`)

- Output limit: `max_output_tokens` (8,192).
- At most `max_records_per_page` (5) records per page: the hinted target product plus at most 4 others, or the first 5 without a hint. The extra records are dropped and counted in `records_dropped_by_cap`.

## 6. Record selection

**Production** keeps every product record on a page (up to the rule 5 cap). No record is picked as "the" robot for the URL; each record is a separate robot and is matched to jobs separately.

**Benchmark scoring** (fixed before hold-out v2):

1. Extraction runs without the product hint. That is the headline. The run with the hint is reported second, as a reference.
2. The runner matches the answer key's `target_product` and `target_aliases` against the extracted product names. It never falls back to an unmatched record.
3. `target_aliases` are the model names for the target product line, taken only from that entry's snapshot `page.txt` (never from extractor output), and approved before the freeze. For a family target, every model in the family is an alias. The name rule is not loosened to make up for missing aliases: picking the record by a field that is also scored would inflate results.
4. Name match (`names_match` in `scripts/test_understanding_v2_benchmark.py`):
   - Both names are normalized: lowercase, `™ ® ©` removed, split into letter/digit tokens (punctuation and `+` are separators), and a trailing plural `s` removed from tokens longer than 3 letters.
   - It is a match if the token lists are equal, or if the shorter list appears as a contiguous run inside the longer one and is not made only of generic words (`a an the and of robot robotic robotics system series autonomous`).
5. The entry is scored with the frozen scorer on the first record, in extraction order, that matches `target_product` or any alias. Field accuracy is also reported across every matched record (`per_field_accuracy_all_matched_records`, pass/total per field).
6. If no record matches (including pages that produced no records), the entry fails as `target_not_extracted`. That is its own failure type, listed separately with the extracted names. Per-field accuracy is computed only over entries whose target record was found.
7. An entry with `unreadable_reason` in the key is reported as unreadable with that reason and is not extracted (e.g. the company was acquired and the URL now serves another company's site; no substitute company is used).
7a. An entry with `target_not_on_page` (the saved page loaded, but it does not describe the target robot) is reported as `target_not_on_page` and is not extracted. It is not an extraction failure and not `target_not_extracted`.
8. Extraction uses the snapshot's `final_url` (after redirects or a same-company `--url` retake), not the key's original URL.
9. Gap probes use the same selection. Negative controls have no target and must produce no records (Reporting).

## Settings

All in `app/services/robot_understanding_v1/extraction_config.json`:

| Key | Value | Meaning |
|-----|-------|---------|
| `evidence_check` | `normalized_pieces_in_order` | Rule 3 |
| `exclude_unsupported_facts` | `true` | Remove unsupported facts from the record (set `false` to keep them with capped confidence) |
| `unsupported_confidence_cap` | `0.3` | Confidence recorded for logged unsupported facts |
| `max_malformed_output_retries` | `1` | Extra calls allowed when the response has no tool call or its products cannot be parsed. Never retried on content. Tokens from every attempt are counted. |
| `max_output_tokens` | `8192` | Rule 5 |
| `max_records_per_page` | `5` | Rule 5 |
| `page_types` | 4 types with definitions | Rule 4; the definitions go into the prompt verbatim |
| `record_page_types` | `manufacturer_product_page` | Rule 4 |

The answer key and the field scorer (`scripts/benchmark_scoring_v2.py`) are unchanged by these rules.

## Industry parents (taxonomy v1.2)

`industry_parents` in the taxonomy says which newer industries also count as an older one: `bar_nightclub` → `restaurant`, `surgery_center` → `hospital`, `k12_school` → `college_university`. Answer keys written on v1.1 stay valid.

- **Scoring:** an extracted child counts as its parent for `industries_required`, `industries_any` and `industries_must_not` (so `bar_nightclub` is forbidden where `restaurant` is), and is not an unexpected extra when its parent is accepted. A parent never satisfies a child.
- **Pilot groups** (`PILOT_INDUSTRY_GROUPS` in `app/services/robot_understanding_v1/industries.py`, from `docs/buyer_opportunity_spec.md` §1): an industry is in a group if it or its parent is a member. `k12_school` stays hidden because `college_university` is in no group. `residential_consumer` is never a buyer.

Taxonomy v1.3 adds `facility_services` (contract cleaning, food service and facility management companies) to pilot group 8. It has no parent. Prompt stays `v6`: no rule changed, and the cache key already carries the taxonomy version.

## Reporting

The benchmark runner reports robots, taxonomy gap probes and negative controls as separate results, each with a count of fields blanked as unsupported, by field. Results without the product hint are the production number and come first. The runner also saves the page record and every extracted product name per page, and reports the page type assigned to every entry next to the expected page type (robots: `expected_page_type`; negative controls: `expected.page_type`).

How the runner applies the answer key (the scorer itself is unchanged):

- A negative control passes only if every field its key states matches. When the key states a `page_type`, the assigned page type must match and the page must produce zero robot records.
- A gap probe passes if `unclassified_notes` names the gap (terms per probe in `GAP_RULES`). For probes marked `forbid_must_not` (Nuro), it also fails if any `industries_must_not` value is tagged. Taxonomy fields are scored and reported beside the verdict only when the key states them (Ekso has no `form_ok`, so form is not scored).
