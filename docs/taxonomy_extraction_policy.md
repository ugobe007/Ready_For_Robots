# Taxonomy extraction policy

Rules the robot classifier (`app/services/robot_understanding_v1/taxonomy_extraction.py`) follows. Adopted 2026-10-14 at prompt `v3`. They were written before any measurement and are measured only on the hold-out set, not on the 23 calibration pages.

## 1. Industry means the buyer-operator's industry

An industry is the industry of the organization that **buys and operates** the robot. It is not the building type, the project type, or the industry of that organization's customers.

- A construction robot used on a hospital project is `construction`.
- A warehouse robot doing pharma logistics is `warehouse_distribution` or `3pl`.

Source of truth: `industries._definition` in `tests/fixtures/taxonomy.v1.json`. The extractor puts that text into the prompt verbatim. Keys starting with `_` are documentation and never become enum values.

## 2. Unsupported facts are excluded

A fact is supported only if its evidence quote is a whitespace- and case-normalized substring of the page text. Any fact that fails this check:

- is removed from the product record, so scoring and matching cannot see it;
- is kept in the record's `unsupported_facts` list with its confidence capped, for logs and review;
- if it is a single-value field (`offering_type`, `form`, `primary_class`, `primary_function`), the field becomes `null` and scores as empty.

Settings live in `app/services/robot_understanding_v1/extraction_config.json`:

| Key | Value | Meaning |
|-----|-------|---------|
| `evidence_check` | `normalized_substring` | How evidence is checked against page text |
| `exclude_unsupported_facts` | `true` | Remove unsupported facts from the record (set `false` to keep them with capped confidence) |
| `unsupported_confidence_cap` | `0.3` | Confidence recorded for logged unsupported facts |

The answer key and scorer are unchanged by either rule.
