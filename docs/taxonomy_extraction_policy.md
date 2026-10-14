# Taxonomy extraction policy

Rules the robot classifier (`app/services/robot_understanding_v1/taxonomy_extraction.py`) follows. Rules 1–2 were adopted 2026-10-14 at prompt `v3`; rules 3–5 at prompt `v4`. Each design change is measured on a hold-out set it was not designed against. Hold-out v1 informed the `v4` changes, so `v4` results on v1 are "seen data", reference only; the `v4` number comes from hold-out v2.

## 1. Industry means the buyer-operator's industry

An industry is the industry of the organization that **buys and operates** the robot. It is not the building type, the project type, or the industry of that organization's customers.

- A construction robot used on a hospital project is `construction`.
- A warehouse robot doing pharma logistics is `warehouse_distribution` or `3pl`.

Source of truth: `industries._definition` in `tests/fixtures/taxonomy.v1.json`. The extractor puts that text into the prompt verbatim. Keys starting with `_` are documentation and never become enum values.

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

The answer key and scorer are unchanged by these rules.

## Reporting

The benchmark runner reports robots, taxonomy gap probes and negative controls as separate results, each with a count of fields blanked as unsupported, by field. Results without the product hint are the production number and come first. The runner also saves the page record and every extracted product name per page.
